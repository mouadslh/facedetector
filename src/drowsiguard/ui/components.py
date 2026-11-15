"""
Module ui.components — Composants visuels pour DrowsiGuard.

RÈGLE : Aucune logique métier ici. Ce module affiche uniquement les données
fournies en respectant la charte graphique 60 / 30 / 10.
"""

from __future__ import annotations

import streamlit as st

from drowsiguard.calibration import CalibrationStatus
from drowsiguard.quality import QualityResult
from drowsiguard.state import AlertLevel, StateResult
from drowsiguard.thresholds import Thresholds
from drowsiguard.ui.theme import COLOR_BORDER, COLOR_TEXT_MUTED, get_alert_color


# ---------------------------------------------------------------------------
# En-tête global
# ---------------------------------------------------------------------------


def render_header(status_label: str = "SURVEILLANCE ACTIVE", session_dur_s: float = 0.0) -> None:
    """Affiche le bandeau d'en-tête de l'application."""
    mins = int(session_dur_s) // 60
    secs = int(session_dur_s) % 60
    time_str = f"{mins:02d}:{secs:02d}"

    with st.container(border=True):
        status, duration = st.columns([3, 1])
        with status:
            st.markdown(f"**{status_label}**")
        with duration:
            st.metric("Durée", time_str)


# ---------------------------------------------------------------------------
# Badges de qualité caméra
# ---------------------------------------------------------------------------


def render_quality_badge(quality: QualityResult) -> None:
    """Affiche le bandeau d'état de la caméra en haut du flux."""
    if quality.ok:
        st.success(quality.message)
    elif quality.status in ("NO_FACE", "TOO_FAR"):
        st.warning(quality.message)
    else:
        st.error(quality.message)


# ---------------------------------------------------------------------------
# Écran de calibration
# ---------------------------------------------------------------------------


def render_calibration_screen(status: CalibrationStatus) -> None:
    """Affiche l'interface de calibration guidée avec grandes consignes et barre en accent cyan."""
    with st.container(border=True):
        st.caption("CALIBRATION AUTOMATIQUE")
        st.subheader("Mesure de vos paramètres personnels")
        st.info(status.message)
    st.progress(status.progress, text=f"Progression : {int(status.progress * 100)} %")


# ---------------------------------------------------------------------------
# Jauge circulaire de fatigue 0-100
# ---------------------------------------------------------------------------


def render_circular_gauge(score: float, level: AlertLevel) -> str:
    """Génère le code SVG d'une jauge circulaire 0-100 de 130px."""
    color = get_alert_color(level)
    radius = 50
    circumference = 2 * 3.14159 * radius
    clamped_score = max(0.0, min(100.0, score))
    offset = circumference * (1.0 - (clamped_score / 100.0))

    return f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
        <svg width="130" height="130" viewBox="0 0 120 120" style="transform: rotate(-90deg);">
            <!-- Cercle de fond -->
            <circle
                cx="60" cy="60" r="{radius}"
                fill="none"
                stroke="{COLOR_BORDER}"
                stroke-width="10"
            />
            <!-- Arc de progression -->
            <circle
                cx="60" cy="60" r="{radius}"
                fill="none"
                stroke="{color}"
                stroke-width="10"
                stroke-linecap="round"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{offset}"
                style="transition: stroke-dashoffset 200ms ease, stroke 200ms ease;"
            />
        </svg>
        <div style="
            margin-top: -85px;
            margin-bottom: 25px;
            display: flex;
            flex-direction: column;
            align-items: center;
        ">
            <span style="
                font-size: 2.1rem;
                font-weight: 800;
                color: {color};
                font-variant-numeric: tabular-nums;
                line-height: 1;
            ">
                {score:.0f}
            </span>
            <span style="font-size: 0.72rem; color: {COLOR_TEXT_MUTED}; font-weight: 600; text-transform: uppercase; margin-top: 2px;">
                Score / 100
            </span>
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Grand badge de niveau de fatigue
# ---------------------------------------------------------------------------


