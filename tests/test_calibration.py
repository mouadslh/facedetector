"""Tests du module calibration.py (sans webcam)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard import config
from drowsiguard.calibration import CalibrationEngine, CalibrationState, _trimmed_median


# ---------------------------------------------------------------------------
# Tests utilitaire _trimmed_median
# ---------------------------------------------------------------------------


class TestTrimmedMedian:
    def test_empty_list(self):
        assert _trimmed_median([], 0.10) == 0.0

    def test_no_trim(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _trimmed_median(values, 0.0)
        assert result == pytest.approx(3.0)

    def test_outliers_removed(self):
        """Les valeurs aberrantes aux extrêmes doivent être ignorées."""
        # 100 valeurs normales + 2 valeurs extrêmes
        values = [0.30] * 50 + [0.31] * 50 + [0.01, 5.0]
        result = _trimmed_median(values, 0.05)
        # Doit être proche de 0.30/0.31, pas de 0.01 ou 5.0
        assert 0.28 <= result <= 0.33

    def test_single_value(self):
        assert _trimmed_median([0.42], 0.10) == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# Simulation d'une séquence de calibration complète
# ---------------------------------------------------------------------------


def _run_calibration(
    n_open: int = 120,
    n_closed: int = 60,
    n_yawn: int = 90,
    ear_open: float = 0.32,
    ear_closed: float = 0.10,
    mar_rest: float = 0.20,
    mar_yawn: float = 0.60,
    include_blink: bool = False,
) -> CalibrationEngine:
    """
    Simule une séquence complète de calibration avec des données synthétiques.

    Returns
    -------
    CalibrationEngine
        Moteur après la séquence.
    """
    engine = CalibrationEngine()
    ts = 0.0
    dt = 1.0 / 30.0  # 30 FPS simulés

    # Phase WAITING_FACE : envoyer d'abord quelques frames sans visage
    for _ in range(5):
        engine.update(ear=0.0, mar=0.0, pitch=0.0, face_ok=False, timestamp=ts)
        ts += dt

    # Attente stabilisation
    for _ in range(int(config.CALIB_STABILIZE_S / dt) + 5):
        engine.update(ear=ear_open, mar=mar_rest, pitch=0.0, face_ok=True, timestamp=ts)
        ts += dt

    # Phase OPEN
    for i in range(n_open):
        ear = ear_closed if (include_blink and i == 30) else ear_open  # 1 clignement simulé
        engine.update(ear=ear, mar=mar_rest, pitch=0.0, face_ok=True, timestamp=ts)
        ts += dt

    # Phase CLOSED
    for _ in range(n_closed):
        engine.update(ear=ear_closed, mar=mar_rest, pitch=0.0, face_ok=True, timestamp=ts)
        ts += dt

    # Phase YAWN
    for _ in range(n_yawn):
        engine.update(ear=ear_open, mar=mar_yawn, pitch=0.0, face_ok=True, timestamp=ts)
        ts += dt

    return engine


class TestCalibrationSequence:
    def test_full_sequence_reaches_done(self):
        """Une séquence complète valide doit atteindre l'état DONE."""
        engine = _run_calibration()
        assert engine.state == CalibrationState.DONE

    def test_profile_values_coherent(self):
        """Le profil produit doit avoir ear_closed < ear_open."""
        engine = _run_calibration()
        assert engine.state == CalibrationState.DONE
        profile = engine.profile
        assert profile is not None
        assert profile.ear_closed < profile.ear_open
        assert profile.mar_yawn > profile.mar_rest

    def test_blink_ignored_in_open_phase(self):
        """Un clignement pendant la phase yeux ouverts ne doit pas fausser ear_open."""
        engine = _run_calibration(include_blink=True)
        assert engine.state == CalibrationState.DONE
        profile = engine.profile
        assert profile is not None
        # ear_open doit rester proche de 0.32 malgré le clignement
        assert profile.ear_open > 0.25

    def test_incoherent_profile_rejected(self):
        """Un profil incohérent (ear_closed ≈ ear_open) doit échouer."""
        engine = _run_calibration(ear_open=0.25, ear_closed=0.24)
        assert engine.state == CalibrationState.FAILED

    def test_reset_restarts_from_waiting(self):
        """reset() doit ramener l'état à WAITING_FACE."""
        engine = _run_calibration()
        assert engine.state == CalibrationState.DONE
        engine.reset()
        assert engine.state == CalibrationState.WAITING_FACE

    def test_face_loss_during_calibration(self):
        """La perte du visage pendant la calibration doit revenir à WAITING_FACE."""
        engine = CalibrationEngine()
        ts = 0.0
        dt = 1.0 / 30.0

        # Attente stabilisation → PHASE_OPEN
        for _ in range(int(config.CALIB_STABILIZE_S / dt) + 5):
            engine.update(ear=0.30, mar=0.20, pitch=0.0, face_ok=True, timestamp=ts)
            ts += dt

        assert engine.state == CalibrationState.PHASE_OPEN

        # Perte du visage
        engine.update(ear=0.0, mar=0.0, pitch=0.0, face_ok=False, timestamp=ts)
        assert engine.state == CalibrationState.WAITING_FACE
