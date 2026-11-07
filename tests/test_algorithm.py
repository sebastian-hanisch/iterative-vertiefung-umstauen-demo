"""Kern gegen Handrechnung und Eigenschaften (DEMO-PLAYBOOK §1b und §12)."""

import pytest

import ive_algorithm as A
from ive_scenario import make_bay, max_height


def test_autopop_and_blockers_by_hand(mini):
    bay, _ = mini
    assert A.autopop(bay) == (bay, [])                                 # die 1 liegt unter der 4
    assert A.autopop(((2, 1), (3,))) == (((), ()), [1, 2, 3])
    assert A.blocker_count(bay) == 1 and A.stack_blockers((1, 2, 3)) == 2 and A.stack_blockers((3, 2, 1)) == 0
    assert A.target_stack(bay) == (1, 0) and A.target_stack(((5, 3), (2, 1))) == (1, 1)


def test_mini_bay_by_hand_ida_in_every_order(mini):
    bay, h = mini
    for order in ("index", "tight"):
        r = A.search(bay, h, "ida", order)
        assert (r.optimum, r.nodes, r.leaves, r.capped, r.stages) == (2, 6, 1, False, ((1, 3, False), (2, 3, True))), order
    # schlechteste zuerst: Budget 2 probiert die 4 zuerst auf Stapel 3 (über der 3: 2 + 1 = 3 > 2, abgeschnitten) und erst dann auf dem leeren Stapel 1: ein Knoten mehr
    anti = A.search(bay, h, "ida", "anti")
    assert (anti.optimum, anti.nodes, anti.stages) == (2, 7, ((1, 3, False), (2, 4, True)))
    assert A.search(bay, h, "enum", "index").nodes == 9 and A.search(bay, h, "enum", "index").leaves == 5


def test_mini_bay_by_hand_branch_and_bound_with_and_without_the_lower_bound(mini):
    bay, h = mini
    for order, (bb, bblb) in {"index": (5, 5), "tight": (5, 5), "anti": (7, 7)}.items():
        assert A.search(bay, h, "bb", order).nodes == bb and A.search(bay, h, "bblb", order).nodes == bblb, order


def test_counterexample_by_hand(counter):
    bay, h = counter
    assert A.search(bay, h, "enum", "index").nodes == 153 and A.search(bay, h, "bb", "tight").nodes == 27
    ida = A.search(bay, h, "ida", "tight")
    assert (ida.optimum, ida.nodes) == (4, 15) and ida.stages == ((3, 3, False), (4, 12, True))
    assert A.search(bay, h, "ida", "index").stages == ((3, 3, False), (4, 14, True))      # die erste Stufe scheitert in jeder Reihenfolge mit 3 Knoten
    assert A.blocker_count(bay) == 3


def test_stage_nodes_add_up_to_the_node_count_and_the_last_stage_finds_the_leaf():
    for sd in range(60):
        bay, h = make_bay(3, 3, sd), max_height(3, 2)
        r = A.search(bay, h, "ida", "tight")
        assert sum(s[1] for s in r.stages) == r.nodes and [s[2] for s in r.stages] == [False] * (len(r.stages) - 1) + [True], sd
        assert [s[0] for s in r.stages] == list(range(A.blocker_count(bay), A.blocker_count(bay) + len(r.stages)))      # Budget wächst um 1 ab der Untergrenze
        assert r.first_leaf == r.optimum == r.stages[-1][0]                                                              # das erste Blatt hat genau das Budget als Hubzahl


def test_sorted_bay_has_exactly_one_node_and_one_leaf_in_every_mode():
    for mode in A.MODES:
        r = A.search(((5, 3), (2, 1), (6, 4)), 4, mode, "tight")
        assert (r.optimum, r.nodes, r.leaves) == (0, 1, 1), mode


