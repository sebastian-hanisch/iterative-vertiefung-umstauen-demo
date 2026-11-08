"""Die Untergrenze macht die Suche klein: IDA* beim Umstauen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 5 der Reihe „Umstauen: Untergrenze und Suche“. Stück 4 zeigte die Knotenexplosion der Suche über alle Hubfolgen. Hier kommt die Untergrenze aus Stück 2 hinzu:
Wer schon g Hübe gebraucht hat und noch mindestens Untergrenze Hübe braucht, kann einen Teilbaum abschneiden, sobald die Summe das Budget übersteigt. IDA* erhöht das
Budget Stufe für Stufe. Die Demo zählt die Knoten für sechs Verfahren an einer Bucht (live, mit Knotenlimit) und zeigt vorberechnet, was die Untergrenze, die Vertiefung
und die Reihenfolge bringen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import ive_algorithm as A
import ive_constants as C
from ive_evaluation import (
    Settings,
    analyse,
    cell_key,
    factor_text,
    load_bands,
    num,
    num_f,
    ratio_text,
    result_rows,
    stage_rows,
    verdict_bay,
    verdict_deepening,
    verdict_gain,
    verdict_gap,
    verdict_over_limit,
    verdict_stages,
    verdict_tail,
)
from ive_layout import dunkles_design, kopf_css
from ive_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from ive_visualization import build_bay, build_effects, build_gap, build_nodes, build_stages, build_tail

st.set_page_config(page_title="Untergrenze und IDA* – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _mini():
    """Baum von IDA* an der Mini-Bucht (Stapelnummern) und das Gegenbeispiel aus Stück 1: Stufen von IDA* (engste Passung), Knoten aus Stück 4."""
    counter = C.COUNTER_BAY
    ida = A.search(counter, C.COUNTER_HEIGHT, "ida", "tight")
    return (A.ida_tree_lines(C.MINI_BAY, C.MINI_HEIGHT), A.search(C.MINI_BAY, C.MINI_HEIGHT, "ida", "index"), ida,
            A.search(counter, C.COUNTER_HEIGHT, "enum", "index"), A.search(counter, C.COUNTER_HEIGHT, "bb", "tight"),
            A.search(counter, C.COUNTER_HEIGHT, "bblb", "tight"))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ive_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧭 Die Untergrenze macht die Suche klein: IDA*")
st.markdown(
    """
Stück 4 hat gezeigt, dass die Suche über **alle Hubfolgen** explodiert. Hier kommt die **Untergrenze** aus Stück 2 dazu: Wer schon *g* Hübe gebraucht hat und im aktuellen Zustand noch **mindestens so viele Hübe braucht, wie Container blockieren**, kann den Teilbaum abschneiden, sobald die Summe das **Budget** übersteigt. **IDA\\*** (iterative Vertiefung) beginnt beim Budget der Untergrenze der Wurzel und erhöht es um 1, bis eine Lösung hineinpasst; die erste gefundene ist das Optimum. Die Demo **zählt die Knoten** von sechs Verfahren und fragt, **woher der Gewinn kommt**.

Weiter unten: die Abschnitte **🔬 Experiment** (IDA\\* an der Mini-Bucht von Hand, die Budgetstufen dieser Bucht, was die Untergrenze bringt, Knoten je Lücke, wo es trotzdem knapp wird), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das fünfte Stück der Reihe „Umstauen: Untergrenze und Suche“; Zustandsmerken und Symmetriebruch, die den Baum weiter verkleinern können, kommen im nächsten.
"""
)

with st.expander("So funktioniert IDA* mit Untergrenze", expanded=True):
    st.markdown(
        """
