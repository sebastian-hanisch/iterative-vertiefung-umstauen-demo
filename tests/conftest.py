"""Gemeinsame Fixtures: die Mini-Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Die Mini-Bucht (einzelner Blocker aus Stück 2): 3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3). Untergrenze 1, Optimum 2.

    Handrechnung von IDA* (Stapelnummern): Budget 1: Wurzel (0 + 1 ≤ 1), die 4 auf Stapel 2 (1 + 1 = 2 > 1, abgeschnitten) und auf Stapel 3 (ebenso): 3 Knoten, kein Blatt.
    Budget 2: Wurzel, die 4 auf Stapel 2 (1 + 1 = 2 ≤ 2), von dort die 4 auf Stapel 1: leere Bucht nach 2 Hüben: 3 Knoten, Blatt. Zusammen 6 Knoten in 2 Stufen.
    Aus Stück 4: volle Aufzählung 9 Knoten und 5 Blätter, Branch and Bound ohne Untergrenze 5 (Stapelnummern, engste Passung) oder 7 (schlechteste zuerst)."""
    return ((1, 4), (5, 2), (6, 3)), 4


@pytest.fixture
def counter():
    """Das Gegenbeispiel aus Stück 1: (3, 6), (2, 4), (1, 5), Höchsthöhe 4. Untergrenze 3, Optimum 4. Aus Stück 4: volle Aufzählung 153 Knoten, Branch and Bound ohne
    Untergrenze 27 (engste Passung). IDA* mit engster Passung: Budget 3: 3 Knoten (Wurzel und ihre beiden abgeschnittenen Kinder), Budget 4: 12 Knoten, zusammen 15."""
    return ((3, 6), (2, 4), (1, 5)), 4
