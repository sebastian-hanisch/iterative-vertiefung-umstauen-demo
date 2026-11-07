"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import ive_algorithm as A
import ive_constants as C
import ive_evaluation as ev


def _res(nodes, opt=2, capped=False, leaves=1, stages=()):
    return A.SearchResult(None if capped else opt, nodes, leaves, capped, None if capped else opt, stages)


def _analysis(bb, ida, opt=5, lower=4, bblb=None, bb_capped=False, ida_capped=False, others_capped=False):
    stages = tuple((lower + i, 1, i == opt - lower) for i in range(opt - lower + 1))
    results = {("enum", "index"): _res(bb * 8, opt, bb_capped), ("bb", "tight"): _res(bb, opt, bb_capped),
               ("bblb", "tight"): _res(bblb if bblb is not None else ida, opt, others_capped),
               ("ida", "index"): _res(ida, opt, ida_capped, stages=stages), ("ida", "tight"): _res(ida, opt, ida_capped, stages=stages),
               ("ida", "anti"): _res(ida, opt, ida_capped, stages=stages)}
    return ev.Analysis(((1,),), 4, lower, results)


def test_bay_verdict_success_names_nodes_factor_optimum_lower_bound_and_stages():
    kind, text = ev.verdict_bay(_analysis(29, 11, opt=5, lower=4, bblb=11))
    assert kind == "info"                                               # Faktor 2,6: mäßig
    assert "Branch and Bound ohne Untergrenze braucht 29 Knoten, IDA* mit engster Passung 11: das 2,6-Fache weniger (Optimum 5, Untergrenze 4, 2 Budgetstufen)." in text
    assert "Branch and Bound mit Untergrenze braucht 11." in text
    kind, text = ev.verdict_bay(_analysis(365409, 297, opt=14, lower=10, bblb=200))
    assert kind == "success" and "das 1230-Fache weniger (Optimum 14, Untergrenze 10, 5 Budgetstufen)" in text


def test_bay_verdict_thresholds_at_five_and_one_and_a_quarter():
    assert ev.verdict_bay(_analysis(50, 10))[0] == "success"           # genau das Fünffache zählt
    assert ev.verdict_bay(_analysis(49, 10))[0] == "info"
    assert ev.verdict_bay(_analysis(125, 100))[0] == "info" and "das 1,2-Fache weniger" in ev.verdict_bay(_analysis(125, 100))[1]   # genau 1,25 zählt als mäßig
    kind, text = ev.verdict_bay(_analysis(124, 100))
    assert kind == "info" and "so klein, dass die Untergrenze nichts spart: 124 Knoten ohne Untergrenze, 100 mit IDA*" in text
    assert C.LB_STRONG == 5.0 and C.LB_WEAK == 1.25


def test_bay_verdict_when_the_old_branch_and_bound_gives_up():
    kind, text = ev.verdict_bay(_analysis(500_000, 2516, opt=9, lower=5, bblb=1500, bb_capped=True))
    assert kind == "warning"
    assert ("Branch and Bound ohne Untergrenze (Stück 4) gibt bei 500 000 Knoten auf; IDA* mit engster Passung beweist das Optimum 9 mit 2 516 Knoten in 5 Budgetstufen "
            "(Untergrenze 5).") in text and "Branch and Bound mit Untergrenze braucht 1 500." in text


def test_bay_verdict_when_ida_gives_up_but_another_method_finishes():
    results = {v: _res(500_000, capped=True) for v in C.VARIANTS}
    results[("bblb", "tight")] = _res(900, 6)
    kind, text = ev.verdict_bay(ev.Analysis(((1,),), 4, 5, results))
    assert kind == "warning" and "IDA* mit engster Passung gibt bei 500 000 Knoten auf; ein anderes Verfahren beweist das Optimum 6 mit 900 Knoten" in text


def test_bay_verdict_when_everything_gives_up():
    a = ev.Analysis(((1,),), 4, 1, {v: _res(500_000, capped=True) for v in C.VARIANTS})
    kind, text = ev.verdict_bay(a)
    assert kind == "warning" and "Alle Verfahren geben bei 500 000 Knoten auf" in text and "Untergrenze 1" in text and a.optimum is None


