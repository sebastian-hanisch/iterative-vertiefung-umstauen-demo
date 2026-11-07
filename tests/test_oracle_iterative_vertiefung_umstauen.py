"""Orakel-Test iterative-vertiefung-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Optimum, Zulässigkeit der Untergrenze und Knotenzahlen gegen ANDERE Rechenwege.

Orakel 1: Breitensuche über alle Buchtzustände (restricted) liefert das Optimum; jedes Verfahren in jeder Reihenfolge muss es treffen.
Orakel 2: Die Untergrenze (Zahl der Blocker) ist an JEDEM Knoten des Suchbaums höchstens so groß wie die wahre Restkosten (Breitensuche vom Knoten aus).
Orakel 3: Knoten von Branch and Bound mit Untergrenze und von IDA* mit einer zweiten, **iterativen** Fassung mit eigenem Stapel (Regeln aus der Beschreibung, nicht aus dem Kern).
Orakel 4: Knoten einer **gescheiterten** Budgetstufe per memoisierter Zählung über (Zustand, Hübe), unabhängig von der Tiefensuche und von der Reihenfolge der Kinder.
Vorher an den Handzahlen geprüft: Mini-Bucht 6 Knoten (3 + 3), Gegenbeispiel 15 (3 + 12)."""

from itertools import permutations

import ive_algorithm as A
from ive_scenario import canonical, make_bay, max_height

INF = 10 ** 9


def _pop(st):
    st = [list(s) for s in st]
    while True:
        items = [c for s in st for c in s]
        if not items:
            return tuple(tuple(s) for s in st)
        t = min(items)
        hit = [s for s in st if s and s[-1] == t]
        if not hit:
            return tuple(tuple(s) for s in st)
        hit[0].pop()


def own_blockers(state):
    """Untergrenze neu gezählt: Container, unter denen ein kleinerer im selben Stapel liegt (anderer Rechenweg als im Kern)."""
    return sum(1 for s in state for i, c in enumerate(s) if any(d < c for d in s[:i]))


def own_children(state, height):
    """Kinder eines Knotens (Bucht nach den Abrufen), alle Zielstapel in Stapelreihenfolge, als Buchten nach dem Hub (noch vor den Abrufen)."""
    items = [c for s in state for c in s]
    t = min(items)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    out = []
    for dst in range(len(state)):
        if dst == src or len(state[dst]) >= height:
            continue
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[dst].append(c)
        out.append(tuple(tuple(s) for s in nxt))
    return out


def bfs_optimum(bay, height):
    start = _pop(bay)
    if not any(start):
        return 0
    frontier, seen, depth = {start}, {start}, 0
    while frontier:
        depth += 1
        nxt = set()
        for state in frontier:
            for child in own_children(state, height):
                new = _pop(child)
                if not any(new):
                    return depth
                if new not in seen:
                    seen.add(new)
                    nxt.add(new)
        frontier = nxt
    raise AssertionError("keine Lösung")


def reachable_states(bay, height):
    """Alle Zustände (nach den Abrufen), die im Suchbaum der vollen Aufzählung vorkommen."""
    start = _pop(bay)
    seen, todo = {start}, [start]
    while todo:
        state = todo.pop()
        if not any(state):
            continue
        for child in own_children(state, height):
            new = _pop(child)
            if new not in seen:
                seen.add(new)
                todo.append(new)
    return seen


def ordered_children(state, height, order):
    t = min(c for s in state for c in s)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    base = [list(s) for s in state]
    base[src].pop()
    dests = [j for j in range(len(state)) if j != src and len(state[j]) < height]
    if order != "index":
        def key(j):
            m = min(base[j]) if base[j] else INF
            return (0, m) if m > c else (1, -m)
        dests.sort(key=lambda j: (key(j), j))
        if order == "anti":
            dests.reverse()
    return src, c, dests


def iterative_search(bay, height, order, prune, stop_at_leaf):
    """Tiefensuche mit eigenem Stapel statt Rekursion. prune(g, state, best) entscheidet über Abschneiden. Gibt (Knoten, bestes Blatt, gefunden) zurück."""
    best, nodes = INF, 0
    stack = [(_pop(bay), 0, None, None)]                               # (Knoten, Hübe, noch nicht abgearbeitete Kinder, Kontext)
    while stack:
        state, g, kids, ctx = stack.pop()
        if kids is None:                                                # Knoten wird zum ersten Mal besucht
            nodes += 1
            if not any(state):
                best = min(best, g)
                if stop_at_leaf:
                    return nodes, best, True
                continue
            if prune(g, state, best):
                continue
            src, c, dests = ordered_children(state, height, order)
            kids, ctx = list(dests), (src, c)
        if not kids:
            continue
        j = kids.pop(0)
        stack.append((state, g, kids, ctx))
        src, c = ctx
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[j].append(c)
        stack.append((_pop(tuple(tuple(s) for s in nxt)), g + 1, None, None))
    return nodes, best, False


