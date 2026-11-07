"""Abbildungen: Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Zahlen der Kurven."""

import ive_algorithm as A
import ive_constants as C
import ive_evaluation as ev
import ive_visualization as V


def _cell_colors(fig):
    out = {}
    for tr in fig.data:
        for txt, color in zip(tr.text, tr.marker.color):
            if txt:
                out[int(txt)] = color
    return out


def test_bay_colours_by_role(mini):
    bay, h = mini
    cols = _cell_colors(V.build_bay(bay, h, target=1))
    assert cols[1] == C.COLOR_TARGET and cols[4] == C.COLOR_BLOCK and cols[5] == cols[2] == cols[6] == cols[3] == C.COLOR_CELL
    assert sorted(_cell_colors(V.build_bay(bay, h))) == [1, 2, 3, 4, 5, 6] and len(V.build_bay(bay, h).data) == h


def test_blocker_cells_agree_with_the_kernel():
    from ive_scenario import make_bay
    assert V.blocker_cells(((1, 4), (5, 2), (6, 3))) == {(0, 1)}
    for sd in range(20):
        bay = make_bay(4, 3, sd)
        assert len(V.blocker_cells(bay)) == A.blocker_count(bay)


def _a():
    return ev.analyse(ev.Settings(3, 2, 2, C.MINI_SEED))


def test_axes_are_locked_in_every_figure():
    a = _a()
    bands = ev.load_bands()
    figs = [V.build_bay(a.bay, a.height), V.build_nodes(ev.result_rows(a)), V.build_stages(ev.stage_rows(a)), V.build_effects(bands["tabelle"]),
            V.build_gap(bands["luecke"]), V.build_tail(bands["tabelle"])]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_nodes_figure_marks_capped_runs_and_uses_a_log_axis():
    rows = [{"variant": ("enum", "index"), "nodes": 500_000, "capped": True, "nodes_text": "mehr als 500 000"},
            {"variant": ("ida", "tight"), "nodes": 1819, "capped": False, "nodes_text": "1 819"}]
    fig = V.build_nodes(rows)
    assert fig.layout.yaxis.type == "log" and list(fig.data[0].y) == [500_000, 1819] and list(fig.data[0].text) == ["mehr als 500 000", "1 819"]
    assert list(fig.data[0].marker.color) == [C.COLOR_CAPPED, C.COLOR_VARIANT[("ida", "tight")]]


def test_stages_figure_colours_the_found_stage_green_and_a_capped_one_red():
    rows = [{"budget": 3, "nodes": 3, "found": False, "result": "kein Blatt"}, {"budget": 4, "nodes": 12, "found": True, "result": "Blatt gefunden: Optimum"}]
    fig = V.build_stages(rows)
    assert list(fig.data[0].x) == ["3", "4"] and list(fig.data[0].y) == [3, 12] and list(fig.data[0].marker.color) == [C.COLOR_CELL, C.COLOR_TARGET]
    capped = V.build_stages([{"budget": 3, "nodes": 9, "found": False, "result": "Limit erreicht"}])
    assert list(capped.data[0].marker.color) == [C.COLOR_CAPPED]


def _stats(gain, deep, idx, anti):
    r = lambda m: {"n": 5, "median": m, "max": m}
    return {"gain": r(gain), "deep": r(deep), "order_index": r(idx), "order_anti": r(anti)}


def test_effects_figure_skips_missing_medians_and_has_four_series_on_a_log_axis():
    fig = V.build_effects({"3 × 3": _stats(2.0, 1.0, 1.0, 1.2), "5 × 4": _stats(None, 1.1, 1.0, 1.3)})
    assert len(fig.data) == 4 and fig.layout.yaxis.type == "log"
    assert list(fig.data[0].x) == ["3 × 3"] and list(fig.data[1].x) == ["3 × 3", "5 × 4"]            # 5 x 4 hat keinen Vergleich mit Stück 4


def test_gap_figure_has_two_dashed_styles_and_skips_missing_medians():
    table = {"0": {"n": 5, "ida": {"median": 3}, "bblb": {"median": 4}}, "1": {"n": 5, "ida": {"median": 9}, "bblb": {"median": None}}}
    fig = V.build_gap({"3 × 3": table})
    assert [t.name for t in fig.data] == ["3 × 3, IDA*", "3 × 3, B&B mit Untergrenze"] and fig.layout.yaxis.type == "log"
    assert list(fig.data[0].x) == [0, 1] and list(fig.data[1].x) == [0] and fig.data[0].line.dash == "solid" and fig.data[1].line.dash == "dot"


def test_tail_figure_has_three_series_on_a_log_axis_and_skips_unfinished_cells():
    ok = {"variants": {"ida/tight": {"median": 5, "mean": 7, "max": 20}}}
    none = {"variants": {"ida/tight": {"median": None, "mean": None, "max": None}}}
    fig = V.build_tail({"a": ok, "b": none})
    assert [t.name for t in fig.data] == ["Median", "Mittel", "Maximum"] and fig.layout.yaxis.type == "log" and list(fig.data[0].x) == ["a"]
