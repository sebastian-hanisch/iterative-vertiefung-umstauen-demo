"""Inhalt der App: Kennzahlen der Presets, Tabelle der Verfahren, Baum der Mini-Bucht, Verdikte, Permalink (AppTest, DEMO-PLAYBOOK §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import ive_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(at=None):
    if at is None:                                              # nicht `at or ...`: ein ungelaufener AppTest ist falsy
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(md.value for md in at.markdown)


def _bodies(at):
    return " ".join(e.value for kind in (at.success, at.info, at.warning) for e in kind)


NO_UG, IDA = "Branch and Bound ohne Untergrenze (Knoten)", "IDA*, engste Passung (Knoten)"


def test_default_bay_shows_the_six_methods_and_the_verdict():
    at = _run()
    m = _metrics(at)
    assert m[NO_UG] == "29" and m[IDA] == "11" and m["Optimum"] == "5" and m["Bucht"] == "3 × 3"
    text = _texts(at)
    assert "| Volle Aufzählung (Stück 4) | 229 | 114 | 5 |  |" in text and "| Branch and Bound ohne Untergrenze, engste Passung (Stück 4) | 29 | 1 | 5 |  |" in text
    assert "| Branch and Bound mit Untergrenze, engste Passung | 11 | 1 | 5 |  |" in text
    assert "| IDA*, Stapelnummern | 20 | 1 | 5 | 2 |" in text and "| IDA*, engste Passung zuerst | 11 | 1 | 5 | 2 |" in text and "| IDA*, schlechteste zuerst | 20 | 1 | 5 | 2 |" in text
    assert "das 2,6-Fache weniger (Optimum 5, Untergrenze 4, 2 Budgetstufen)" in _bodies(at)
    assert "| 4 | 5 | kein Blatt |" in text and "| 5 | 6 | Blatt gefunden: Optimum |" in text
    assert any("IDA* braucht 2 Budgetstufen, also Lücke + 1" in i.value for i in at.info)


def test_mini_preset_shows_six_nodes_in_two_stages():
    at = _preset(_run(), "Die Mini-Bucht")
    assert _metrics(at)[IDA] == "6" and _metrics(at)[NO_UG] == "5" and "| 1 | 3 | kein Blatt |" in _texts(at) and "| 2 | 3 | Blatt gefunden: Optimum |" in _texts(at)
    assert any("so klein, dass die Untergrenze nichts spart: 5 Knoten ohne Untergrenze, 6 mit IDA*" in i.value for i in at.info)


def test_gap_preset_shows_six_budget_stages():
    at = _preset(_run(), "Große Lücke (3 Stapel, 4 Lagen)")
    text = _texts(at)
    assert _metrics(at)[IDA] == "183" and "| IDA*, engste Passung zuerst | 183 | 1 | 11 | 6 |" in text
    assert text.count("kein Blatt |") >= 5 and "Lücke 5" in " ".join(m.delta for m in at.metric)


def test_limit_preset_gives_up_the_old_branch_and_bound_and_says_so():
    at = _preset(_run(), "Wo Stück 4 aufgibt (4 Stapel, 4 Lagen)")
    m = _metrics(at)
    assert m[NO_UG] == "mehr als 500 000" and m[IDA] == "2 516" and m["Optimum"] == "15"
    assert any("gibt bei 500 000 Knoten auf; IDA* mit engster Passung beweist das Optimum 15 mit 2 516 Knoten in 6 Budgetstufen" in w.value for w in at.warning)
    assert "| Volle Aufzählung (Stück 4) | mehr als 500 000 |" in _texts(at)


def test_the_mini_tree_and_the_counterexample_are_written_out_for_every_setting():
    at = _run()
    code = "\n".join(c.value for c in at.code)
    assert code.count("Knoten ") == 6 and code.count("abgeschnitten") == 2 and code.startswith("Budget 1:")
    assert any("6 Knoten in 2 Budgetstufen (3 + 3), Optimum 2" in s.value for s in at.success)
    assert ("IDA\\* mit engster Passung braucht **15 Knoten** (3 + 12 in den Budgetstufen 3, 4), Branch and Bound mit Untergrenze 17, Branch and Bound ohne Untergrenze (Stück 4) 27 "
            "und die volle Aufzählung 153.") in _texts(at)


def test_the_tables_and_the_verdicts_name_the_numbers_of_the_default_cell():
    at = _run()
    text = _texts(at)
    assert "| 3 × 3 (100) | 230 / 1 403 / 13 427 | 33 / 68 / 419 | 13 / 20 / 114 | 16 / 25 / 144 |" in text
    assert "| 4 × 3 (40) | 3 611,5 / 108 841 / 612 886, 10 über Limit |" in text and "| 5 × 4 (20) | nicht gerechnet | nicht gerechnet | 513 / 44 470 / 468 662 | 521,5 / 50 391 / 487 765 |" in text
    assert "| 3 × 3 | 2,25 (7,7) | 0,89 (1,8) | 1,14 | 1,39 (4,1) | 2,52, 5 |" in text and "| 5 × 4 | – | 0,97 (3,5) | – | – | 3,85, 8 |" in text
    bodies = _bodies(at)
    assert "Die Untergrenze spart im Median das 2,2-Fache der Knoten" in bodies and "100 Buchten" in bodies
    assert "Branch and Bound mit Untergrenze braucht im Median das 0,89-Fache der Knoten von IDA*" in bodies
    assert "Von 100 Buchten hat IDA* in 100 genau Lücke + 1 Budgetstufen gebraucht" in bodies
    assert "3 × 3: Mit jeder Einheit Lücke wächst der Median von IDA* um das 3,0, 2,4, 2,5, 2,1-Fache" in bodies
    assert "5 × 4: IDA* mit engster Passung braucht im Median 521,5 Knoten, im Mittel 50 391, im Maximum 487 765 (Mittel 97-mal der Median)." in bodies
    assert "4 × 4: Von 30 Buchten gibt bei 1 000 000 Knoten auf: die volle Aufzählung in 28, Branch and Bound ohne Untergrenze in 1" in bodies


def test_every_combination_of_the_stack_and_layer_sliders_has_a_stored_cell():
    cells = {(s, l) for s, l, _, _ in C.TABLE_CELLS}
    assert cells == {(s, l) for s in range(C.STACKS_MIN, C.STACKS_MAX + 1) for l in range(C.LAYERS_MIN, C.LAYERS_MAX + 1)}


def test_the_cell_of_the_setting_is_named_and_the_space_note_appears_for_other_space():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params.update({"stacks": "5", "layers": "4", "extra": "1", "seed": "5"})
    _run(at)
    text = _texts(at)
    assert "**Zelle 5 × 4 (Ihre Einstellung)**, Tabellen gelten für Platz 2, hier ist Platz 1 eingestellt:" in text
    assert "Von 20 Buchten hat IDA* in 20 genau Lücke + 1" in _bodies(at)
    assert "Der Vergleich mit Stück 4 ist so nicht möglich" in _bodies(at)                 # 5 x 4 hat keinen Stück-4-Vergleich
    at2 = _run()
    assert "**Zelle 3 × 3 (Ihre Einstellung)**:" in _texts(at2)


def test_permalink_is_clamped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["stacks"] = "99"
    at.query_params["layers"] = "-4"
    at.query_params["extra"] = "17"
    _run(at)
    assert at.sidebar.slider(key="stacks_slider").value == C.STACKS_MAX
    assert at.sidebar.slider(key="layers_slider").value == C.LAYERS_MIN
    assert at.sidebar.slider(key="extra_slider").value == C.EXTRA_MAX