def iterative_bblb(bay, height, order):
    nodes, best, _ = iterative_search(bay, height, order, lambda g, st, b: g + own_blockers(st) >= b, False)
    return best, nodes


def iterative_ida(bay, height, order):
    """(Optimum, Knoten je Stufe [(Budget, Knoten, gefunden)])."""
    budget = own_blockers(_pop(bay))
    stages = []
    while True:
        nodes, best, found = iterative_search(bay, height, order, lambda g, st, b, budget=budget: g + own_blockers(st) > budget, True)
        stages.append((budget, nodes, found))
        if found:
            return best, stages
        budget += 1


def failed_stage_nodes(bay, height, budget):
    """Knoten einer gescheiterten Stufe per memoisierter Zählung über (Zustand, Hübe): unabhängig von Reihenfolge und Tiefensuche."""
    memo = {}

    def rec(state, g):
        assert any(state), "die Stufe ist nicht gescheitert (ein Blatt wurde erreicht)"
        if (state, g) not in memo:
            n = 1
            if g + own_blockers(state) <= budget:
                n += sum(rec(_pop(child), g + 1) for child in own_children(state, height))
            memo[(state, g)] = n
        return memo[(state, g)]

    return rec(_pop(bay), 0)


def all_bays_3x2():
    seen = {}
    for perm in permutations(range(1, 7)):
        bay = tuple(tuple(perm[i * 2:(i + 1) * 2]) for i in range(3))
        seen.setdefault(canonical(bay), bay)
    return list(seen.values())


def test_oracle_on_the_hand_numbers(mini, counter):
    assert bfs_optimum(*mini) == 2 and bfs_optimum(*counter) == 4
    assert iterative_ida(*mini, "index") == (2, [(1, 3, False), (2, 3, True)])
    assert iterative_ida(*counter, "tight") == (4, [(3, 3, False), (4, 12, True)])
    assert own_blockers(((1, 4), (5, 2), (6, 3))) == 1 and own_blockers(((3, 6), (2, 4), (1, 5))) == 3


def test_every_mode_and_order_finds_the_optimum_of_the_breadth_first_search():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            opt = bfs_optimum(bay, h)
            for mode in A.MODES:
                for order in A.ORDERS:
                    r = A.search(bay, h, mode, order)
                    assert (r.optimum, r.capped) == (opt, False), (stacks, layers, sd, mode, order)


def test_the_lower_bound_never_exceeds_the_true_remaining_cost_at_any_node():
    h = max_height(2, 2)
    total = 0
    for bay in all_bays_3x2():
        for state in reachable_states(bay, h):
            if any(state):
                assert A.blocker_count(state) == own_blockers(state) <= bfs_optimum(state, h), state
                total += 1
    assert total > 500                                                 # wirklich viele Knoten geprüft, nicht nur die Wurzeln
    for sd in range(8):
        bay = make_bay(4, 2, sd)
        for state in list(reachable_states(bay, h))[:400]:
            if any(state):
                assert A.blocker_count(state) <= bfs_optimum(state, h), (sd, state)


def test_branch_and_bound_with_the_lower_bound_matches_an_iterative_second_implementation():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            for order in A.ORDERS:
                r = A.search(bay, h, "bblb", order)
                assert (r.optimum, r.nodes) == iterative_bblb(bay, h, order), (stacks, layers, bay, order)


def test_ida_matches_an_iterative_second_implementation_stage_by_stage():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            for order in A.ORDERS:
                r = A.search(bay, h, "ida", order)
                opt, stages = iterative_ida(bay, h, order)
                assert (r.optimum, list(r.stages)) == (opt, stages), (stacks, layers, bay, order)
                assert r.nodes == sum(s[1] for s in stages)


def test_failed_stages_equal_a_memoised_count_and_do_not_depend_on_the_order():
    for stacks, layers, seeds in ((3, 2, 60), (4, 2, 30), (3, 3, 30)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            per_order = {o: A.search(bay, h, "ida", o).stages for o in A.ORDERS}
            for o, stages in per_order.items():
                for budget, nodes, found in stages[:-1]:
                    assert nodes == failed_stage_nodes(bay, h, budget), (stacks, layers, sd, o, budget)
            first = [[s[:2] for s in st[:-1]] for st in per_order.values()]
            assert first[0] == first[1] == first[2], (stacks, layers, sd)


def test_the_number_of_stages_is_the_gap_plus_one():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 60), (3, 3, 60), (3, 4, 6)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            opt = bfs_optimum(bay, h) if layers < 4 else A.search(bay, h, "bblb", "tight").optimum
            for order in A.ORDERS:
                assert len(A.search(bay, h, "ida", order).stages) == opt - own_blockers(bay) + 1, (stacks, layers, sd, order)


def test_branch_and_bound_with_the_lower_bound_never_visits_more_nodes_than_without():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 60), (3, 3, 60)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            for order in A.ORDERS:
                with_lb, without = A.search(bay, h, "bblb", order), A.search(bay, h, "bb", order)
                assert with_lb.nodes <= without.nodes and with_lb.optimum == without.optimum, (stacks, layers, sd, order)
