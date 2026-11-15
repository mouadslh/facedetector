"""
Tests unitaires pour les modules d'interface utilisateur (theme, charts, components).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.state import AlertLevel, StateResult
from drowsiguard.thresholds import Thresholds
from drowsiguard.ui.charts import ear_chart, mar_chart, perclos_score_chart
from drowsiguard.ui.components import _generate_sparkline, render_circular_gauge
from drowsiguard.ui.theme import (
    COLOR_ACCENT,
    COLOR_DOMINANT,
    COLOR_SECONDARY,
    COLOR_STATE_DANGER,
    COLOR_STATE_NORMAL,
    COLOR_STATE_VIGILANCE,
    get_alert_color,
)


def test_theme_colors():
    assert COLOR_DOMINANT == "#F5F7FA"
    assert COLOR_SECONDARY == "#FFFFFF"
    assert COLOR_ACCENT == "#2878C7"
    assert get_alert_color(AlertLevel.NORMAL) == COLOR_STATE_NORMAL
    assert get_alert_color(AlertLevel.VIGILANCE) == COLOR_STATE_VIGILANCE
    assert get_alert_color(AlertLevel.DANGER) == COLOR_STATE_DANGER


def test_charts_generation():
    thr = Thresholds(
        ear_close=0.20,
        ear_drowsy=0.25,
        ear_open_ref=0.35,
        mar_yawn=0.55,
        mar_rest_ref=0.15,
        pitch_forward=15.0,
        pitch_backward=-10.0,
        pitch_neutral_ref=0.0,
    )
    ear_hist = [0.35, 0.34, 0.32, 0.30, 0.28]
    mar_hist = [0.10, 0.12, 0.15, 0.20, 0.58]
    perclos_hist = [0.02, 0.04, 0.08, 0.12]
    score_hist = [10.0, 15.0, 25.0, 65.0]

    fig_ear = ear_chart(ear_hist, thr)
    assert fig_ear is not None
    assert len(fig_ear.data) >= 1

    fig_mar = mar_chart(mar_hist, thr)
    assert fig_mar is not None
    assert len(fig_mar.data) >= 1

    fig_ps = perclos_score_chart(perclos_hist, score_hist)
    assert fig_ps is not None
    assert len(fig_ps.data) == 2


def test_sparkline_and_gauge():
    spark = _generate_sparkline([0.1, 0.2, 0.3, 0.25], "#22D3EE")
    assert "<svg" in spark
    assert "polyline" in spark

    gauge = render_circular_gauge(45.0, AlertLevel.NORMAL)
    assert "<svg" in gauge
    assert "45" in gauge
