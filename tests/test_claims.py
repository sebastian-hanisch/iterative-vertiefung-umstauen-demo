"""JEDE Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über die vorberechneten Tabellen (ive_bands.json, gegen eine frische Rechnung geprüft in
test_presets.py für die kleinen Zellen) und die Auswertungsfunktionen der App, über die festen Buchten je Zelle, nie über eine einzelne Bucht."""

import pytest

import ive_constants as C
import ive_evaluation as ev

BANDS = ev.load_bands()

# Zelle -> (Buchten, {Verfahren: (Median, Mittel, Maximum, Läufe über Limit)}, Verhältnis B&B ohne UG / IDA* (Median, Maximum, Buchten), B&B mit UG / IDA* (Median),
#           IDA* Nummern / engste (Median), IDA* schlechteste / engste (Median, Maximum), Budgetstufen (Mittel, Maximum))
TABELLE = {
    (3, 2): (100, {"enum/index": (9, 20, 161, 0), "bb/tight": (5, 6, 27, 0), "bblb/tight": (5, 5, 17, 0), "ida/index": (3, 5, 17, 0), "ida/tight": (3, 4, 15, 0), "ida/anti": (4, 5, 18, 0)},
             (1.50, 2.2, 100), 1.13, 1.00, (1.17, 2.2), (1.33, 2)),
    (4, 2): (100, {"enum/index": (67, 713, 20867, 0), "bb/tight": (7, 16, 117, 0), "bblb/tight": (7, 8, 16, 0), "ida/index": (4, 6, 17, 0), "ida/tight": (3, 4, 10, 0), "ida/anti": (6, 8, 27, 0)},
             (2.33, 11.7, 100), 2.00, 1.25, (1.67, 3.0), (1.30, 2)),
    (3, 3): (100, {"enum/index": (230, 1403, 13427, 0), "bb/tight": (33, 68, 419, 0), "bblb/tight": (13, 20, 114, 0), "ida/index": (18, 32, 176, 0), "ida/tight": (16, 25, 144, 0), "ida/anti": (20, 37, 218, 0)},
             (2.25, 7.7, 100), 0.89, 1.14, (1.39, 4.1), (2.52, 5)),
    (5, 2): (60, {"enum/index": (1721, 25019, 654257, 1), "bb/tight": (25, 80, 1268, 0), "bblb/tight": (13, 13, 25, 0), "ida/index": (6, 7, 24, 0), "ida/tight": (4, 6, 12, 0), "ida/anti": (10, 10, 27, 0)},
             (6.25, 105.7, 60), 3.00, 1.25, (2.00, 3.0), (1.32, 2)),
    (4, 3): (40, {"enum/index": (3611.5, 108841, 612886, 10), "bb/tight": (120, 1221, 15455, 0), "bblb/tight": (16, 34, 306, 0), "ida/index": (17, 46, 409, 0), "ida/tight": (12, 33, 360, 0), "ida/anti": (22, 67, 608, 0)},
             (9.90, 154.6, 40), 1.35, 1.28, (2.02, 5.9), (2.17, 5)),
    (3, 4): (40, {"enum/index": (18163.5, 82533, 696375, 0), "bb/tight": (384, 625, 3665, 0), "bblb/tight": (51, 79, 379, 0), "ida/index": (89, 143, 785, 0), "ida/tight": (65, 121, 672, 0), "ida/anti": (128, 178, 1030, 0)},
             (5.25, 12.6, 40), 0.71, 1.13, (1.55, 3.2), (4.28, 8)),
    (5, 3): (20, {"enum/index": (12693, 212067, 800161, 15), "bb/tight": (1361, 32211, 253266, 0), "bblb/tight": (31, 43, 206, 0), "ida/index": (27, 57, 295, 0), "ida/tight": (18.5, 33, 218, 0), "ida/anti": (48, 102, 903, 0)},
             (183.79, 2739.7, 20), 1.79, 1.39, (2.21, 9.4), (2.00, 4)),
    (4, 4): (30, {"enum/index": (251062.5, 251062, 358087, 28), "bb/tight": (17804, 91461, 755046, 1), "bblb/tight": (286, 1088, 9711, 0), "ida/index": (292.5, 1235, 10506, 0), "ida/tight": (291, 1106, 11739, 0), "ida/anti": (529.5, 1555, 11386, 0)},
             (75.42, 1230.3, 29), 0.98, 1.10, (1.84, 4.9), (4.00, 8)),
    (5, 4): (20, {"bblb/tight": (513, 44470, 468662, 0), "ida/tight": (521.5, 50391, 487765, 0)}, (None, None, 0), 0.97, None, (None, None), (3.85, 8)),
}