def render_fatigue_section(result: StateResult) -> None:
    """Affiche le niveau de fatigue avec les composants natifs Streamlit."""
    level = result.level
    reasons = " • ".join(result.reasons) if result.reasons else "Aucun signe de fatigue détecté"

    with st.container(border=True):
        st.caption("NIVEAU DE FATIGUE")
        if level == AlertLevel.DANGER:
            st.error("ALERTE : RÉVEILLEZ-VOUS !")
        elif level == AlertLevel.VIGILANCE:
            st.warning(level.value.upper())
        else:
            st.success(level.value.upper())
        st.write(reasons)
        score_col, progress_col = st.columns([1, 2])
        with score_col:
            st.metric("Score", f"{result.score:.0f}")
            st.caption("sur 100")
        with progress_col:
            st.caption("Indice de fatigue")
            st.progress(max(0.0, min(1.0, result.score / 100.0)))


# ---------------------------------------------------------------------------
# Cartes métriques temps réel avec Sparklines SVG
# ---------------------------------------------------------------------------


def _generate_sparkline(values: list[float], stroke_color: str, height: int = 24, width: int = 90) -> str:
    """Génère un sparkline SVG ultra-léger pour une série de valeurs."""
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'

    pts = values[-25:]
    min_v = min(pts)
    max_v = max(pts)
    delta = (max_v - min_v) if (max_v - min_v) > 1e-4 else 1.0

    n = len(pts)
    step_x = width / (n - 1)
    coords = []
    for i, v in enumerate(pts):
        x = i * step_x
        # Inversion Y (0 en haut)
        y = height - ((v - min_v) / delta * (height - 4) + 2)
        coords.append(f"{x:.1f},{y:.1f}")

    points_str = " ".join(coords)
    return f"""
    <svg width="{width}" height="{height}" style="display: block;">
        <polyline
            fill="none"
            stroke="{stroke_color}"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            points="{points_str}"
        />
    </svg>
    """


def render_metrics_cards(
    result: StateResult,
    ear: float,
    mar: float,
    pitch: float,
    ear_history: list[float],
    mar_history: list[float],
    perclos_history: list[float],
    thresholds: Thresholds | None = None,
) -> None:
    """Affiche les indicateurs temps réel sous forme de cartes Streamlit natives."""
    ear_ref = f"Seuil : {thresholds.ear_close:.2f}" if thresholds else "Réf : 0.20"
    mar_ref = f"Seuil : {thresholds.mar_yawn:.2f}" if thresholds else "Réf : 0.50"
    closed_s = result.closed_duration

    columns = st.columns(2)
    with columns[0].container(border=True):
        st.metric("EAR (yeux)", f"{ear:.3f}")
        st.caption(ear_ref)
    with columns[1].container(border=True):
        st.metric("MAR (bouche)", f"{mar:.3f}")
        st.caption(mar_ref)
    with columns[0].container(border=True):
        st.metric("PERCLOS (60 s)", f"{int(result.perclos * 100)} %")
        st.caption("Seuil alerte : 15 %")
    with columns[1].container(border=True):
        st.metric("Fermeture des yeux", f"{closed_s:.1f} s")
        st.caption("Alarme si > 1,5 s")
    with st.container(border=True):
        st.metric("Inclinaison de la tête", f"{pitch:+.1f}°", help="Valeur neutre : 0°")


# ---------------------------------------------------------------------------
# Compteurs de session
# ---------------------------------------------------------------------------


def render_counters_bar(result: StateResult, alert_count: int) -> None:
    """Affiche les compteurs de session avec les composants natifs Streamlit."""
    columns = st.columns(3)
    with columns[0].container(border=True):
        st.metric("Bâillements", result.yawn_count)
    with columns[1].container(border=True):
        st.metric("Micro-sommeils", result.microsleep_count)
    with columns[2].container(border=True):
        st.metric("Alertes Danger", alert_count)