def test_bay_verdict_mentions_when_branch_and_bound_with_the_bound_gives_up():
    kind, text = ev.verdict_bay(_analysis(100, 10, bblb=7, others_capped=True))
    assert "Branch and Bound mit Untergrenze gibt auf." in text


def test_result_rows_and_stage_rows_by_hand():
    a = _analysis(29, 11, opt=6, lower=4)
    rows = ev.result_rows(a)
    assert [r["name"] for r in rows] == [C.VARIANT_NAMES[v] for v in C.VARIANTS] and rows[1]["nodes_text"] == "29" and rows[1]["optimum"] == "6"
    assert [r["stages"] for r in rows] == [None, None, None, 3, 3, 3]
    assert ev.stage_rows(a) == [{"budget": 4, "nodes": 1, "found": False, "result": "kein Blatt"}, {"budget": 5, "nodes": 1, "found": False, "result": "kein Blatt"},
                                {"budget": 6, "nodes": 1, "found": True, "result": "Blatt gefunden: Optimum"}]
    capped = ev.stage_rows(ev.Analysis(((1,),), 4, 3, {**a.results, ("ida", "tight"): _res(100, capped=True, stages=((3, 40, False), (4, 60, False)))}))
    assert capped[-1]["result"] == "Limit erreicht" and capped[0]["result"] == "kein Blatt"
    assert ev.result_rows(_analysis(500_000, 5, bb_capped=True))[1]["nodes_text"] == "mehr als 500 000"
    assert a.gap == 2


def _stats(gain=12.0, deep=1.1, stages_ok=40, n=40, tight_over=0, mean=200.0, median=100.0, mx=900, enum_over=0):
    var = lambda over: {"ok": n - over, "over": over, "median": median, "mean": mean, "max": mx}
    return {"n": n, "full": True,
            "variants": {"enum/index": var(enum_over), "bb/tight": var(0), "bblb/tight": var(0), "ida/index": var(0), "ida/tight": var(tight_over), "ida/anti": var(0)},
            "gain": {"n": n, "median": gain, "max": 90.0}, "deep": {"n": n, "median": deep, "max": 3.0}, "order_index": {"n": n, "median": 1.0, "max": 2.0},
            "order_anti": {"n": n, "median": 1.2, "max": 3.0}, "stages": {"n": n, "mean": 2.5, "max": 6, "equal_gap_plus_1": stages_ok}, "last_share": 0.5}


def test_gain_verdict_three_states_and_numbers():
    kind, text = ev.verdict_gain(_stats(gain=12.0))
    assert kind == "success"
    assert "spart im Median das 12-Fache der Knoten" in text and "40 Buchten, Maximum 90" in text and "Die Untergrenze wirkt hier stark" in text
    assert ev.verdict_gain(_stats(gain=5.0))[0] == "success" and ev.verdict_gain(_stats(gain=4.9))[0] == "info"
    assert ev.verdict_gain(_stats(gain=1.25))[0] == "info"
    kind, text = ev.verdict_gain(_stats(gain=1.2))
    assert kind == "warning" and "kaum" in text
    assert ev.verdict_gain({**_stats(), "gain": {"n": 0, "median": None, "max": None}})[0] == "warning"


def test_deepening_verdict_three_states_and_numbers():
    kind, text = ev.verdict_deepening(_stats(deep=1.13))
    assert kind == "info" and "das 1,13-Fache der Knoten von IDA* (40 Buchten, Maximum 3,0)" in text and "nicht von der Vertiefung" in text
    assert "IDA* ist hier im Median merklich sparsamer" in ev.verdict_deepening(_stats(deep=1.5))[1]            # genau 1,5 zählt
    assert "nah beieinander" in ev.verdict_deepening(_stats(deep=1.49))[1] and "nah beieinander" in ev.verdict_deepening(_stats(deep=0.7))[1]
    assert "Branch and Bound mit Untergrenze ist hier im Median merklich sparsamer" in ev.verdict_deepening(_stats(deep=0.66))[1]
    assert ev.verdict_deepening({**_stats(), "deep": {"n": 0, "median": None, "max": None}})[0] == "warning"


