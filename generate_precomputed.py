"""Erzeugt ive_bands.json: Knotenzahlen der festen Buchten (Seeds ab 0) für zwei Auswertungen.

    python generate_precomputed.py

"tabelle": je Zelle (Stapel, Lagen) Kennzahlen der sechs Verfahren (ive_constants.TABLE_CELLS; große Zellen mit weniger Buchten, 5 x 4 nur mit den beiden
           Verfahren mit Untergrenze), Platz 2.
"luecke":  Median der Knoten je Lücke (Optimum - Untergrenze) für IDA* und Branch and Bound mit Untergrenze (aus denselben Buchten wie die Tabelle) für 3 x 3 und 3 x 4.

Rechenzeit rund zehn bis zwanzig Minuten (Knotenlimit 1 000 000 je Lauf; die volle Aufzählung und Branch and Bound ohne Untergrenze in 4 x 3, 5 x 3 und 4 x 4 sind
die teuren Läufe). Dieselben Funktionen wie die Tests (`ive_evaluation.cell_rows`, `cell_stats`, `gap_table`); die Datei speichert nur Kennzahlen, keine Zeilen.
tests/test_presets.py rechnet kleine Zellen neu und vergleicht."""

import json
import sys

import ive_constants as C
import ive_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def main():
    bands = {"tabelle": {}, "luecke": {}}
    for stacks, layers, n, full in C.TABLE_CELLS:
        rows = ev.cell_rows(stacks, layers, C.DEFAULT_EXTRA, range(n), full)
        bands["tabelle"][ev.cell_key(stacks, layers)] = ev.cell_stats(rows, full)
        if (stacks, layers) in C.GAP_CELLS:
            bands["luecke"][ev.cell_key(stacks, layers)] = ev.gap_table(rows)
        print(f"{stacks} Stapel x {layers} Lagen ({n} Buchten): fertig", flush=True)
    ev.BANDS_FILE.write_text(json.dumps(bands, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("geschrieben:", ev.BANDS_FILE.name)


if __name__ == "__main__":
    main()