@pytest.mark.parametrize("cell", list(TABELLE))
def test_readme_table_cell(cell):
    n, variants, gain, deep, idx, anti, stages = TABELLE[cell]
    st = BANDS["tabelle"][ev.cell_key(*cell)]
    assert st["n"] == n and set(st["variants"]) == set(variants)
    for key, (med, mean, mx, over) in variants.items():
        v = st["variants"][key]
        assert (v["median"], round(v["mean"]), v["max"], v["over"]) == (med, mean, mx, over), key
    g = st["gain"]
    assert (g["median"] if g["median"] is None else round(g["median"], 2), g["max"] if g["max"] is None else round(g["max"], 1), g["n"]) == gain
    assert round(st["deep"]["median"], 2) == deep
    if idx is not None:
        assert round(st["order_index"]["median"], 2) == idx and (round(st["order_anti"]["median"], 2), round(st["order_anti"]["max"], 1)) == anti
    assert (round(st["stages"]["mean"], 2), st["stages"]["max"]) == stages and st["stages"]["equal_gap_plus_1"] == st["stages"]["n"] == n


def test_the_untergrenze_gives_the_big_gain_in_every_cell_and_the_deepening_a_small_one():
    for cell, (n, variants, gain, deep, *_rest) in TABELLE.items():
        if gain[0] is not None:
            assert gain[0] >= 1.5, cell                                       # B&B ohne Untergrenze braucht mindestens das 1,5-Fache von IDA*
        assert 0.7 <= deep <= 3.0, cell                                       # die Vertiefung gegen B&B mit Untergrenze: 0,71 bis 3,0
    assert min(g[2][0] for g in TABELLE.values() if g[2][0] is not None) == 1.5 and max(g[2][0] for g in TABELLE.values() if g[2][0] is not None) == 183.79
    assert min(g[3] for g in TABELLE.values()) == 0.71 and max(g[3] for g in TABELLE.values()) == 3.0


def test_the_untergrenze_gain_is_larger_than_the_deepening_gain_from_five_stacks_or_four_layers_on():
    for cell in ((5, 2), (4, 3), (3, 4), (5, 3), (4, 4)):
        gain, deep = TABELLE[cell][2][0], TABELLE[cell][3]
        assert gain > deep and gain >= 5.0 and (cell == (5, 2) or deep < 2.0), cell


def test_the_deepening_wins_where_gaps_are_small_and_loses_where_they_are_large():
    # 4 x 2, 5 x 2, 5 x 3: IDA* im Median mindestens 1,75-mal sparsamer als B&B mit Untergrenze; 3 x 3, 3 x 4: B&B mit Untergrenze sparsamer
    assert all(TABELLE[c][3] >= 1.75 for c in ((4, 2), (5, 2), (5, 3)))
    assert TABELLE[(3, 3)][3] < 1.0 and TABELLE[(3, 4)][3] < 1.0
    assert BANDS["tabelle"]["3,4"]["stages"]["mean"] > BANDS["tabelle"]["5,2"]["stages"]["mean"]


def test_the_order_effect_is_small_in_the_median_with_the_lower_bound():
    meds_idx = [v[4] for v in TABELLE.values() if v[4] is not None]
    meds_anti = [v[5][0] for v in TABELLE.values() if v[5][0] is not None]
    assert max(meds_idx) <= 1.39 and min(meds_idx) >= 1.0 and max(meds_anti) <= 2.21 and min(meds_anti) >= 1.17
    assert max(v[5][1] for v in TABELLE.values() if v[5][1] is not None) == 9.4