1. **Untergrenze eines Knotens:** die Zahl der Container, die im Zustand gerade über einem früher abzurufenden liegen (Stück 2). Jeder muss noch mindestens einmal bewegt werden.
2. **Abschneiden:** Hat ein Knoten schon *g* Hübe hinter sich, braucht jede Lösung darunter mindestens *g* + Untergrenze Hübe. Übersteigt das das **Budget**, wird der Teilbaum übergangen.
3. **IDA\\*:** Budget = Untergrenze der Wurzel; je Budget eine Tiefensuche mit diesem Abschneiden, die am ersten Blatt endet. Gibt es keins, wächst das Budget um 1. Das erste Blatt hat genau das Optimum als Hubzahl. Die Knoten der Stufen werden addiert.
4. **Zum Vergleich:** *Branch and Bound mit Untergrenze* schneidet bei *g* + Untergrenze ≥ beste bisher gefundene Lösung ab (ohne Budget); *Branch and Bound ohne Untergrenze* ist das Verfahren aus Stück 4 (schneidet bei *g* + 1 ≥ beste Lösung ab).
5. **Reihenfolge der Kinder:** *Stapelnummern*, *engste Passung zuerst* (Regel aus Stück 1) oder *schlechteste zuerst*.
6. **Nicht dabei:** kein Zustandsmerken, kein Symmetriebruch. Gleiche Zustände zählen mehrfach (Stück 6).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    layers = st.slider("Lagen je Stapel", *bounds("layers_slider"), key="layers_slider", help="So viele Container stehen anfangs auf jedem Stapel.")
    extra = st.slider("Platz (Lagen über der Anfangshöhe)", *bounds("extra_slider"), key="extra_slider",
                      help="Höchsthöhe = Lagen + Platz. Standard 2. Die vorberechneten Tabellen gelten für Platz 2.")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Plätze verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "layers_slider": int(layers), "extra_slider": int(extra), "seed_input": int(seed)})