def test_stages_verdict_counts_the_bays_with_gap_plus_one():
    kind, text = ev.verdict_stages(_stats())
    assert kind == "success" and "Von 40 Buchten hat IDA* in 40 genau Lücke + 1 Budgetstufen gebraucht (im Mittel 2,50, höchstens 6)" in text
    kind, text = ev.verdict_stages(_stats(stages_ok=39))
    assert kind == "warning" and "in 39 genau" in text
    assert ev.verdict_stages({**_stats(), "stages": {"n": 0, "mean": None, "max": None, "equal_gap_plus_1": 0}})[0] == "warning"


def _gap(medians, bblb=None, last=(1.0, 0.5, 0.25)):
    t = {}
    for i, m in enumerate(medians):
        t[str(i)] = {"n": 10, "ida": {"ok": 10, "over": 0, "median": m, "mean": m, "max": m},
                     "bblb": {"ok": 10, "over": 0, "median": (bblb or medians)[i], "mean": 1, "max": 1}, "last_share": last[i]}
    return t


def test_gap_growth_and_verdict_by_hand():
    t = _gap([3, 9, 22])
    assert ev.growth_factors(t, "ida") == [3.0, 22 / 9]
    kind, text = ev.verdict_gap(_gap([3, 9, 18], bblb=[4, 8, 16]), "3 × 3")
    assert kind == "info" and "3 × 3: Mit jeder Einheit Lücke wächst der Median von IDA* um das 3,0, 2,0-Fache" in text
    assert "der von Branch and Bound mit Untergrenze um das 2,0, 2,0-Fache" in text and "von 100 % (Lücke 0) auf 25 % (Lücke 2)" in text
    one = {"0": _gap([3])["0"]}
    assert "zu wenige" in ev.verdict_gap(one, "x")[1]
    gapped = {"0": _gap([3, 9, 22])["0"], "2": _gap([3, 9, 22])["2"]}
    assert ev.growth_factors(gapped, "ida") == []                       # Lücken 0 und 2 sind nicht aufeinanderfolgend


def test_tail_verdict_and_over_limit_verdict():
    kind, text = ev.verdict_tail(_stats(median=522, mean=50391, mx=487765), "5 × 4")
    assert kind == "info" and "5 × 4: IDA* mit engster Passung braucht im Median 522 Knoten, im Mittel 50 391, im Maximum 487 765 (Mittel 97-mal der Median)." in text
    kind, text = ev.verdict_tail(_stats(tight_over=2), "5 × 4")
    assert kind == "warning" and "2 Läufe lagen über dem Limit." in text
    none = _stats()
    none["variants"]["ida/tight"] = {"ok": 0, "over": 5, "median": None, "mean": None, "max": None}
    assert ev.verdict_tail(none, "x")[0] == "warning"
    kind, text = ev.verdict_over_limit(_stats(enum_over=28, n=30))
    assert kind == "warning" and "Von 30 Buchten gibt bei 1 000 000 Knoten auf: die volle Aufzählung in 28, Branch and Bound ohne Untergrenze in 0" in text
    assert ev.verdict_over_limit(_stats())[0] == "info"
    short = {**_stats(), "variants": {"bblb/tight": _stats()["variants"]["bblb/tight"], "ida/tight": _stats()["variants"]["ida/tight"]}}
    assert "die volle Aufzählung" not in ev.verdict_over_limit(short)[1]


def test_num_f_by_hand():
    assert ev.num_f(5.0) == "5" and ev.num_f(71.5) == "71,5" and ev.num_f(525188.5) == "525 188,5" and ev.num_f(1234.0) == "1 234"


def test_gap_table_by_hand():
    rows = [{"lb": 1, "opt": 1, "stages": 1, "last": 5, "ida/tight": 5, "bblb/tight": 5}, {"lb": 1, "opt": 1, "stages": 1, "last": 7, "ida/tight": 7, "bblb/tight": 9},
            {"lb": 2, "opt": 4, "stages": 3, "last": 4, "ida/tight": 10, "bblb/tight": None}, {"lb": 3, "opt": None, "stages": None, "last": None, "ida/tight": None, "bblb/tight": None}]
    t = ev.gap_table(rows)
    assert set(t) == {"0", "2"} and t["0"]["n"] == 2 and t["0"]["ida"]["median"] == 6 and t["0"]["bblb"]["median"] == 7 and t["0"]["last_share"] == 1.0
    assert t["2"]["ida"]["median"] == 10 and t["2"]["bblb"]["median"] is None and t["2"]["bblb"]["over"] == 1 and t["2"]["last_share"] == 0.4