def test_runs_over_the_limit_per_cell():
    over = {cell: BANDS["tabelle"][ev.cell_key(*cell)]["variants"]["enum/index"]["over"] for cell in TABELLE if cell != (5, 4)}
    assert over == {(3, 2): 0, (4, 2): 0, (3, 3): 0, (5, 2): 1, (3, 4): 0, (4, 3): 10, (5, 3): 15, (4, 4): 28}
    assert BANDS["tabelle"]["4,4"]["variants"]["bb/tight"]["over"] == 1
    for cell in TABELLE:
        for key in ("bblb/tight", "ida/tight"):
            assert BANDS["tabelle"][ev.cell_key(*cell)]["variants"][key]["over"] == 0, (cell, key)


def test_the_table_cells_and_the_documented_cells_agree():
    assert [(s, l, n) for s, l, n, _ in C.TABLE_CELLS] == [(s, l, TABELLE[(s, l)][0]) for s, l, _, _ in C.TABLE_CELLS]
    assert {(s, l) for s, l, _, _ in C.TABLE_CELLS} == set(TABELLE)


def test_the_last_stage_share_falls_with_the_gap_across_cells():
    shares = {cell: BANDS["tabelle"][ev.cell_key(*cell)]["last_share"] for cell in TABELLE}
    assert shares[(3, 2)] == shares[(4, 2)] == shares[(5, 2)] == 1.0                    # kleine Zellen: nur die letzte Stufe zählt (Lücke 0 oder 1 mit Untergrenze 1)
    assert round(shares[(3, 3)], 2) == 0.5 and round(shares[(4, 3)], 2) == 0.54 and round(shares[(3, 4)], 2) == 0.21 and round(shares[(5, 3)], 2) == 0.48
    assert round(shares[(4, 4)], 2) == 0.28 and round(shares[(5, 4)], 2) == 0.32


def test_readme_gap_table_3x3():
    t = BANDS["luecke"]["3,3"]
    assert {g: (r["n"], r["ida"]["median"], r["bblb"]["median"], round(r["last_share"] * 100)) for g, r in t.items()} == {
        "0": (19, 3, 5, 100), "1": (31, 9, 9, 57), "2": (33, 22, 19, 38), "3": (13, 55, 40, 17), "4": (4, 113, 73, 8)}
    assert [round(x, 1) for x in ev.growth_factors(t, "ida")] == [3.0, 2.4, 2.5, 2.1]
    assert [round(x, 1) for x in ev.growth_factors(t, "bblb")] == [1.8, 2.1, 2.1, 1.8]


def test_readme_gap_table_3x4():
    t = BANDS["luecke"]["3,4"]
    assert {g: (r["n"], r["ida"]["median"], r["bblb"]["median"], round(r["last_share"] * 100)) for g, r in t.items()} == {
        "1": (5, 12, 13, 50), "2": (10, 37, 36, 29), "3": (7, 54, 37, 29), "4": (10, 105.5, 78.5, 13), "5": (4, 171, 105.5, 8), "6": (3, 399, 238, 3), "7": (1, 672, 354, 2)}
    assert sum(r["n"] for r in t.values()) == 40


def test_ida_beats_the_bound_only_at_small_gaps():
    t = BANDS["luecke"]["3,3"]
    assert t["0"]["ida"]["median"] < t["0"]["bblb"]["median"] and all(t[g]["ida"]["median"] > t[g]["bblb"]["median"] for g in ("2", "3", "4"))


def test_the_tail_of_the_biggest_cell():
    v = BANDS["tabelle"]["5,4"]["variants"]["ida/tight"]
    assert (v["median"], round(v["mean"]), v["max"]) == (521.5, 50391, 487765) and round(v["mean"] / v["median"]) == 97
    assert BANDS["tabelle"]["5,4"]["full"] is False and BANDS["tabelle"]["5,4"]["gain"]["n"] == 0
