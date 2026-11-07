"""Kern: Tiefensuche mit Untergrenze beim Umstauen (restricted), mit Knotenzählung. Aufbauend auf Stück 2 (Untergrenze) und Stück 4 (Suchbaum).

Eine Bucht besteht aus Stapeln (Tupel von unten nach oben). Die Abrufnummer 1 kommt zuerst dran; nur der oberste Container eines Stapels ist erreichbar.
Liegt die nächste Nummer nicht oben, wird der oberste Container ihres Stapels (ein Blocker) auf einen anderen Stapel mit Platz gesetzt, jeder Hub kostet 1;
die nächste Nummer wird kostenlos entnommen, sobald sie oben liegt (restricted: nur Container über dem gesuchten werden bewegt).

Suchbaum wie in Stück 4: Ein **Knoten** ist ein Aufruf der Suche mit einer Bucht (und den bisherigen Hüben g), seine **Kinder** entstehen, indem der Blocker auf jeden
anderen Stapel mit Platz gesetzt wird; ein **Blatt** ist eine leere Bucht. Kein Zustandsmerken, kein Symmetriebruch: gleiche Zustände zählen mehrfach.

**Untergrenze eines Knotens:** die Zahl der gerade blockierenden Container im Zustand (Stück 2). Jeder von ihnen muss noch mindestens einmal bewegt werden, also sind bei g
bisherigen Hüben mindestens g + Untergrenze Hübe nötig.

  search   vier Verfahren (`mode`):
             "enum"  volle Aufzählung (keine Schranke)
             "bb"    Branch and Bound wie Stück 4: Abbruch, wenn g + 1 nicht mehr unter der besten bisher gefundenen Lösung liegt
             "bblb"  Branch and Bound mit Untergrenze: Abbruch, wenn g + Untergrenze nicht mehr unter der besten Lösung liegt
             "ida"   iterative Vertiefung (IDA*): Budget b = Untergrenze der Wurzel, dann b + 1, ...; je Budget eine Tiefensuche, die abbricht, sobald
                     g + Untergrenze > b; das erste Blatt ist das Optimum. Die Knoten sind die Summe über alle Budgetstufen.
           Reihenfolge der Kinder (`order`): "index" (Stapelnummern), "tight" (engste Passung zuerst), "anti" (schlechteste zuerst).
           Knotenlimit: Überschreitung gibt capped=True und kein Optimum.
  ida_tree_lines   der ausgeschriebene Suchbaum von IDA* je Budgetstufe für kleine Buchten
  autopop, blocker_count, target_stack, child_targets   Abruf, Untergrenze und Kinder (aus Stück 2 und 4)
"""

from dataclasses import dataclass

INF = 10 ** 9
MODES = ("enum", "bb", "bblb", "ida")
ORDERS = ("index", "tight", "anti")


