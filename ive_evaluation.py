"""Kennzahlen, Verdikt-Logik, vorberechnete Tabellen. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import ive_algorithm as A
import ive_constants as C
from ive_scenario import make_bay, max_height

BANDS_FILE = Path(__file__).resolve().parent / "ive_bands.json"

ENUM, BB, BBLB = ("enum", "index"), ("bb", "tight"), ("bblb", "tight")
IDA_I, IDA_T, IDA_A = ("ida", "index"), ("ida", "tight"), ("ida", "anti")


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    layers: int = C.DEFAULT_LAYERS
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.EVERYDAY_SEED


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    lower: int          # Untergrenze: blockierende Container (Stück 2)
    results: dict       # (Verfahren, Reihenfolge) -> SearchResult

    def res(self, variant) -> A.SearchResult:
        return self.results[variant]

    @property
    def optimum(self):
        """Das Optimum, sobald ein Verfahren es bewiesen hat (alle, die fertig werden, liefern dasselbe); sonst None."""
        found = {r.optimum for r in self.results.values() if not r.capped}
        assert len(found) <= 1, found
        return found.pop() if found else None

    @property
    def gap(self):
        """Lücke Optimum - Untergrenze (Stück 2), None, wenn das Optimum nicht bewiesen ist."""
        return None if self.optimum is None else self.optimum - self.lower


def analyse(settings: Settings, cap: int = C.LIVE_CAP) -> Analysis:
    bay = make_bay(settings.stacks, settings.layers, settings.seed)
    height = max_height(settings.layers, settings.extra)
    return Analysis(bay, height, A.blocker_count(bay), {v: A.search(bay, height, v[0], v[1], cap) for v in C.VARIANTS})


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def num_f(x: float) -> str:
    """Zahl mit Leerzeichen als Tausendertrenner; hat sie einen Nachkommaanteil (Median einer geraden Zahl von Läufen), mit einer Nachkommastelle und Komma."""
    if float(x).is_integer():
        return num(int(x))
    whole, frac = f"{x:.1f}".split(".")
    return f"{num(int(whole))},{frac}"


def nodes_text(r: A.SearchResult) -> str:
    return f"mehr als {num(r.nodes)}" if r.capped else num(r.nodes)


def factor_text(x: float) -> str:
    """Verhältnis mit einer Nachkommastelle unter 10, sonst ganzzahlig gerundet."""
    return f"{x:.1f}".replace(".", ",") if x < 10 else f"{x:.0f}"


def ratio_text(x: float) -> str:
    """Verhältnis mit zwei Nachkommastellen (Tabellen)."""
    return f"{x:.2f}".replace(".", ",")


# ---------------------------------------------------------------- Verdikt einer Bucht

def verdict_bay(a: Analysis, cap: int = C.LIVE_CAP) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viel spart die Untergrenze gegenüber dem Branch and Bound aus Stück 4 (ohne Untergrenze)?"""
    bb, ida, bblb = a.res(BB), a.res(IDA_T), a.res(BBLB)
    opt = a.optimum
    if opt is None:
        return "warning", f"Alle Verfahren geben bei {num(cap)} Knoten auf: In dieser Bucht ist das Optimum so nicht zu beweisen (Untergrenze {a.lower})."
    if ida.capped:
        n = min(r.nodes for r in a.results.values() if not r.capped)
        return "warning", (f"IDA* mit engster Passung gibt bei {num(cap)} Knoten auf; ein anderes Verfahren beweist das Optimum {opt} mit {num(n)} Knoten "
                           f"(Untergrenze {a.lower}).")
    stages = len(ida.stages)
    tail = f" Branch and Bound mit Untergrenze braucht {num(bblb.nodes)}." if not bblb.capped else " Branch and Bound mit Untergrenze gibt auf."
    if bb.capped:
        return "warning", (f"Branch and Bound ohne Untergrenze (Stück 4) gibt bei {num(cap)} Knoten auf; IDA* mit engster Passung beweist das Optimum {opt} mit "
                           f"{num(ida.nodes)} Knoten in {stages} Budgetstufen (Untergrenze {a.lower})." + tail)
    factor = bb.nodes / ida.nodes
    if factor >= C.LB_STRONG:
        return "success", (f"Branch and Bound ohne Untergrenze braucht {num(bb.nodes)} Knoten, IDA* mit engster Passung {num(ida.nodes)}: das {factor_text(factor)}-Fache weniger "
                           f"(Optimum {opt}, Untergrenze {a.lower}, {stages} Budgetstufen)." + tail)
    if factor >= C.LB_WEAK:
        return "info", (f"Branch and Bound ohne Untergrenze braucht {num(bb.nodes)} Knoten, IDA* mit engster Passung {num(ida.nodes)}: das {factor_text(factor)}-Fache weniger "
                        f"(Optimum {opt}, Untergrenze {a.lower}, {stages} Budgetstufen)." + tail)
    return "info", (f"Die Bucht ist so klein, dass die Untergrenze nichts spart: {num(bb.nodes)} Knoten ohne Untergrenze, {num(ida.nodes)} mit IDA* "
                    f"(Optimum {opt}, Untergrenze {a.lower}, {stages} Budgetstufen)." + tail)


