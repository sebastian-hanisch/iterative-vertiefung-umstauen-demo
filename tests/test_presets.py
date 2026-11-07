"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Eigenschaften der Sonderbuchten und der vorberechneten Tabellen."""

import pytest

import ive_algorithm as A
import ive_constants as C
import ive_evaluation as ev
import ive_presets as P
from ive_scenario import canonical, make_bay, max_height


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.STACKS_MIN <= preset["stacks"] <= C.STACKS_MAX and C.LAYERS_MIN <= preset["layers"] <= C.LAYERS_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]))


def _nodes(a):
    return {v: a.res(v).nodes for v in C.VARIANTS}


def test_everyday_preset():
    a = _analysis("Alltag (3 Stapel, 3 Lagen)")
    n = _nodes(a)
    assert (a.lower, a.optimum, a.gap) == (4, 5, 1) and n[("enum", "index")] == 229 and n[("bb", "tight")] == 29 and n[("bblb", "tight")] == 11 and n[("ida", "tight")] == 11
    assert len(a.res(("ida", "tight")).stages) == 2 and not any(r.capped for r in a.results.values())


def test_mini_preset_is_the_stage_two_bay_with_six_nodes():
    p = C.PRESETS["Die Mini-Bucht"]
    assert canonical(make_bay(p["stacks"], p["layers"], p["seed"])) == canonical(C.MINI_BAY)
    a = _analysis("Die Mini-Bucht")
    assert (a.lower, a.optimum) == (1, 2) and a.res(("enum", "index")).nodes == 9
    assert a.res(("ida", "tight")).stages == ((1, 3, False), (2, 3, True)) and a.res(("ida", "tight")).nodes == 6 and a.res(("ida", "index")).nodes == 6


def test_gap_preset_has_six_budget_stages():
    a = _analysis("Große Lücke (3 Stapel, 4 Lagen)")
    ida = a.res(("ida", "tight"))
    assert (a.lower, a.optimum, a.gap) == (6, 11, 5) and len(ida.stages) == 6 and ida.nodes == 183 and not any(r.capped for r in a.results.values())
    assert sum(s[1] for s in ida.stages) == 183 and ida.stages[-1][2]


def test_limit_preset_breaks_the_old_branch_and_bound_but_not_ida():
    a = _analysis("Wo Stück 4 aufgibt (4 Stapel, 4 Lagen)")
    assert a.res(("enum", "index")).capped and a.res(("bb", "tight")).capped and a.res(("bb", "tight")).nodes == C.LIVE_CAP
    ida = a.res(("ida", "tight"))
    assert not ida.capped and ida.nodes == 2516 and a.optimum == 15 and a.lower == 10 and len(ida.stages) == 6
    assert not a.res(("bblb", "tight")).capped


def test_the_named_seeds_are_the_documented_bays():
    assert (C.MINI_SEED, C.EVERYDAY_SEED, C.GAP_SEED, C.LIMIT_SEED) == (223, 12, 8, 5)
    assert make_bay(3, 4, C.GAP_SEED) == make_bay(3, 4, 8) and C.MINI_HEIGHT == 4 and C.COUNTER_HEIGHT == 4


@pytest.mark.parametrize("cell", [(3, 2, 100), (4, 2, 100)])
def test_stored_table_cells_equal_a_fresh_computation(cell):
    stacks, layers, n = cell
    stored = ev.load_bands()["tabelle"][ev.cell_key(stacks, layers)]
    assert stored == ev.cell_stats(ev.cell_rows(stacks, layers, C.DEFAULT_EXTRA, range(n)))


def test_stored_3x3_table_and_gap_table_equal_a_fresh_computation():
    rows = ev.cell_rows(3, 3, C.DEFAULT_EXTRA, range(100))
    bands = ev.load_bands()
    assert bands["tabelle"][ev.cell_key(3, 3)] == ev.cell_stats(rows)
    assert bands["luecke"][ev.cell_key(3, 3)] == ev.gap_table(rows)


def test_stored_cell_without_the_old_methods_equals_a_fresh_computation_on_a_prefix():
    rows = ev.cell_rows(5, 4, C.DEFAULT_EXTRA, range(3), full=False)
    assert set(rows[0]) == {"seed", "lb", "opt", "stages", "last", "bblb/tight", "ida/tight"}
    stored = ev.load_bands()["tabelle"][ev.cell_key(5, 4)]
    assert stored["full"] is False and set(stored["variants"]) == {"bblb/tight", "ida/tight"} and stored["gain"]["median"] is None


def test_every_band_cell_exists():
    bands = ev.load_bands()
    assert set(bands["tabelle"]) == {ev.cell_key(s, l) for s, l, _, _ in C.TABLE_CELLS}
    assert set(bands["luecke"]) == {ev.cell_key(s, l) for s, l in C.GAP_CELLS}
    assert all(bands["tabelle"][ev.cell_key(s, l)]["n"] == n and bands["tabelle"][ev.cell_key(s, l)]["full"] == full for s, l, n, full in C.TABLE_CELLS)


def test_cell_rows_use_the_fixed_seeds_and_cap():
    rows = ev.cell_rows(3, 2, 2, range(10))
    assert [r["seed"] for r in rows] == list(range(10))
    for r in rows:
        bay = make_bay(3, 2, r["seed"])
        ida = A.search(bay, max_height(2, 2), "ida", "tight")
        assert r["lb"] == A.blocker_count(bay) and r["ida/tight"] == ida.nodes and r["opt"] == ida.optimum
        assert r["stages"] == len(ida.stages) and r["last"] == ida.stages[-1][1] and r["enum/index"] == A.search(bay, max_height(2, 2), "enum", "index").nodes
    small = ev.cell_rows(4, 3, 2, [3], cap=20)
    assert small[0]["enum/index"] is None and small[0]["ida/tight"] is None and small[0]["opt"] is None and small[0]["stages"] is None


def test_the_table_cells_are_the_documented_ones():
    assert C.TABLE_CELLS[:7] == ((3, 2, 100, True), (4, 2, 100, True), (3, 3, 100, True), (5, 2, 60, True), (4, 3, 40, True), (3, 4, 40, True), (5, 3, 20, True))
    assert C.TABLE_CELLS[7:] == ((4, 4, 30, True), (5, 4, 20, False))
