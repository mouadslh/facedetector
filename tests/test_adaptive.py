"""Tests du module adaptive.py (sans webcam)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard import config
from drowsiguard.adaptive import AdaptiveBaseline


EAR_OPEN_INIT = 0.32
EAR_CLOSE_THR = 0.20  # Seuil de fermeture


def _make_baseline() -> AdaptiveBaseline:
    return AdaptiveBaseline(
        ear_open_initial=EAR_OPEN_INIT,
        ear_close_threshold=EAR_CLOSE_THR,
        window_s=30.0,  # Fenêtre courte pour les tests
        percentile=90.0,
        max_speed=0.005,
        max_drift=0.20,
    )


class TestAdaptiveBaseline:
    def test_initial_value_unchanged(self):
        """Sans mise à jour, la valeur doit être la valeur initiale."""
        bl = _make_baseline()
        assert bl.ear_open == pytest.approx(EAR_OPEN_INIT)

    def test_follows_brightness_decrease(self):
        """
        Si l'EAR diminue progressivement (lumière qui baisse),
        l'estimation doit s'adapter vers le bas.
        """
        bl = _make_baseline()
        fps = 30.0
        dt = 1.0 / fps
        target_ear = 0.27  # Baisse de ~15 %
        ts = 0.0

        # Simuler 60 secondes de données à EAR réduit
        for _ in range(int(60 * fps)):
            bl.update(ear=target_ear, timestamp=ts)
            ts += dt

        # L'estimation doit s'approcher de la cible
        assert bl.ear_open < EAR_OPEN_INIT * 0.97, (
            f"L'adaptation vers le bas a échoué : {bl.ear_open:.4f} >= {EAR_OPEN_INIT * 0.97:.4f}"
        )

    def test_does_not_drift_during_eye_closure(self):
        """
        Pendant une fermeture prolongée (EAR < seuil), l'estimation
        ne doit PAS dériver vers le bas.
        """
        bl = _make_baseline()
        fps = 30.0
        dt = 1.0 / fps
        ts = 0.0

        # D'abord quelques secondes en éveil pour établir une baseline
        for _ in range(int(10 * fps)):
            bl.update(ear=EAR_OPEN_INIT, timestamp=ts)
            ts += dt

        ear_after_wake = bl.ear_open

        # Fermeture prolongée de 30 s (micro-sommeil simulé)
        for _ in range(int(30 * fps)):
            bl.update(ear=0.08, timestamp=ts)  # Yeux fermés
            ts += dt

        # L'estimation doit rester proche de la valeur en éveil
        assert abs(bl.ear_open - ear_after_wake) < 0.02, (
            f"Dérive pendant la fermeture : {bl.ear_open:.4f} vs {ear_after_wake:.4f}"
        )

    def test_max_drift_respected(self):
        """L'amplitude de dérive ne doit pas dépasser max_drift * ear_open_initial."""
        bl = _make_baseline()
        fps = 30.0
        dt = 1.0 / fps
        ts = 0.0

        # Forcer des valeurs EAR très basses mais au-dessus du seuil de fermeture
        for _ in range(int(300 * fps)):
            bl.update(ear=EAR_CLOSE_THR + 0.01, timestamp=ts)
            ts += dt

        max_drift_abs = EAR_OPEN_INIT * config.ADAPTIVE_MAX_DRIFT
        assert abs(bl.ear_open - EAR_OPEN_INIT) <= max_drift_abs + 0.01

    def test_reset_restores_initial(self):
        """reset() doit restaurer la valeur initiale."""
        bl = _make_baseline()
        fps = 30.0
        dt = 1.0 / fps
        ts = 0.0

        for _ in range(int(60 * fps)):
            bl.update(ear=0.27, timestamp=ts)
            ts += dt

        new_ear = 0.35
        bl.reset(new_ear, EAR_CLOSE_THR + 0.05)
        assert bl.ear_open == pytest.approx(new_ear)