def test_child_targets_orders_by_hand():
    stacks = ((7,), (5, 8), (9,), ())                                  # Blocker 3 kommt von Stapel 1 (Index 0), die übergebene Bucht ist die ohne ihn
    assert A.child_targets(stacks, 0, 6, 3, "index") == [1, 2, 3]
    assert A.child_targets(stacks, 0, 6, 3, "tight") == [1, 2, 3]
    assert A.child_targets(stacks, 0, 6, 3, "anti") == [3, 2, 1]
    assert A.child_targets(((7,), (2, 8), (1,), (4,)), 0, 6, 9, "tight") == [3, 1, 2]
    assert A.child_targets(((1, 2), (3, 4), (5,)), 0, 2, 9, "index") == [2]


def test_cap_counts_nodes_over_all_stages_for_ida(counter):
    bay, h = counter
    ok = A.search(bay, h, "ida", "tight", cap=15)
    assert not ok.capped and ok.nodes == 15 and ok.optimum == 4
    r = A.search(bay, h, "ida", "tight", cap=14)                       # genau ein Knoten zu wenig
    assert r.capped and r.optimum is None and r.nodes == 14 and r.stages == ((3, 3, False), (4, 11, False))
    assert sum(s[1] for s in r.stages) == r.nodes
    r2 = A.search(bay, h, "ida", "tight", cap=2)                       # schon die erste Stufe bricht ab
    assert r2.capped and r2.stages == ((3, 2, False),)


def test_cap_for_the_other_modes(counter):
    bay, h = counter
    r = A.search(bay, h, "enum", "index", cap=100)
    assert r.capped and r.optimum is None and r.nodes == 100
    assert not A.search(bay, h, "enum", "index", cap=153).capped and A.search(bay, h, "enum", "index", cap=152).capped
    assert not A.search(bay, h, "bblb", "tight", cap=A.search(bay, h, "bblb", "tight").nodes).capped


def test_unknown_options_are_rejected(mini):
    with pytest.raises(ValueError):
        A.search(*mini, "x", "tight")
    with pytest.raises(ValueError):
        A.search(*mini, "ida", "x")
    with pytest.raises(ValueError):
        A.child_targets(((1,), ()), 0, 3, 2, "x")


def test_ida_tree_lines_of_the_mini_bay(mini):
    lines = A.ida_tree_lines(*mini)
    assert lines[0] == "Budget 1:"
    assert lines[1] == "    Knoten 1: (1, 4) | (5, 2) | (6, 3) nach 0 Hüben; Untergrenze 1: 0 + 1 = 1 ≤ 1, weiter"
    assert lines[2] == "    → Container 4 von Stapel 1 auf Stapel 2"
    assert lines[3] == "        Knoten 2: () | (5, 2, 4) | (6, 3) nach 1 Hub, abgerufen 1; Untergrenze 1: 1 + 1 = 2 > 1, abgeschnitten"
    assert "    kein Blatt mit höchstens 1 Hub: Budget auf 2" in lines
    assert lines[-1] == "            Knoten 3: () | () | () nach 2 Hüben, abgerufen 2, 3, 4, 5, 6 – Blatt (leer): gefunden, Optimum 2"
    assert sum(1 for l in lines if l.lstrip().startswith("Knoten ")) == 6 and sum(1 for l in lines if l.startswith("Budget ")) == 2
    assert sum(1 for l in lines if l.endswith("abgeschnitten")) == 2


def test_ida_tree_lines_agree_with_the_search_node_counts():
    for bay, h in ((((3, 6), (2, 4), (1, 5)), 4), (make_bay(3, 2, 7), 4), (make_bay(3, 2, 100), 4)):
        for order in A.ORDERS:
            lines = A.ida_tree_lines(bay, h, order, max_nodes=400)
            assert sum(1 for l in lines if l.lstrip().startswith("Knoten ")) == A.search(bay, h, "ida", order).nodes, (bay, order)


def test_ida_tree_lines_refuse_big_trees(counter):
    with pytest.raises(ValueError):
        A.ida_tree_lines(*counter, max_nodes=14)                       # der Baum hat 17 (Stapelnummern) Knoten
    assert A.ida_tree_lines(*counter, max_nodes=17)
