"""
Module ui.charts — Graphiques Plotly haute fidélité pour DrowsiGuard.

Style :
- Fond blanc
- Grille très discrète gris clair
- Courbes principales en bleu modéré
- Seuils de référence en pointillés #8FA3BF
- Zones de vigilance/danger teintées avec couleurs d'état à faible opacité
- Pas de barre d'outils Plotly (displayModeBar=False)
"""

from __future__ import annotations

import plotly.graph_objects as go

from drowsiguard.thresholds import Thresholds
from drowsiguard.ui.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_DOMINANT,
    COLOR_SECONDARY,
    COLOR_STATE_DANGER,
    COLOR_STATE_NORMAL,
    COLOR_STATE_VIGILANCE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
)


def _base_layout(title: str, y_title: str, y_range: list[float] | None = None) -> dict:
    """Génère la configuration commune aux 3 graphiques."""
    layout = dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(color=COLOR_TEXT_PRIMARY, size=13, family="Inter, sans-serif"),
            x=0.02,
            y=0.92,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=COLOR_TEXT_MUTED, size=10, family="Inter, sans-serif"),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLOR_BORDER,
            zeroline=False,
            showticklabels=False,  # Évite l'encombrement horizontal
            title=None,
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color=COLOR_TEXT_MUTED, size=11)),
            showgrid=True,
            gridcolor=COLOR_BORDER,
            zeroline=False,
            color=COLOR_TEXT_MUTED,
        ),
        margin=dict(l=40, r=16, t=36, b=24),
        height=120,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            font=dict(color=COLOR_TEXT_MUTED, size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    if y_range is not None:
        layout["yaxis"]["range"] = y_range
    return layout


# ---------------------------------------------------------------------------
# Graphique 1 : EAR + Seuil personnel
# ---------------------------------------------------------------------------


def ear_chart(
    ear_history: list[float],
    thresholds: Thresholds,
    max_points: int = 180,
) -> go.Figure:
    """Graphique de l'ouverture des yeux avec seuils de fermeture et somnolence."""
    data = ear_history[-max_points:] if ear_history else [0.25]
    x = list(range(len(data)))

    fig = go.Figure(layout=_base_layout("EAR — Ouverture des yeux", "EAR", y_range=[0.0, 0.45]))

    # Zone de danger (sous le seuil de fermeture)
    fig.add_hrect(
        y0=0.0,
        y1=thresholds.ear_close,
        fillcolor=COLOR_STATE_DANGER,
        opacity=0.12,
        line_width=0,
    )

    # Courbe EAR en cyan accent
    fig.add_trace(
        go.Scatter(
            x=x,
            y=data,
            mode="lines",
            name="EAR",
            line=dict(color=COLOR_ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(40, 120, 199, 0.10)",
        )
    )

    # Seuil de fermeture
    fig.add_hline(
        y=thresholds.ear_close,
        line=dict(color=COLOR_STATE_DANGER, dash="dash", width=1.4),
        annotation_text="Fermé",
        annotation_position="bottom right",
        annotation_font=dict(color=COLOR_STATE_DANGER, size=9),
    )

    # Seuil de somnolence légère
    fig.add_hline(
        y=thresholds.ear_drowsy,
        line=dict(color=COLOR_TEXT_MUTED, dash="dot", width=1.2),
        annotation_text="Seuil",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_TEXT_MUTED, size=9),
    )

    return fig


# ---------------------------------------------------------------------------
# Graphique 2 : MAR + Seuil bâillement
# ---------------------------------------------------------------------------


def mar_chart(
    mar_history: list[float],
    thresholds: Thresholds,
    max_points: int = 180,
) -> go.Figure:
    """Graphique de l'ouverture buccale avec seuil de détection du bâillement."""
    data = mar_history[-max_points:] if mar_history else [0.05]
    x = list(range(len(data)))

    fig = go.Figure(layout=_base_layout("MAR — Ouverture de la bouche", "MAR", y_range=[0.0, 1.0]))

    # Zone de bâillement (au-dessus du seuil)
    fig.add_hrect(
        y0=thresholds.mar_yawn,
        y1=1.0,
        fillcolor=COLOR_STATE_VIGILANCE,
        opacity=0.12,
        line_width=0,
    )

    # Courbe MAR en cyan accent
    fig.add_trace(
        go.Scatter(
            x=x,
            y=data,
            mode="lines",
            name="MAR",
            line=dict(color=COLOR_ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(40, 120, 199, 0.10)",
        )
    )

    # Seuil de bâillement
    fig.add_hline(
        y=thresholds.mar_yawn,
        line=dict(color=COLOR_STATE_VIGILANCE, dash="dash", width=1.4),
        annotation_text="Bâillement",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_STATE_VIGILANCE, size=9),
    )

    return fig


# ---------------------------------------------------------------------------
# Graphique 3 : PERCLOS + Score de fatigue (combiné)
# ---------------------------------------------------------------------------


def perclos_score_chart(
    perclos_history: list[float],
    score_history: list[float],
    max_points: int = 180,
) -> go.Figure:
    """Graphique combiné du PERCLOS (%) et du score de fatigue (0-100)."""
    p_data = [v * 100 for v in perclos_history[-max_points:]] if perclos_history else [0.0]
    s_data = score_history[-max_points:] if score_history else [0.0]
    x = list(range(max(len(p_data), len(s_data))))

    fig = go.Figure(layout=_base_layout("PERCLOS (%) & Score fatigue", "% / Score", y_range=[0.0, 100.0]))

    # Ligne de vigilance (score 40)
    fig.add_hline(
        y=40.0,
        line=dict(color=COLOR_STATE_VIGILANCE, dash="dot", width=1.0),
        annotation_text="Vigilance",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_STATE_VIGILANCE, size=9),
    )

    # Ligne de danger (score 70)
    fig.add_hline(
        y=70.0,
        line=dict(color=COLOR_STATE_DANGER, dash="dash", width=1.2),
        annotation_text="Danger",
        annotation_position="top right",
        annotation_font=dict(color=COLOR_STATE_DANGER, size=9),
    )

    # Courbe PERCLOS
    fig.add_trace(
        go.Scatter(
            x=x[:len(p_data)],
            y=p_data,
            mode="lines",
            name="PERCLOS %",
            line=dict(color=COLOR_TEXT_PRIMARY, width=1.8),
        )
    )

    # Courbe Score
    fig.add_trace(
        go.Scatter(
            x=x[:len(s_data)],
            y=s_data,
            mode="lines",
            name="Score fatigue",
            line=dict(color=COLOR_ACCENT, width=2.2),
            fill="tozeroy",
            fillcolor="rgba(40, 120, 199, 0.10)",
        )
    )

    return fig


# Configuration globale pour désactiver la barre Plotly
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}