def result_rows(a: Analysis) -> list[dict]:
    """Eine Zeile je Verfahren: Name, Knoten (Text), Blätter, Optimum (oder „nicht bewiesen“), Zahl der Budgetstufen (nur IDA*)."""
    rows = []
    for v in C.VARIANTS:
        r = a.res(v)
        rows.append({"variant": v, "name": C.VARIANT_NAMES[v], "nodes": r.nodes, "capped": r.capped, "nodes_text": nodes_text(r),
                     "leaves": r.leaves, "optimum": "nicht bewiesen" if r.capped else str(r.optimum), "stages": len(r.stages) if v[0] == "ida" else None})
    return rows


def stage_rows(a: Analysis, variant=IDA_T) -> list[dict]:
    """Eine Zeile je Budgetstufe von IDA*: Budget, Knoten, Ergebnis (Text). Die letzte Stufe einer abgebrochenen Suche heißt „Limit erreicht“."""
    r = a.res(variant)
    rows = []
    for i, (b, n, found) in enumerate(r.stages):
        last = i == len(r.stages) - 1
        result = "Blatt gefunden: Optimum" if found else "Limit erreicht" if (last and r.capped) else "kein Blatt"
        rows.append({"budget": b, "nodes": n, "found": found, "result": result})
    return rows


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def cell_rows(stacks: int, layers: int, extra: int, seeds, full: bool = True, cap: int = C.BAND_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze, Optimum, Zahl der Budgetstufen von IDA*, Knoten der letzten Stufe und Knoten je Verfahren (None = über Limit).
    `full=False` rechnet nur die Verfahren mit Untergrenze (Zelle 5 x 4). Langsam bei großen Zellen, nur offline und in Tests."""
    height = max_height(layers, extra)
    variants = C.VARIANTS if full else C.LB_VARIANTS
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        row = {"seed": sd, "lb": A.blocker_count(bay), "opt": None, "stages": None, "last": None}
        for v in variants:
            r = A.search(bay, height, v[0], v[1], cap)
            row[C.VARIANT_KEYS[v]] = None if r.capped else r.nodes
            if v == IDA_T and not r.capped:
                row["opt"], row["stages"], row["last"] = r.optimum, len(r.stages), r.stages[-1][1]
        rows.append(row)
    return rows


def _stat(xs):
    ok = [x for x in xs if x is not None]
    if not ok:
        return {"ok": 0, "over": len(xs), "median": None, "mean": None, "max": None}
    return {"ok": len(ok), "over": len(xs) - len(ok), "median": median(ok), "mean": mean(ok), "max": max(ok)}


def _ratios(rows, top, bottom):
    return [r[top] / r[bottom] for r in rows if r.get(top) is not None and r.get(bottom) is not None]


def _ratio_stat(xs):
    return {"n": len(xs), "median": median(xs) if xs else None, "max": max(xs) if xs else None}


def cell_stats(rows: list[dict], full: bool = True) -> dict:
    """Kennzahlen einer Stichprobe: Knoten je Verfahren (Median, Mittel, Maximum der fertigen Läufe, Zahl der Läufe über Limit), die Verhältnisse über die Buchten,
    in denen beide Läufe fertig wurden (Median, Maximum): `gain` = Branch and Bound ohne Untergrenze / IDA* (engste Passung), `deep` = Branch and Bound mit Untergrenze /
    IDA*, `order_index` = IDA* Stapelnummern / engste Passung, `order_anti` = IDA* schlechteste / engste Passung; dazu die Budgetstufen von IDA* (Mittel, Maximum,
    Zahl der Buchten mit Stufen = Lücke + 1) und der Anteil der letzten Stufe an den Knoten (Median)."""
    k = C.VARIANT_KEYS
    variants = C.VARIANTS if full else C.LB_VARIANTS
    out = {"n": len(rows), "full": full, "variants": {k[v]: _stat([r[k[v]] for r in rows]) for v in variants}}
    out["gain"] = _ratio_stat(_ratios(rows, k[BB], k[IDA_T]))
    out["deep"] = _ratio_stat(_ratios(rows, k[BBLB], k[IDA_T]))
    out["order_index"] = _ratio_stat(_ratios(rows, k[IDA_I], k[IDA_T]))
    out["order_anti"] = _ratio_stat(_ratios(rows, k[IDA_A], k[IDA_T]))
    done = [r for r in rows if r["stages"] is not None]
    out["stages"] = {"n": len(done), "mean": mean(r["stages"] for r in done) if done else None, "max": max((r["stages"] for r in done), default=None),
                     "equal_gap_plus_1": sum(r["stages"] == r["opt"] - r["lb"] + 1 for r in done)}
    shares = [r["last"] / r[k[IDA_T]] for r in done]
    out["last_share"] = median(shares) if shares else None
    return out


def gap_table(rows: list[dict]) -> dict:
    """Knoten je Lücke (Optimum - Untergrenze): {Lücke: {n, ida: Kennzahlen, bblb: Kennzahlen, last_share: Median des Anteils der letzten Stufe}}."""
    k = C.VARIANT_KEYS
    table = {}
    done = [r for r in rows if r["stages"] is not None]
    for gap in sorted({r["opt"] - r["lb"] for r in done}):
        sub = [r for r in done if r["opt"] - r["lb"] == gap]
        table[str(gap)] = {"n": len(sub), "ida": _stat([r[k[IDA_T]] for r in sub]), "bblb": _stat([r[k[BBLB]] for r in sub]),
                           "last_share": median(r["last"] / r[k[IDA_T]] for r in sub)}
    return table


def growth_factors(table: dict, key: str) -> list[float]:
    """Verhältnisse aufeinanderfolgender Mediane (Lücke um 1 größer); nur dort, wo beide Mediane vorliegen und die Lücken aufeinanderfolgen."""
    out = []
    keys = sorted(int(x) for x in table)
    for a, b in zip(keys, keys[1:]):
        sa, sb = table[str(a)][key], table[str(b)][key]
        if b == a + 1 and sa["median"] is not None and sb["median"] is not None and sa["median"] > 0:
            out.append(sb["median"] / sa["median"])
    return out


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"tabelle": {"s,l": Stichprobe}, "luecke": {"s,l": Tabelle}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


def cell_key(stacks: int, layers: int) -> str:
    return f"{stacks},{layers}"


def verdict_gain(stats: dict) -> tuple[str, str]:
    """Verdikt „was bringt die Untergrenze?“ in drei Zuständen nach dem Median des Verhältnisses Branch and Bound ohne Untergrenze (Stück 4) / IDA*."""
    g = stats["gain"]
    if g["median"] is None:
        return "warning", "In dieser Zelle wurde kein Branch and Bound ohne Untergrenze fertig oder gerechnet: Der Vergleich mit Stück 4 ist so nicht möglich."
    text = (f"Die Untergrenze spart im Median das {factor_text(g['median'])}-Fache der Knoten (Branch and Bound ohne Untergrenze aus Stück 4 gegen IDA*, "
            f"{g['n']} Buchten, Maximum {factor_text(g['max'])}).")
    if g["median"] >= C.LB_STRONG:
        return "success", text + " Die Untergrenze wirkt hier stark."
    if g["median"] >= C.LB_WEAK:
        return "info", text + " Die Untergrenze wirkt hier mäßig."
    return "warning", text + " Die Untergrenze wirkt hier kaum: Die Bucht ist zu klein."


def verdict_deepening(stats: dict) -> tuple[str, str]:
    """Verdikt „ist die iterative Vertiefung der Gewinn?“: Median des Verhältnisses Branch and Bound mit Untergrenze / IDA* in drei Zuständen."""
    d = stats["deep"]
    if d["median"] is None:
        return "warning", "In dieser Zelle liegen für den Vergleich von Branch and Bound mit Untergrenze und IDA* keine fertigen Läufe vor."
    text = (f"Branch and Bound mit Untergrenze braucht im Median das {ratio_text(d['median'])}-Fache der Knoten von IDA* ({d['n']} Buchten, Maximum {factor_text(d['max'])}).")
    if d["median"] >= C.DEEPENING_BIG:
        return "info", text + " IDA* ist hier im Median merklich sparsamer."
    if d["median"] <= 1 / C.DEEPENING_BIG:
        return "info", text + " Branch and Bound mit Untergrenze ist hier im Median merklich sparsamer."
    return "info", text + " Die beiden Verfahren liegen im Median nah beieinander: Der Gewinn kommt von der Untergrenze, nicht von der Vertiefung."


def verdict_stages(stats: dict) -> tuple[str, str]:
    """Verdikt „Budgetstufen = Lücke + 1“: in wie vielen der Buchten stimmt es?"""
    s = stats["stages"]
    if s["n"] == 0:
        return "warning", "In dieser Zelle wurde kein IDA*-Lauf fertig."
    text = (f"Von {s['n']} Buchten hat IDA* in {s['equal_gap_plus_1']} genau Lücke + 1 Budgetstufen gebraucht (im Mittel {ratio_text(s['mean'])}, höchstens {s['max']}).")
    return ("success" if s["equal_gap_plus_1"] == s["n"] else "warning"), text


def verdict_gap(table: dict, name: str) -> tuple[str, str]:
    """Verdikt „Knoten je Lücke“: Verhältnisse aufeinanderfolgender Mediane von IDA* und Branch and Bound mit Untergrenze."""
    gi, gb = growth_factors(table, "ida"), growth_factors(table, "bblb")
    if not gi:
        return "info", f"{name}: zu wenige aufeinanderfolgende Lücken für ein Wachstumsverhältnis."
    last = [table[g]["last_share"] for g in sorted(table, key=int)]
    text = (f"{name}: Mit jeder Einheit Lücke wächst der Median von IDA* um das " + ", ".join(factor_text(x) for x in gi)
            + "-Fache (aufeinanderfolgende Lücken)" + (f", der von Branch and Bound mit Untergrenze um das " + ", ".join(factor_text(x) for x in gb) + "-Fache" if gb else "")
            + f". Der Anteil der letzten Stufe an den Knoten fällt im Median von {last[0] * 100:.0f} % (Lücke {min(table, key=int)}) auf {last[-1] * 100:.0f} % (Lücke {max(table, key=int)}).")
    return "info", text


def verdict_over_limit(stats: dict) -> tuple[str, str]:
    """Verdikt „wer gibt auf?“: Zahl der Läufe über dem Limit je Verfahren in der Zelle (nur gerechnete Verfahren)."""
    n = stats["n"]
    parts = []
    over = {}
    for v in C.VARIANTS:
        s = stats["variants"].get(C.VARIANT_KEYS[v])
        if s is not None:
            over[v] = s["over"]
    names = {ENUM: "die volle Aufzählung", BB: "Branch and Bound ohne Untergrenze", BBLB: "Branch and Bound mit Untergrenze", IDA_T: "IDA* (engste Passung)"}
    for v, name in names.items():
        if v in over:
            parts.append(f"{name} in {over[v]}")
    text = f"Von {n} Buchten gibt bei {num(C.BAND_CAP)} Knoten auf: " + ", ".join(parts) + "."
    return ("warning" if any(over.get(v, 0) for v in (ENUM, BB, BBLB, IDA_T)) else "info"), text


def verdict_tail(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „Wo wird es trotzdem knapp?“: Median, Mittel, Maximum von IDA* in einer Zelle und Zahl der Läufe über Limit."""
    v = stats["variants"]["ida/tight"]
    if v["median"] is None:
        return "warning", f"{name}: IDA* wurde in keiner Bucht fertig (alle {v['over']} über Limit)."
    over = f" {v['over']} Läufe lagen über dem Limit." if v["over"] else ""
    text = (f"{name}: IDA* mit engster Passung braucht im Median {num_f(v['median'])} Knoten, im Mittel {num(round(v['mean']))}, im Maximum {num(v['max'])} "
            f"(Mittel {factor_text(v['mean'] / v['median'])}-mal der Median)." + over)
    return ("warning" if v["over"] else "info"), text
