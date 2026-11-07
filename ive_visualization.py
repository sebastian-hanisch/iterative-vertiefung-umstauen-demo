"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ive_algorithm as A
import ive_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = A.INF
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_nodes(rows):
    """Knoten je Verfahren als Balken (logarithmische Achse); Läufe am Knotenlimit sind rot und als „mehr als“ beschriftet. `rows`: Zeilen aus result_rows."""
    fig = go.Figure(go.Bar(
        x=[C.VARIANT_SHORT[r["variant"]] for r in rows], y=[r["nodes"] for r in rows],
        marker_color=[C.COLOR_CAPPED if r["capped"] else C.COLOR_VARIANT[r["variant"]] for r in rows],
        text=[r["nodes_text"] for r in rows], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{text} Knoten<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten (logarithmisch)", type="log")
    return _base(fig, height=320)


def build_stages(rows):
    """Knoten je Budgetstufe von IDA* als Balken; die letzte Stufe (Blatt gefunden) ist grün, die übrigen grau-blau, eine am Limit abgebrochene rot.
    `rows`: Zeilen aus stage_rows."""
    colors = [C.COLOR_TARGET if r["found"] else C.COLOR_CAPPED if r["result"] == "Limit erreicht" else C.COLOR_CELL for r in rows]
    fig = go.Figure(go.Bar(x=[str(r["budget"]) for r in rows], y=[r["nodes"] for r in rows], marker_color=colors,
                           text=[f"{r['nodes']:,}".replace(",", " ") for r in rows], textposition="outside", cliponaxis=False,
                           hovertemplate="Budget %{x}: %{y:,.0f} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="Budget (Hübe)", type="category")
    fig.update_yaxes(title_text="Knoten der Stufe", rangemode="tozero")
    return _base(fig, height=300)


def build_effects(cells):
    """Wirkung der Untergrenze, der Vertiefung und der Reihenfolge je Zelle (logarithmisch): Median der Verhältnisse Branch and Bound ohne Untergrenze / IDA*,
    Branch and Bound mit Untergrenze / IDA*, IDA* Stapelnummern / engste Passung und schlechteste / engste Passung. `cells`: {Zellname: cell_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("B&B ohne Untergrenze (Stück 4) / IDA*", "gain", C.COLOR_LINES[3]), ("B&B mit Untergrenze / IDA*", "deep", C.COLOR_LINES[2]),
                              ("IDA*: Stapelnummern / engste Passung", "order_index", C.COLOR_LINES[0]), ("IDA*: schlechteste / engste Passung", "order_anti", C.COLOR_VARIANT[("ida", "anti")])):
        have = [n for n in names if cells[n][key]["median"] is not None]
        fig.add_trace(go.Bar(x=have, y=[cells[n][key]["median"] for n in have], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:.2f}-fach<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Median des Verhältnisses (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_gap(tables):
    """Median der Knoten je Lücke (Optimum - Untergrenze), logarithmisch, je Zelle eine Linie für IDA* und eine für Branch and Bound mit Untergrenze.
    `tables`: {Zellname: gap_table}."""
    fig = go.Figure()
    idx = 0
    for name, table in tables.items():
        for key, label in (("ida", "IDA*"), ("bblb", "B&B mit Untergrenze")):
            gaps = [int(x) for x in sorted(table, key=int) if table[x][key]["median"] is not None]
            fig.add_trace(go.Scatter(x=gaps, y=[table[str(g)][key]["median"] for g in gaps], mode="lines+markers", name=f"{name}, {label}",
                                     line=dict(color=C.COLOR_LINES[idx % len(C.COLOR_LINES)], width=3, dash="solid" if key == "ida" else "dot"),
                                     hovertemplate="Lücke %{x}: Median %{y:,.0f} Knoten<extra>%{fullData.name}</extra>"))
            idx += 1
    fig.update_xaxes(title_text="Lücke (Optimum - Untergrenze)", dtick=1)
    fig.update_yaxes(title_text="Median der Knoten (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_tail(cells):
    """Median, Mittel und Maximum der Knoten von IDA* (engste Passung) je Zelle, logarithmisch: der schwere Schwanz. `cells`: {Zellname: cell_stats}."""
    names = [n for n in cells if cells[n]["variants"]["ida/tight"]["median"] is not None]
    fig = go.Figure()
    for label, key, color in (("Median", "median", C.COLOR_LINES[1]), ("Mittel", "mean", C.COLOR_LINES[2]), ("Maximum", "max", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=names, y=[cells[n]["variants"]["ida/tight"][key] for n in names], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:,.0f} Knoten<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten von IDA* (logarithmisch)", type="log")
    return _base(fig)
