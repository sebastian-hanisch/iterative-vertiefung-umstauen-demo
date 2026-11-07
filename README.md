# Die Untergrenze macht die Suche klein: IDA* beim Umstauen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-iterative-vertiefung-umstauen-demo.streamlit.app/)** -->

Fünftes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. [Stück 2](https://sebastianhanisch-untergrenze-umstauen-demo.streamlit.app/) erklärt die Untergrenze (die Zahl der blockierenden Container), [Stück 4](https://sebastianhanisch-knotenexplosion-umstauen-demo.streamlit.app/) zeigt, wie die Suche über alle Hubfolgen explodiert. Dieses Stück **verbindet beide**: Wer schon *g* Hübe gebraucht hat und im aktuellen Zustand noch mindestens so viele braucht, wie Container blockieren, kann den Teilbaum abschneiden, sobald die Summe das Budget übersteigt. **IDA\*** (iterative Vertiefung) erhöht das Budget Stufe für Stufe. Die Demo **zählt die Knoten** von sechs Verfahren und fragt, woher der Gewinn kommt.

## Warum dieses Problem

Dass eine gute Schranke eine Suche klein macht, ist bekannt. Spannend ist die Frage, **welcher Teil** davon die Schranke ist und welcher das Verfahren drumherum. Hier lässt sich das sauber trennen: Dieselbe Untergrenze steckt in zwei Verfahren, in Branch and Bound mit Untergrenze und in IDA\*, dazu kommt das Verfahren aus Stück 4 ohne sie. Die Messung zeigt: Die **Untergrenze** bringt das Meiste, die **iterative Vertiefung** im Median höchstens das Dreifache (und manchmal weniger als Branch and Bound), und der Baum **wächst trotzdem exponentiell**.

## Modell

Eine Bucht aus *s* Stapeln mit Höchsthöhe *H* = Lagen + Platz (Platz 1 bis 4, Standard 2), anfangs jeder Stapel gleich hoch gefüllt, Abrufnummern 1 bis *N* zufällig verteilt (Familie wie in Stück 1 bis 4, gleiche festen Buchten). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; **restricted**: nur der Blocker über der nächsten abzurufenden Nummer wird bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt.

**Suchbaum** wie in Stück 4: Ein **Knoten** ist ein Aufruf der Suche (Bucht nach den kostenlosen Abrufen, mit den bisherigen Hüben *g*), die **Kinder** entstehen, indem der Blocker auf jeden anderen Stapel mit Platz gesetzt wird, ein **Blatt** ist eine leere Bucht. **Untergrenze eines Knotens:** die Zahl der Container, die im Zustand gerade über einem früher abzurufenden liegen; jeder muss noch mindestens einmal bewegt werden. Kein Zustandsmerken, kein Symmetriebruch: gleiche Zustände zählen mehrfach. Formal im Expander „📐 Mathematische Formulierung“.

## Methodik

- **Sechs Verfahren:** *volle Aufzählung* (`enum`), *Branch and Bound ohne Untergrenze* (`bb`, Stück 4: Abbruch bei *g* + 1 ≥ beste bisherige Lösung), *Branch and Bound mit Untergrenze* (`bblb`: Abbruch bei *g* + Untergrenze ≥ beste bisherige Lösung), *IDA\** (`ida`) in drei Reihenfolgen der Kinder (*index*, *tight* = engste Passung aus Stück 1, *anti* = Umkehrung von *tight*).
- **IDA\*:** Budget = Untergrenze der Wurzel; je Budget eine Tiefensuche, die einen Knoten bei *g* + Untergrenze > Budget abschneidet und am ersten Blatt endet; gibt es keins, wächst das Budget um 1. Die Knoten der Stufen werden addiert.
- **Knotenlimit:** Läufe über 500 000 Knoten (live) beziehungsweise 1 000 000 (vorberechnet) werden abgebrochen und als „über Limit“ gezählt; sie liefern kein Optimum und fehlen in den Medianen. Gezählt werden Knoten, keine Sekunden.
- **Abschnitte der App:** Ergebnis (sechs Verfahren an einer Bucht, live); IDA\* an der Mini-Bucht von Hand und das Gegenbeispiel aus Stück 1; die Budgetstufen der gewählten Bucht; Tabellen über neun Zellen (Untergrenze, Vertiefung, Reihenfolge); Knoten je Lücke; Mittelwert, Maximum und Läufe über dem Limit. Die Tabellen sind vorberechnet (`ive_bands.json`, erzeugt von `generate_precomputed.py`, rund zehn bis fünfzehn Minuten).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den festen Buchten 0 bis (Zahl der Buchten − 1) je Zelle bei Platz 2 (Python-Zufallsfolge, `random.shuffle`, **dieselben Buchten wie in Stück 4**), nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_iterative_vertiefung_umstauen.py`. Zahlen: Median / Mittel / Maximum der fertigen Läufe, „über Limit“ = Läufe über 1 000 000 Knoten.

| Zelle (Buchten) | volle Aufzählung | B&B ohne Untergrenze (Stück 4) | B&B mit Untergrenze | IDA\*, engste Passung |
|---|---|---|---|---|
| 3 × 2 (100) | 9 / 20 / 161 | 5 / 6 / 27 | 5 / 5 / 17 | 3 / 4 / 15 |
| 4 × 2 (100) | 67 / 713 / 20 867 | 7 / 16 / 117 | 7 / 8 / 16 | 3 / 4 / 10 |
| 3 × 3 (100) | 230 / 1 403 / 13 427 | 33 / 68 / 419 | 13 / 20 / 114 | 16 / 25 / 144 |
| 5 × 2 (60) | 1 721 / 25 019 / 654 257, 1 über Limit | 25 / 80 / 1 268 | 13 / 13 / 25 | 4 / 6 / 12 |
| 4 × 3 (40) | 3 611,5 / 108 841 / 612 886, **10 über Limit** | 120 / 1 221 / 15 455 | 16 / 34 / 306 | 12 / 33 / 360 |
| 3 × 4 (40) | 18 163,5 / 82 533 / 696 375 | 384 / 625 / 3 665 | 51 / 79 / 379 | 65 / 121 / 672 |
| 5 × 3 (20) | 12 693 / 212 067 / 800 161, **15 über Limit** | 1 361 / 32 211 / 253 266 | 31 / 43 / 206 | 18,5 / 33 / 218 |
| 4 × 4 (30) | 251 062,5 / 251 062 / 358 087, **28 über Limit** | 17 804 / 91 461 / 755 046, 1 über Limit | 286 / 1 088 / 9 711 | 291 / 1 106 / 11 739 |
| 5 × 4 (20) | nicht gerechnet | nicht gerechnet | 513 / 44 470 / 468 662 | 521,5 / 50 391 / 487 765 |

| Zelle | B&B ohne UG / IDA\* (Median, Maximum) | B&B mit UG / IDA\* (Median, Maximum) | IDA\* Nummern / engste (Median) | IDA\* schlechteste / engste (Median, Maximum) | Budgetstufen (Mittel, Maximum) |
|---|---|---|---|---|---|
| 3 × 2 | 1,50 (2,2) | 1,13 (1,8) | 1,00 | 1,17 (2,2) | 1,33, 2 |
| 4 × 2 | 2,33 (12) | 2,00 (2,6) | 1,25 | 1,67 (3,0) | 1,30, 2 |
| 3 × 3 | 2,25 (7,7) | 0,89 (1,8) | 1,14 | 1,39 (4,1) | 2,52, 5 |
| 5 × 2 | 6,25 (106) | 3,00 (3,5) | 1,25 | 2,00 (3,0) | 1,32, 2 |
| 4 × 3 | 9,90 (155) | 1,35 (2,8) | 1,28 | 2,02 (5,9) | 2,17, 5 |
| 3 × 4 | 5,25 (13) | 0,71 (2,5) | 1,13 | 1,55 (3,2) | 4,28, 8 |
| 5 × 3 | 183,79 (2740) | 1,79 (3,6) | 1,39 | 2,21 (9,4) | 2,00, 4 |
| 4 × 4 | 75,42 (1230) | 0,98 (2,8) | 1,10 | 1,84 (4,9) | 4,00, 8 |
| 5 × 4 | – | 0,97 (3,5) | – | – | 3,85, 8 |

Die Verhältnisse sind je Bucht gebildet, dann der Median über die Buchten, in denen **beide** Läufe fertig wurden (bei 4 × 4: 29 von 30, weil Branch and Bound ohne Untergrenze in einer Bucht aufgab). „UG“ = Untergrenze.

| Frage | Befund |
|---|---|
| **Was bringt die Untergrenze?** | Gegenüber Branch and Bound ohne Untergrenze (Stück 4) braucht IDA\* im Median das **1,5- bis 184-Fache weniger** Knoten: 1,5 bei 3 × 2, 2,3 / 2,25 bei 4 × 2 / 3 × 3, 5,3 bei 3 × 4, 6,3 bei 5 × 2, 9,9 bei 4 × 3, 75 bei 4 × 4, 184 bei 5 × 3 (20 Buchten). Einzelne Buchten: bis zum 2 740-Fachen (5 × 3) und 1 230-Fachen (4 × 4). Bei 4 × 4 gibt die volle Aufzählung in 28 von 30 Buchten bei einer Million Knoten auf, IDA\* nie. |
| **Ist die iterative Vertiefung der Gewinn?** | **Nein, nicht der große.** Branch and Bound mit Untergrenze braucht im Median das **0,71- bis 3,0-Fache** der Knoten von IDA\*: IDA\* ist bei kleiner Lücke besser (4 × 2: 2,00, 5 × 2: 3,00, 5 × 3: 1,79), Branch and Bound mit Untergrenze bei großer Lücke (3 × 3: 0,89, 3 × 4: 0,71, die 4 × 4 und 5 × 4 liegen bei 0,98 und 0,97). Grund: IDA\* zählt die Knoten der früheren Stufen mit, Branch and Bound nicht. Der Beitrag der Untergrenze (bis zum 184-Fachen) ist um Größenordnungen größer als der der Vertiefung (bis zum 3-Fachen). |
| **Wie viele Budgetstufen?** | **Genau Lücke + 1** (Lücke = Optimum − Untergrenze aus Stück 2) in allen 100 + 100 + 100 + 60 + 40 + 40 + 20 + 30 + 20 = 510 Buchten; das folgt aus der Zulässigkeit der Untergrenze (Beweis im Expander) und ist in jeder Bucht nachgerechnet. Mittel 1,3 bei 3 × 2, 4 × 2, 5 × 2, 2,2 bei 4 × 3, 2,5 bei 3 × 3, 4,3 bei 3 × 4, höchstens 8 Stufen. |
| **Wie wachsen die Knoten mit der Lücke?** (3 × 3, 100 Buchten) | Median bei Lücke 0 / 1 / 2 / 3 / 4 (19 / 31 / 33 / 13 / 4 Buchten): IDA\* 3 / 9 / 22 / 55 / 113, Branch and Bound mit Untergrenze 5 / 9 / 19 / 40 / 73. Verhältnisse aufeinanderfolgender Mediane: 3,0 / 2,4 / 2,5 / 2,1 (IDA\*) und 1,8 / 2,1 / 2,1 / 1,8 (Branch and Bound mit UG). Der Anteil der letzten Stufe an den Knoten fällt im Median von 100 % auf 8 %. |
| **Und bei 3 × 4?** (40 Buchten) | Lücke 1 bis 7 (5 / 10 / 7 / 10 / 4 / 3 / 1 Buchten): IDA\* 12 / 37 / 54 / 105,5 / 171 / 399 / 672, Branch and Bound mit UG 13 / 36 / 37 / 78,5 / 105,5 / 238 / 354. Nur bei Lücke 1 liegt IDA\* vorn (12 gegen 13), ab Lücke 2 Branch and Bound mit Untergrenze. Anteil der letzten Stufe 50 % bis 2 %. |
| **Was bringt die Reihenfolge der Kinder?** | Mit Untergrenze im Median noch weniger als in Stück 4: Stapelnummern gegen engste Passung das 1,00- bis 1,39-Fache, schlechteste gegen engste das 1,17- bis 2,21-Fache; einzelne Buchten bis zum 9,4-Fachen (5 × 3). Die früheren, gescheiterten Stufen kosten in jeder Reihenfolge gleich viele Knoten; nur die letzte unterscheidet sich. |
| **Wo wird es trotzdem knapp?** | Der Schwanz bleibt schwer: bei 5 × 4 (20 Buchten) liegt der Median bei **521,5** Knoten, das Mittel bei **50 391**, das Maximum bei **487 765** (Mittel 97-mal der Median); bei 4 × 4 Median 291, Mittel 1 106, Maximum 11 739. Kein IDA\*-Lauf und kein Lauf mit Untergrenze erreicht das Limit von einer Million Knoten. |
| **Die Mini-Bucht** | (1, 4), (5, 2), (6, 3), Höchsthöhe 4, Untergrenze 1, Optimum 2: IDA\* in der Reihenfolge der Stapelnummern **6 Knoten** (Budget 1: 3 Knoten, die beiden Kinder sind zu teuer; Budget 2: 3 Knoten, Blatt), schlechteste zuerst 7 (3 + 4). Aus Stück 4: volle Aufzählung 9 Knoten, Branch and Bound ohne Untergrenze 5: **In so kleinen Buchten spart die Untergrenze noch nichts.** |
| **Das Gegenbeispiel aus Stück 1** | (3, 6), (2, 4), (1, 5), Höchsthöhe 4, Untergrenze 3, Optimum 4: IDA\* mit engster Passung **15 Knoten** (Budget 3: 3, Budget 4: 12), Stapelnummern 17 (3 + 14), Branch and Bound mit Untergrenze 17; aus Stück 4: Branch and Bound ohne Untergrenze 27, volle Aufzählung 153. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (3 × 3, Bucht 12: volle Aufzählung 229, Branch and Bound ohne Untergrenze 29, mit Untergrenze und IDA\* 11, Optimum 5, Untergrenze 4, 2 Stufen), „Die Mini-Bucht“ (3 × 2, Bucht 223: IDA\* 6 Knoten), „Große Lücke“ (3 × 4, Bucht 8: Untergrenze 6, Optimum 11, sechs Stufen, 183 Knoten), „Wo Stück 4 aufgibt“ (4 × 4, Bucht 5: Branch and Bound ohne Untergrenze über 500 000 Knoten, IDA\* 2 516 Knoten, Optimum 15, Untergrenze 10, sechs Stufen; die Berechnung dauert einige Sekunden).

**Korrektur gegenüber dem Plan:** Der Plan schrieb, Branch and Bound mit Untergrenze braucht „ähnlich viele Knoten“ wie IDA\*. Die Zellen zeigen es genauer: Das Verhältnis liegt zwischen 0,71 und 3,0 und hängt von der Lücke ab (siehe oben). Der Satz „die Vertiefung ist nicht der Gewinn“ gilt, die Streuung ist aber nicht klein.

## Ehrliche Grenzen

- **Ohne Zustandsmerken und Symmetriebruch.** Gleiche Zustände zählen mehrfach, auch über die Budgetstufen hinweg. Mit ihnen schrumpft der Baum weiter; das ist Stück 6, hier ist es nicht gemessen.
- **Knoten statt Zeit.** IDA\* zählt die Knoten der früheren Stufen mit, die Untergrenze kostet pro Knoten Rechenzeit; Sekunden und Knoten je Sekunde sind nicht gemessen.
- **Eine einfache Untergrenze.** Die Zahl der Blocker ist die schwächste der naheliegenden Schranken; stärkere würden den Baum weiter schneiden, nicht gemessen.
- **Große Zellen mit wenigen Buchten:** 4 × 4 mit 30, 5 × 4 und 5 × 3 mit je 20 Buchten. Der Median bei 5 × 3 beruht auf 20 Buchten (das Maximum der Schrankenwirkung ist ein Einzelwert), bei 5 × 4 fehlt der Vergleich mit Stück 4.
- **Nur restricted, nur volle Buchten mit gleich hohen Stapeln, Platz 2 in den Tabellen.** Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich die Knotenzahlen.
- **Der Schwanz:** Median und Mittel liegen bei 5 × 4 um das 97-Fache auseinander; aus dem Median allein folgt keine Laufzeit.
- **Zahlen aus Zufallsbuchten:** feste Buchten aus der Zufallsfolge von Python (`random.shuffle`), keine Messung an einem echten Terminal oder Lager; die CI prüft die Zahlen unter Linux.
- **Die Literatur wurde nicht im Volltext gelesen.** IDA\* für das Relocation-Problem untersuchen Zhu, Qin, Lim und Zhang (IEEE Transactions on Automation Science and Engineering 9(4), 2012, S. 710–722; Fundstelle geprüft, nicht gelesen). Die Verfahren und die Zählung sind hier selbst gebaut.

## Verifikation

- **Kern:** Knoten, Stufen und Blätter jedes Verfahrens gegen Handzählung an zwei Mini-Buchten (Mini-Bucht 6 und 7, Gegenbeispiel 15 und 17); die Knoten der Stufen addieren sich zur Knotenzahl; das erste Blatt hat genau das Budget als Hubzahl; sortierte Bucht hat genau einen Knoten; das Knotenlimit stoppt genau beim Überschreiten (auch mitten in einer Stufe); die ausgeschriebenen Bäume haben so viele Knoten wie die Suche.
- **Orakel:** das Optimum jedes Verfahrens in jeder Reihenfolge gegen eine **Breitensuche** über alle Zustände (3 × 2, 4 × 2, 3 × 3); die **Zulässigkeit der Untergrenze an jedem Knoten** des Suchbaums gegen die wahren Restkosten (Breitensuche vom Knoten aus); die Knoten von Branch and Bound mit Untergrenze und die Stufen von IDA\* gegen eine **zweite, iterative Fassung** mit eigenem Stapel und eigener Zählung der Blocker; die Knoten **gescheiterter** Stufen gegen eine **memoisierte Zählung** über (Zustand, Hübe), unabhängig von der Reihenfolge.
- **Eigenschaften:** Zahl der Stufen = Lücke + 1 in jeder geprüften Bucht; Branch and Bound mit Untergrenze besucht nie mehr Knoten als ohne (bei gleicher Reihenfolge); gescheiterte Stufen kosten in jeder Reihenfolge gleich viele Knoten.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (neun Zellen, Lücke, Schwanz, Limit); kleine Zellen und die 3-×-3-Tabellen gegen eine frische Rechnung (`tests/test_presets.py`).
- **Verdikte:** reine Funktionen, jede Schwelle (Faktor 5 und 1,25 für die Untergrenze, 1,5 und 1 / 1,5 für die Vertiefung, Lücke + 1 in jeder Bucht) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, Stufentabelle, ausgeschriebener Baum, Tabellenzeilen, Permalink), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Reglerwirkung), Footer, Laufzeit-Importe.
- **Abbildungen:** Farben je Rolle des Containers und der Stufen, feste Achsen, logarithmische Achsen, fehlende Mediane übersprungen.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `ive_bands.json` (Tabelle, Lücke) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `ive_algorithm.py` | Kern: Tiefensuche mit Knotenzählung (volle Aufzählung, Branch and Bound mit und ohne Untergrenze, IDA\*), Baumtext von IDA\* |
| `ive_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `ive_constants.py` | Regler-Grenzen, Knotenlimits, Zellen, Farben, Sonderbuchten, Presets |
| `ive_evaluation.py` | Analyse einer Bucht, Stichproben, Lücke, Verdikte (reine Funktionen) |
| `ive_layout.py` | Fester Kopf (Stylesheet), Tabellen scrollen im eigenen Rahmen |
| `ive_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `ive_scenario.py` | Buchten (volle Buchten, Zufallsbuchten) |
| `ive_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Zustandsmerken, Symmetriebruch:** das nächste Stück der Reihe.
- **Eine stärkere Untergrenze als die Blockerzahl.**
- **Eine Zeitmessung:** nur Knotenzahlen, weil die Rechenzeit je Gerät schwankt.
- **Den Vergleich mit Stück 4 bei 5 × 4:** die volle Aufzählung und Branch and Bound ohne Untergrenze wären dort zu langsam.
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

114 Tests, rund eine Minute.

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