settings = Settings(int(stacks), int(layers), int(extra), int(seed))
with st.spinner(f"Zähle die Knoten der sechs Verfahren (höchstens {num(C.LIVE_CAP)} je Verfahren) …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
rows = result_rows(a)
by_variant = {r["variant"]: r for r in rows}
m1, m2, m3, m4 = st.columns(4)
m1.metric("Branch and Bound ohne Untergrenze (Knoten)", by_variant[("bb", "tight")]["nodes_text"], help=f"Das Verfahren aus Stück 4, engste Passung zuerst; Läufe über {num(C.LIVE_CAP)} Knoten werden abgebrochen.")
m2.metric("IDA*, engste Passung (Knoten)", by_variant[("ida", "tight")]["nodes_text"], help="Summe über alle Budgetstufen.")
m3.metric("Optimum", "nicht bewiesen" if a.optimum is None else a.optimum,
          delta=f"Untergrenze {a.lower}" + ("" if a.gap is None else f", Lücke {a.gap}"), delta_color="off", help="Alle Verfahren, die fertig werden, liefern dasselbe Optimum.")
m4.metric("Bucht", f"{settings.stacks} × {settings.layers}", delta=f"{settings.stacks * settings.layers} Container, Platz {settings.extra}", delta_color="off")
st.plotly_chart(build_bay(a.bay, a.height, target=min(c for s in a.bay for c in s)), width="stretch", key="chart_bay")
st.caption("Rot: blockierende Container (liegen über einem früher abzurufenden), grün: der nächste Abruf, grau-blau: alle übrigen.")
table = ["| Verfahren | Knoten | Blätter | Optimum | Budgetstufen |", "|---|---|---|---|---|"]
for r in rows:
    table.append(f"| {r['name']} | {r['nodes_text']} | {num(r['leaves'])}{'+' if r['capped'] else ''} | {r['optimum']} | {'' if r['stages'] is None else r['stages']} |")
st.markdown("\n".join(table))
st.caption(f"Knoten: besuchte Aufrufe der Suche (bei IDA* die Summe über alle Budgetstufen); „mehr als“ heißt: am Limit von {num(C.LIVE_CAP)} abgebrochen (dann sind auch die Blätter nur die bis dahin besuchten).")
st.plotly_chart(build_nodes(rows), width="stretch", key="chart_nodes")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie macht die Untergrenze die Suche klein?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: IDA* an der Mini-Bucht ----------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: IDA* an der Mini-Bucht von Hand")
lines, mini, counter_ida, counter_enum, counter_bb, counter_bblb = _mini()
st.caption("3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3): nur die 4 blockiert (Untergrenze 1). Hier der Suchbaum von IDA* je Budgetstufe, "
           "Kinder in der Reihenfolge der Stapelnummern; ein Pfeil ist ein Hub.")
st.plotly_chart(build_bay(C.MINI_BAY, C.MINI_HEIGHT, target=1), width="stretch", key="chart_mini")
st.code("\n".join(lines), language=None)
st.success(f"{mini.nodes} Knoten in {len(mini.stages)} Budgetstufen ({' + '.join(str(s[1]) for s in mini.stages)}), Optimum {mini.optimum}: Bei Budget 1 sind beide Kinder schon "
           "zu teuer (die 4 blockiert nach dem Hub wieder), bei Budget 2 passt der erste Weg. In so kleinen Buchten spart die Untergrenze noch nichts (Stück 4: 9 Knoten für die volle Aufzählung, "
           "5 für Branch and Bound).")
cs = counter_ida.stages
st.markdown(f"**Das Gegenbeispiel aus Stück 1** ((3, 6), (2, 4), (1, 5), Höchsthöhe 4): IDA\\* mit engster Passung braucht **{counter_ida.nodes} Knoten** "
            f"({' + '.join(str(s[1]) for s in cs)} in den Budgetstufen {', '.join(str(s[0]) for s in cs)}), Branch and Bound mit Untergrenze {counter_bblb.nodes}, "
            f"Branch and Bound ohne Untergrenze (Stück 4) {counter_bb.nodes} und die volle Aufzählung {counter_enum.nodes}.")

st.markdown("---")

# --- Experiment: Budgetstufen dieser Bucht -------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Die Budgetstufen dieser Bucht")
srows = stage_rows(a)
st.caption("IDA* mit engster Passung zuerst an der Bucht der Seitenleiste. Das Budget beginnt bei der Untergrenze und wächst um 1; die Stufen davor haben kein Blatt, die letzte hat das Optimum.")
stable = ["| Budget | Knoten | Ergebnis |", "|---|---|---|"]
for r in srows:
    stable.append(f"| {r['budget']} | {num(r['nodes'])} | {r['result']} |")
st.markdown("\n".join(stable))
st.plotly_chart(build_stages(srows), width="stretch", key="chart_stages")
if a.gap is not None and not a.res(("ida", "tight")).capped:
    st.info(f"Untergrenze {a.lower}, Optimum {a.optimum}, Lücke {a.gap}: IDA* braucht {len(srows)} Budgetstufen, also Lücke + 1. Das gilt in jeder Bucht (siehe die mathematische Formulierung unten): "
            "Jede Stufe unterhalb des Optimums scheitert, die Stufe des Optimums gelingt.")
else:
    st.warning("IDA* mit engster Passung hat das Knotenlimit erreicht: Die letzte Stufe ist unvollständig.")

st.markdown("---")

# --- Experiment: Was bringt die Untergrenze? -----------------------------------------------------------------------------------------------------

bands = _bands()
tab = bands["tabelle"]
st.subheader("🔬 Experiment: Was bringen Untergrenze, Vertiefung und Reihenfolge?")
st.caption(f"Je Zelle feste Buchten (Platz 2, dieselben wie in Stück 4), Knotenlimit {num(C.BAND_CAP)} je Lauf; vorberechnet (`generate_precomputed.py`). Median / Mittel / Maximum der fertigen Läufe; "
           "„über Limit“ = abgebrochene Läufe, die im Median fehlen (der Median ist dann nur eine Untergrenze).")


def _cell(st_, key):
    v = st_["variants"].get(key)
    if v is None:
        return "nicht gerechnet"
    if v["median"] is None:
        return f"alle {v['over']} über Limit"
    over = f", {v['over']} über Limit" if v["over"] else ""
    return f"{num_f(v['median'])} / {num(round(v['mean']))} / {num(v['max'])}{over}"


header = "| Zelle (Buchten) | volle Aufzählung | B&B ohne Untergrenze (Stück 4) | B&B mit Untergrenze | IDA*, engste Passung |"
lines_t = [header, "|---|---|---|---|---|"]
for s_, l_, n_, _full in C.TABLE_CELLS:
    c = tab[cell_key(s_, l_)]
    lines_t.append(f"| {s_} × {l_} ({c['n']}) | {_cell(c, 'enum/index')} | {_cell(c, 'bb/tight')} | {_cell(c, 'bblb/tight')} | {_cell(c, 'ida/tight')} |")
st.markdown("\n".join(lines_t))
st.caption("Knoten je Bucht: Median / Mittel / Maximum.")


def _ratio(st_, key, with_max=True):
    r = st_[key]
    if r["median"] is None:
        return "–"
    return f"{ratio_text(r['median'])}" + (f" ({factor_text(r['max'])})" if with_max else "")


header2 = "| Zelle | B&B ohne UG / IDA* (Median, Maximum) | B&B mit UG / IDA* (Median, Maximum) | IDA* Nummern / engste (Median) | IDA* schlechteste / engste (Median, Maximum) | Budgetstufen (Mittel, Maximum) |"
lines_r = [header2, "|---|---|---|---|---|---|"]
for s_, l_, _n, _full in C.TABLE_CELLS:
    c = tab[cell_key(s_, l_)]
    lines_r.append(f"| {s_} × {l_} | {_ratio(c, 'gain')} | {_ratio(c, 'deep')} | {_ratio(c, 'order_index', False)} | {_ratio(c, 'order_anti')} | "
                   f"{ratio_text(c['stages']['mean'])}, {c['stages']['max']} |")
st.markdown("\n".join(lines_r))
st.caption("Verhältnisse je Bucht, dann der Median über die Buchten, in denen beide Läufe fertig wurden. „UG“ = Untergrenze.")
cells = {f"{s_} × {l_}": tab[cell_key(s_, l_)] for s_, l_, _n, _f in C.TABLE_CELLS}
st.plotly_chart(build_effects(cells), width="stretch", key="chart_effects")
here = tab[cell_key(settings.stacks, settings.layers)]        # jede Kombination der Regler Stapel und Lagen hat eine Zelle
st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung)**" + ("" if settings.extra == C.DEFAULT_EXTRA else f", Tabellen gelten für Platz {C.DEFAULT_EXTRA}, hier ist Platz {settings.extra} eingestellt") + ":")
for verdict in (verdict_gain, verdict_deepening, verdict_stages):
    kind, text = verdict(here)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Knoten je Lücke -----------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie wachsen die Knoten mit der Lücke?")
