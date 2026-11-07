"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 3          # Zahl der Stapel
LAYERS_MIN, LAYERS_MAX, DEFAULT_LAYERS = 2, 4, 3          # Anfangsfüllung je Stapel (Lagen)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 1, 4, 2             # Platz: Höchsthöhe = Lagen + Zuschlag (Standard 2 wie in Stück 1 bis 4)
SEED_MAX = 999999

LIVE_CAP = 500_000                                        # Knotenlimit der Live-Läufe (rund zwei bis drei Sekunden je Lauf); darüber: „gibt auf“
BAND_CAP = 1_000_000                                      # Knotenlimit der vorberechneten Tabellen
SAMPLE_SEEDS = tuple(range(100))                          # feste Buchten: nie eine einzelne Bucht als Befund

# Zellen der vorberechneten Tabelle: (Stapel, Lagen, Zahl der festen Buchten, alle sechs Verfahren?). Die sieben ersten Zellen sind die aus Stück 4 (gleiche Buchten);
# 4 x 4 (30 Buchten) ist dort die Zelle, an der die volle Aufzählung aufgibt; 5 x 4 (20 Buchten) wird nur mit den Verfahren mit Untergrenze gerechnet.
TABLE_CELLS = ((3, 2, 100, True), (4, 2, 100, True), (3, 3, 100, True), (5, 2, 60, True), (4, 3, 40, True), (3, 4, 40, True), (5, 3, 20, True),
               (4, 4, 30, True), (5, 4, 20, False))
GAP_CELLS = ((3, 3), (3, 4))                              # Zellen der Kurve „Knoten je Lücke“ (aus den Buchten der Tabelle)

LB_STRONG, LB_WEAK = 5.0, 1.25                            # Verdikt „die Untergrenze wirkt“: Median des Verhältnisses Branch and Bound ohne Untergrenze (Stück 4) / IDA*
DEEPENING_BIG = 1.5                                       # Verdikt „die Vertiefung“: Verhältnis Branch and Bound mit Untergrenze / IDA* ab hier (oder bis 1 / hier) zählt als deutlich

# Verfahren: (Verfahren, Reihenfolge)
VARIANTS = (("enum", "index"), ("bb", "tight"), ("bblb", "tight"), ("ida", "index"), ("ida", "tight"), ("ida", "anti"))
LB_VARIANTS = (("bblb", "tight"), ("ida", "tight"))       # die Verfahren, die auch in der Zelle 5 x 4 gerechnet werden
VARIANT_KEYS = {v: f"{v[0]}/{v[1]}" for v in VARIANTS}
VARIANT_NAMES = {
    ("enum", "index"): "Volle Aufzählung (Stück 4)",
    ("bb", "tight"): "Branch and Bound ohne Untergrenze, engste Passung (Stück 4)",
    ("bblb", "tight"): "Branch and Bound mit Untergrenze, engste Passung",
    ("ida", "index"): "IDA*, Stapelnummern",
    ("ida", "tight"): "IDA*, engste Passung zuerst",
    ("ida", "anti"): "IDA*, schlechteste zuerst",
}
VARIANT_SHORT = {("enum", "index"): "volle Aufzählung", ("bb", "tight"): "B&B ohne UG", ("bblb", "tight"): "B&B mit UG",
                 ("ida", "index"): "IDA* Nummern", ("ida", "tight"): "IDA* engste", ("ida", "anti"): "IDA* schlechteste"}

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_CAPPED = "#b5545a"       # Lauf am Knotenlimit abgebrochen
COLOR_VARIANT = {("enum", "index"): "#7a8fa6", ("bb", "tight"): "#4c78a8", ("bblb", "tight"): "#d9822b",
                 ("ida", "index"): "#9bc7c0", ("ida", "tight"): "#2F6B65", ("ida", "anti"): "#1c4742"}
COLOR_LINES = ("#7a8fa6", "#2F6B65", "#d9822b", "#4c78a8")

# Sonderbuchten (in der Vormessung gefunden, Eigenschaften in tests/test_presets.py festgehalten)
MINI_SEED = 223        # 3 x 2: (5, 2), (1, 4), (6, 3) = der einzelne Blocker aus Stück 2 bis auf Vertauschen der Stapel: IDA* 6 Knoten (3 + 3)
EVERYDAY_SEED = 12     # 3 x 3, Platz 2: volle Aufzählung 229 Knoten, Branch and Bound ohne Untergrenze 29, mit Untergrenze und IDA* 11
GAP_SEED = 8           # 3 x 4, Platz 2: Lücke 5, also sechs Budgetstufen (IDA* 183 Knoten)
LIMIT_SEED = 5         # 4 x 4, Platz 2: Branch and Bound ohne Untergrenze gibt bei 500 000 Knoten auf, IDA* beweist das Optimum mit 2 516
MINI_BAY = ((1, 4), (5, 2), (6, 3))                       # die Mini-Bucht des ausgeschriebenen Baums (Stück 2: einzelner Blocker), Höchsthöhe 4
MINI_HEIGHT = 4
COUNTER_BAY = ((3, 6), (2, 4), (1, 5))                    # das Gegenbeispiel aus Stück 1, Höchsthöhe 4
COUNTER_HEIGHT = 4

PRESETS = {
    "Alltag (3 Stapel, 3 Lagen)": {"stacks": 3, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EVERYDAY_SEED},
    "Die Mini-Bucht": {"stacks": 3, "layers": 2, "extra": DEFAULT_EXTRA, "seed": MINI_SEED},
    "Große Lücke (3 Stapel, 4 Lagen)": {"stacks": 3, "layers": 4, "extra": DEFAULT_EXTRA, "seed": GAP_SEED},
    "Wo Stück 4 aufgibt (4 Stapel, 4 Lagen)": {"stacks": 4, "layers": 4, "extra": DEFAULT_EXTRA, "seed": LIMIT_SEED},
}
PRESET_HELP = {
    "Alltag (3 Stapel, 3 Lagen)": "9 Container: volle Aufzählung 229 Knoten, Branch and Bound ohne Untergrenze 29, IDA* 11.",
    "Die Mini-Bucht": "6 Container, ein einziger Blocker: IDA* braucht 6 Knoten, in zwei Budgetstufen zu 3.",
    "Große Lücke (3 Stapel, 4 Lagen)": "12 Container, Optimum 5 Hübe über der Untergrenze: sechs Budgetstufen, rund 180 Knoten.",
    "Wo Stück 4 aufgibt (4 Stapel, 4 Lagen)": "16 Container: Branch and Bound ohne Untergrenze gibt bei 500 000 Knoten auf, IDA* beweist das Optimum mit rund 2 500 (dauert einige Sekunden).",
}
