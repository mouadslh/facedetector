"""Tests du module state.py (sans webcam)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard import config
from drowsiguard.profile import UserProfile
from drowsiguard.state import AlertLevel, DrowsinessState
from drowsiguard.thresholds import derive_thresholds


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


PROFILE = UserProfile(
    ear_open=0.32,
    ear_closed=0.10,
    mar_rest=0.20,
    mar_yawn=0.65,
    pitch_neutral=0.0,
)


def _make_state() -> DrowsinessState:
    thr = derive_thresholds(PROFILE, "Normale")
    return DrowsinessState(thr)


def _run_frames(
    state: DrowsinessState,
    ear: float,
    mar: float,
    pitch: float,
    duration_s: float,
    fps: float = 30.0,
    start_ts: float = 0.0,
) -> "StateResult":
    """Simule des frames pendant une durée donnée."""
    dt = 1.0 / fps
    n = int(duration_s * fps)
    result = None
    ts = start_ts
    for _ in range(n):
        result = state.update(ear=ear, mar=mar, pitch=pitch, timestamp=ts)
        ts += dt
    return result  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Tests de fermeture des yeux
# ---------------------------------------------------------------------------


class TestEyesClosed:
    def test_short_blink_no_alert(self):
        """Un clignement court (< MICROSLEEP_DURATION_S) ne doit pas déclencher d'alerte."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        # Yeux ouverts d'abord
        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=2.0)

        # Clignement de 0.2 s
        result = _run_frames(state, ear=thr.ear_close - 0.01, mar=0.20, pitch=0.0, duration_s=0.2, start_ts=2.0)
        assert result.level == AlertLevel.NORMAL
        assert result.microsleep_count == 0

    def test_long_closure_triggers_danger(self):
        """Une fermeture > DANGER_DURATION_S doit déclencher le niveau Danger."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        # Yeux ouverts d'abord (initialise l'état)
        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=3.0)

        # Yeux fermés pendant 3 s
        result = _run_frames(
            state, ear=thr.ear_close - 0.05, mar=0.20, pitch=0.0,
            duration_s=config.DANGER_DURATION_S + 0.5, start_ts=3.0
        )
        assert result.level == AlertLevel.DANGER

    def test_microsleep_counted(self):
        """Un micro-sommeil (> MICROSLEEP_DURATION_S) doit être compté une seule fois."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=2.0)
        _run_frames(
            state, ear=thr.ear_close - 0.05, mar=0.20, pitch=0.0,
            duration_s=config.MICROSLEEP_DURATION_S + 0.5, start_ts=2.0
        )
        result = _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=0.1, start_ts=5.0)
        assert result.microsleep_count == 1


# ---------------------------------------------------------------------------
# Tests PERCLOS
# ---------------------------------------------------------------------------


class TestPerclos:
    def test_perclos_zero_when_eyes_open(self):
        """PERCLOS = 0 quand les yeux sont toujours ouverts."""
        state = _make_state()
        result = _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=5.0)
        assert result.perclos == pytest.approx(0.0)

    def test_perclos_one_when_eyes_closed(self):
        """PERCLOS ≈ 1 quand les yeux sont toujours fermés."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)
        result = _run_frames(state, ear=thr.ear_close - 0.05, mar=0.20, pitch=0.0, duration_s=5.0)
        assert result.perclos > 0.90

    def test_perclos_half(self):
        """PERCLOS ≈ 0.5 quand les yeux sont fermés la moitié du temps."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)
        fps = 30.0
        dt = 1.0 / fps
        ts = 0.0

        for i in range(300):
            ear = thr.ear_close - 0.05 if i % 2 == 0 else PROFILE.ear_open
            state.update(ear=ear, mar=0.20, pitch=0.0, timestamp=ts)
            ts += dt

        result = state.update(ear=PROFILE.ear_open, mar=0.20, pitch=0.0, timestamp=ts)
        assert 0.40 <= result.perclos <= 0.60


# ---------------------------------------------------------------------------
# Tests bâillements
# ---------------------------------------------------------------------------


class TestYawns:
    def test_yawn_counted_once(self):
        """Un bâillement doit être compté une seule fois même s'il dure plusieurs secondes."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=1.0)
        # Bâillement de 1.5 s
        _run_frames(state, ear=PROFILE.ear_open, mar=thr.mar_yawn + 0.05, pitch=0.0, duration_s=1.5, start_ts=1.0)
        # Fermeture du bâillement
        result = _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=0.5, start_ts=2.5)

        assert result.yawn_count == 1

    def test_yawn_not_counted_if_too_short(self):
        """Un bâillement trop court (< YAWN_MIN_DURATION_S) ne doit pas être compté."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=1.0)
        yawn_short_dur = config.YAWN_MIN_DURATION_S * 0.3
        _run_frames(
            state, ear=PROFILE.ear_open, mar=thr.mar_yawn + 0.05, pitch=0.0,
            duration_s=yawn_short_dur, start_ts=1.0
        )
        result = _run_frames(
            state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0,
            duration_s=0.5, start_ts=1.0 + yawn_short_dur
        )

        assert result.yawn_count == 0

    def test_cooldown_prevents_double_count(self):
        """Deux bâillements trop rapprochés (< cooldown) ne doivent compter que pour 1."""
        state = _make_state()
        thr = derive_thresholds(PROFILE)

        ts = 0.0
        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=1.0)
        ts = 1.0
        # 1er bâillement
        _run_frames(state, ear=PROFILE.ear_open, mar=thr.mar_yawn + 0.05, pitch=0.0,
                    duration_s=1.0, start_ts=ts)
        ts += 1.0
        _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=0.2, start_ts=ts)
        ts += 0.2
        # 2e bâillement immédiat (dans le cooldown)
        _run_frames(state, ear=PROFILE.ear_open, mar=thr.mar_yawn + 0.05, pitch=0.0,
                    duration_s=1.0, start_ts=ts)
        ts += 1.0
        result = _run_frames(state, ear=PROFILE.ear_open, mar=0.20, pitch=0.0, duration_s=0.2, start_ts=ts)

        assert result.yawn_count == 1