gap = bands["luecke"]
st.caption("Die Lücke ist Optimum minus Untergrenze (Stück 2); sie bestimmt, wie oft das Budget wächst. Median der Knoten je Lücke aus den Buchten der Tabelle: durchgezogen IDA*, gepunktet Branch and Bound mit Untergrenze.")
st.plotly_chart(build_gap({k.replace(",", " × "): v for k, v in gap.items()}), width="stretch", key="chart_gap")
for k, v in gap.items():
    kind, text = verdict_gap(v, k.replace(",", " × "))
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Wo wird es knapp? ---------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wo wird es trotzdem knapp?")
st.caption(f"Median, Mittel und Maximum der Knoten von IDA* je Zelle (dieselben Buchten wie in der Tabelle, Limit {num(C.BAND_CAP)} Knoten). Das Limit zählt Knoten, nicht Sekunden.")
st.plotly_chart(build_tail(cells), width="stretch", key="chart_tail")
for key in ("4,4", "5,4"):
    kind, text = verdict_tail(tab[key], key.replace(",", " × "))
    getattr(st, kind)(text)
kind, text = verdict_over_limit(tab["4,4"])
getattr(st, kind)("4 × 4: " + text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ohne Zustandsmerken und Symmetriebruch** | Gleiche Zustände zählen mehrfach, auch über die Budgetstufen hinweg. Mit ihnen kann der Baum weiter schrumpfen; im Median bringt das bei IDA\\* kaum etwas, im Schwanz bis zum 45-Fachen (Stück 6, hier nicht gemessen). | das nächste Stück der Reihe |
| **Knoten statt Zeit** | IDA\\* zählt die Knoten der früheren Stufen mit, die Untergrenze kostet pro Knoten Rechenzeit; Sekunden und Knoten je Sekunde sind nicht gemessen. | – |
| **Eine einfache Untergrenze** | Die Zahl der Blocker ist eine einfache Schranke. Stärkere sind nicht untersucht. | – |
| **Große Zellen mit wenigen Buchten** | 4 × 4 mit 30, 5 × 4 mit 20 Buchten: die Mediane dort sind grob. In 5 × 4 fehlt der Vergleich mit Stück 4 (nicht gerechnet). | – |
| **Nur restricted, nur volle Buchten, Platz 2 in den Tabellen** | Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich die Knotenzahlen. | – |
| **Zahlen aus Zufallsbuchten** | Größenordnungen aus festen Buchten, keine Messung an einem echten Terminal oder Lager. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** eine Bucht aus $s$ Stapeln der Höchsthöhe $H$, die Container tragen die Abrufnummern $1, \dots, N$ (kleiner = früher). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; im *restricted* Modell werden nur Container über der nächsten abzurufenden Nummer bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt. Der Suchbaum und die Zählung der **Knoten** (besuchte Aufrufe der Suche, gleiche Buchten zählen mehrfach) sind die aus Stück 4.

**Untergrenze eines Knotens.** Sei $\ell(B)$ die Zahl der Container in $B$, die über einem früher abzurufenden Container im selben Stapel liegen. Jeder von ihnen muss vor dem darunterliegenden bewegt werden, jeder Hub bewegt einen Container: Von $B$ aus braucht jede Lösung mindestens $\ell(B)$ weitere Hübe. Das gilt in **jedem** Zustand, nicht nur an der Wurzel (Satz 1 aus Stück 2, angewendet auf den Zustand).

**Abschneiden.** Ein Knoten mit $g$ bisherigen Hüben und Zustand $B$ kann nur zu einer Lösung mit mindestens $g + \ell(B)$ Hüben führen. *Branch and Bound mit Untergrenze:* Ist $g + \ell(B) \ge b$ für die beste bisher gefundene Lösung $b$, kann darunter nichts Besseres liegen. *Stück 4:* dasselbe mit $\ell(B)$ durch $1$ ersetzt; an einem Knoten, der kein Blatt ist, gilt $\ell(B) \ge 1$ (die nächste Nummer liegt nicht oben, also blockiert etwas). **Folge:** bei gleicher Reihenfolge der Kinder besucht Branch and Bound mit Untergrenze nie mehr Knoten als ohne: Die beste bisher gefundene Lösung ist an jeder Stelle dieselbe, der zusätzlich abgeschnittene Teilbaum enthält kein besseres Blatt.

**IDA\*.** Setze $b_0 = \ell(\text{Wurzel})$. Für $b = b_0, b_0 + 1, \dots$: Tiefensuche, die einen Knoten abschneidet, wenn $g + \ell(B) > b$, und am ersten Blatt endet. Mit $\mathrm{OPT}$ als der kleinsten Hubzahl eines Blatts gilt: Für $b < \mathrm{OPT}$ gibt es kein Blatt mit höchstens $b$ Hüben, und abgeschnitten wird nur, was kein solches Blatt enthält; die Stufe scheitert. Für $b = \mathrm{OPT}$ gibt es eines, und die Suche findet es, denn der Weg dorthin wird nie abgeschnitten. Das gefundene Blatt hat $g \le b = \mathrm{OPT}$ Hübe, und weniger als $\mathrm{OPT}$ geht nicht, also $g = \mathrm{OPT}$. **Die Zahl der Stufen ist damit genau $\mathrm{OPT} - b_0 + 1$**, die Lücke aus Stück 2 plus 1. Die Zahl der Knoten ist die Summe über die Stufen.

**Reihenfolge der Kinder.** *Stapelnummern*, *engste Passung zuerst* (unter den Stapeln, auf denen $c$ nichts blockiert, der mit dem kleinsten frühesten Abruf; leerer Stapel zuletzt unter ihnen; danach die übrigen nach größtem frühesten Abruf) oder *schlechteste zuerst* (Umkehrung). Bei IDA\* ändert sie nur, wo in der letzten Stufe das erste Blatt liegt; die früheren Stufen scheitern in jeder Reihenfolge mit gleich vielen Knoten.

**Literatur.** Das Problem heißt in der Literatur Block Relocation Problem (auch Container Relocation Problem). IDA\* für das Problem untersuchen Zhu, Qin, Lim und Zhang, IEEE Transactions on Automation Science and Engineering 9(4), 2012, S. 710–722 (Fundstelle geprüft, Volltext nicht gelesen); eine Klassifikation verwandter Stapelprobleme geben Lehnfeld und Knust, European Journal of Operational Research 239(2), 2014, S. 297–312 (Fundstelle geprüft, Volltext nicht gelesen). Die Untergrenze aus Stück 2, die Zählung der Knoten und die sechs Verfahren sind hier selbst gebaut; Aussagen über die Literatur gehen nicht über die Fundstelle hinaus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