def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def stack_blockers(stack):
    """Container in einem Stapel (unten nach oben), die über einem früher abzurufenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def blocker_count(stacks):
    """Zahl der blockierenden Container (Untergrenze der Hubzahl, Stück 2)."""
    return sum(stack_blockers(s) for s in stacks)


def target_stack(stacks):
    """(nächste Abrufnummer, Index ihres Stapels). Die Bucht darf nicht leer sein."""
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


def _fit_key(stacks, j, c):
    """Sortierschlüssel der engsten Passung für den Zielstapel j: Stapel, auf denen c nichts blockiert, zuerst (kleinster frühester Abruf zuerst, leerer Stapel zuletzt
    unter ihnen), danach die übrigen nach größtem frühesten Abruf."""
    m = min(stacks[j]) if stacks[j] else INF
    return (0, m) if m > c else (1, -m)


def child_targets(stacks, src, height, c, order):
    """Zielstapel für den Blocker c (Stapel `src`, Bucht ohne c) in der Reihenfolge `order`; nur Stapel mit Platz, gleiche Stapel werden NICHT zusammengefasst."""
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    dests = [j for j in range(len(stacks)) if j != src and len(stacks[j]) < height]
    if order == "index":
        return dests
    dests.sort(key=lambda j: (_fit_key(stacks, j, c), j))
    return dests[::-1] if order == "anti" else dests


@dataclass(frozen=True)
class SearchResult:
    optimum: int | None     # None, wenn das Knotenlimit erreicht wurde
    nodes: int              # Zahl der besuchten Knoten (bei capped: das Limit), bei IDA* die Summe über alle Budgetstufen
    leaves: int             # Zahl der besuchten Blätter
    capped: bool
    first_leaf: int | None  # Hubzahl des ersten besuchten Blatts (der erste Tauchgang)
    stages: tuple = ()      # nur IDA*: (Budget, Knoten, gefunden) je Stufe; bei capped endet die Liste mit der abgebrochenen Stufe


class _CapReached(Exception):
    pass


class _Found(Exception):
    pass


def _dfs(start, height, order, prune, cap, stop_at_leaf):
    """Eine Tiefensuche. `prune(g, state)` -> True schneidet den Teilbaum eines Nicht-Blatts ab; `stop_at_leaf` beendet die Suche am ersten Blatt.
    Gibt (Knoten, Blätter, Hubzahl des ersten Blatts, beste Hubzahl, gefunden) zurück; wirft _CapReached, wenn mehr als `cap` Knoten gebraucht werden
    (der Zähler steht dann in der Ausnahme)."""
    nodes = [0]
    leaves = [0]
    first = [None]
    best = [INF]

    def rec(state, g):
        nodes[0] += 1
        if nodes[0] > cap:
            raise _CapReached(nodes[0] - 1, leaves[0])
        st, _ = autopop(state)
        if not any(st):
            leaves[0] += 1
            if first[0] is None:
                first[0] = g
            if g < best[0]:
                best[0] = g
            if stop_at_leaf:
                raise _Found
            return
        if prune(g, st, best[0]):
            return
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        for j in child_targets(base, i, height, c, order):
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            rec(tuple(tuple(s) for s in nxt), g + 1)

    found = False
    try:
        rec(start, 0)
    except _Found:
        found = True
    return nodes[0], leaves[0], first[0], best[0], found


def search(stacks, height, mode="ida", order="tight", cap=1_000_000) -> SearchResult:
    """Tiefensuche über die Hubfolgen mit Knotenzählung (siehe Moduldoc)."""
    if mode not in MODES:
        raise ValueError(f"unbekanntes Verfahren {mode!r}")
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    start = tuple(tuple(s) for s in stacks)
    if mode != "ida":
        if mode == "enum":
            prune = lambda g, st, best: False                                   # noqa: E731
        elif mode == "bb":
            prune = lambda g, st, best: g + 1 >= best                           # noqa: E731  jeder weitere Hub kostet mindestens 1
        else:
            prune = lambda g, st, best: g + blocker_count(st) >= best           # noqa: E731
        try:
            nodes, leaves, first, best, _ = _dfs(start, height, order, prune, cap, False)
        except _CapReached as e:
            return SearchResult(None, cap, e.args[1], True, None)
        return SearchResult(best, nodes, leaves, False, first)
    budget = blocker_count(start)
    total, leaves_total, stages = 0, 0, []
    while True:
        b = budget
        try:
            nodes, leaves, first, best, found = _dfs(start, height, order, lambda g, st, _best, b=b: g + blocker_count(st) > b, cap - total, True)
        except _CapReached as e:
            stages.append((b, e.args[0], False))
            return SearchResult(None, cap, leaves_total + e.args[1], True, None, tuple(stages))
        total += nodes
        leaves_total += leaves
        stages.append((b, nodes, found))
        if found:
            return SearchResult(first, total, leaves_total, False, first, tuple(stages))
        budget += 1


def ida_tree_lines(stacks, height, order="index", max_nodes=300):
    """Der Suchbaum von IDA* als Textzeilen, je Budgetstufe ein Abschnitt (Einrückung = Tiefe, Kinder in der Reihenfolge `order`). Je Knoten: Bucht nach den Abrufen,
    bisherige Hübe g, Untergrenze und die Entscheidung. Wirft ValueError, wenn insgesamt mehr als `max_nodes` Zeilen für Knoten nötig wären (nur für kleine Buchten)."""
    lines = []
    total = [0]
    start = tuple(tuple(s) for s in stacks)
    b = blocker_count(start)
    while True:
        lines.append(f"Budget {b}:")
        count = [0]
        found = []

        def rec(state, g, depth, b=b):
            count[0] += 1
            total[0] += 1
            if total[0] > max_nodes:
                raise ValueError("Baum zu groß zum Ausschreiben")
            st, popped = autopop(state)
            pad = "    " * (depth + 1)
            pop_txt = f", abgerufen {', '.join(str(p) for p in popped)}" if popped else ""
            head = f"{pad}Knoten {count[0]}: {_fmt(st)} nach {g} {'Hub' if g == 1 else 'Hüben'}{pop_txt}"
            if not any(st):
                lines.append(head + f" – Blatt (leer): gefunden, Optimum {g}")
                found.append(g)
                raise _Found
            lb = blocker_count(st)
            if g + lb > b:
                lines.append(head + f"; Untergrenze {lb}: {g} + {lb} = {g + lb} > {b}, abgeschnitten")
                return
            lines.append(head + f"; Untergrenze {lb}: {g} + {lb} = {g + lb} ≤ {b}, weiter")
            _, i = target_stack(st)
            lst = [list(s) for s in st]
            c = lst[i].pop()
            base = tuple(tuple(s) for s in lst)
            for j in child_targets(base, i, height, c, order):
                lines.append(f"{pad}→ Container {c} von Stapel {i + 1} auf Stapel {j + 1}")
                nxt = [list(s) for s in lst]
                nxt[j].append(c)
                rec(tuple(tuple(s) for s in nxt), g + 1, depth + 1)

        try:
            rec(start, 0, 0)
        except _Found:
            pass
        if found:
            return lines
        lines.append(f"    kein Blatt mit höchstens {b} {'Hub' if b == 1 else 'Hüben'}: Budget auf {b + 1}")
        b += 1


def _fmt(stacks):
    return " | ".join("(" + ", ".join(str(c) for c in s) + ")" if s else "()" for s in stacks)
