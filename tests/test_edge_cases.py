"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import ive_algorithm as A
import ive_evaluation as ev


def test_two_stacks_one_hub_in_every_mode_and_order():
    for mode in A.MODES:
        for order in A.ORDERS:
            r = A.search(((1, 2), ()), 3, mode, order)
            assert (r.optimum, r.nodes, r.leaves) == (1, 2, 1), (mode, order)      # Wurzel, ein Hub auf den leeren Stapel, Blatt
    assert A.search(((1, 2), ()), 3, "ida", "tight").stages == ((1, 2, True),)


def test_single_container_and_empty_bay():
    assert A.search(((1,), ()), 2, "enum", "index").nodes == 1
    assert A.search(((), ()), 2, "ida", "tight").optimum == 0 and A.search(((), ()), 2, "ida", "tight").stages == ((0, 1, True),)


def test_exactly_two_containers_in_each_order():
    assert A.search(((2,), (1,)), 2, "ida", "index").optimum == 0
    assert A.search(((2, 1),), 2, "ida", "index").optimum == 0
    assert A.search(((1, 2), ()), 2, "ida", "index").optimum == 1


def test_only_one_free_slot_leaves_exactly_one_child_per_hub():
    r = A.search(((1, 5), (2, 3), (4, 6)), 3, "ida", "index")          # Höchsthöhe 3: jeder Blocker findet höchstens einen freien Platz
    assert r.optimum is not None and r.leaves == 1


def test_capped_result_never_claims_an_optimum_and_the_bay_analysis_says_so(counter):
    bay, h = counter
    r = A.search(bay, h, "enum", "index", cap=10)
    assert r.optimum is None and r.capped and r.leaves <= 10
    capped = A.SearchResult(None, 10, 2, True, None)
    a = ev.Analysis(bay, h, 3, {v: capped for v in ev.C.VARIANTS})
    assert a.optimum is None and a.gap is None


def test_num_and_factor_text():
    assert ev.num(5) == "5" and ev.num(1234) == "1 234" and ev.num(1_000_000) == "1 000 000"
    assert ev.factor_text(1.0) == "1,0" and ev.factor_text(9.94) == "9,9" and ev.factor_text(10.0) == "10" and ev.factor_text(47.4) == "47"
    assert ev.ratio_text(1.5) == "1,50" and ev.ratio_text(0.714) == "0,71"


def test_cell_stats_with_all_runs_over_the_limit_has_no_medians():
    rows = [{"seed": 0, "lb": 5, "opt": None, "stages": None, "last": None, "enum/index": None, "bb/tight": None, "bblb/tight": None, "ida/index": None, "ida/tight": None, "ida/anti": None}]
    st = ev.cell_stats(rows)
    assert st["variants"]["ida/tight"] == {"ok": 0, "over": 1, "median": None, "mean": None, "max": None}
    assert st["gain"]["median"] is None and st["deep"]["median"] is None and st["order_anti"]["n"] == 0
    assert st["stages"] == {"n": 0, "mean": None, "max": None, "equal_gap_plus_1": 0} and st["last_share"] is None


def test_cell_stats_without_the_variants_of_stage_four_leaves_the_gain_empty():
    rows = [{"seed": 0, "lb": 2, "opt": 3, "stages": 2, "last": 5, "bblb/tight": 9, "ida/tight": 8}]
    st = ev.cell_stats(rows, full=False)
    assert set(st["variants"]) == {"bblb/tight", "ida/tight"} and st["gain"]["median"] is None and st["deep"]["median"] == 9 / 8
    assert st["last_share"] == 5 / 8 and st["stages"]["equal_gap_plus_1"] == 1
