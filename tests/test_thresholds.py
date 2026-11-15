"""Tests du module thresholds.py (sans webcam)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.profile import UserProfile
from drowsiguard.thresholds import derive_thresholds


def _make_profile(ear_open: float, ear_closed: float, mar_rest: float, mar_yawn: float) -> UserProfile:
    return UserProfile(
        ear_open=ear_open,
        ear_closed=ear_closed,
        mar_rest=mar_rest,
        mar_yawn=mar_yawn,
        pitch_neutral=0.0,
    )


# Profil "grands yeux" : EAR_open élevé
PROFILE_LARGE = _make_profile(ear_open=0.38, ear_closed=0.12, mar_rest=0.20, mar_yawn=0.65)
# Profil "petits yeux" : EAR_open faible
PROFILE_SMALL = _make_profile(ear_open=0.22, ear_closed=0.06, mar_rest=0.18, mar_yawn=0.50)


class TestDeriveThresholds:
    def test_two_profiles_give_different_thresholds(self):
        """Deux profils différents doivent donner des seuils différents."""
        thr_large = derive_thresholds(PROFILE_LARGE)
        thr_small = derive_thresholds(PROFILE_SMALL)
        assert thr_large.ear_close != thr_small.ear_close
        assert thr_large.mar_yawn != thr_small.mar_yawn

    def test_ear_close_between_closed_and_open(self):
        """ear_close doit être entre ear_closed et ear_open."""
        for profile in [PROFILE_LARGE, PROFILE_SMALL]:
            thr = derive_thresholds(profile)
            assert profile.ear_closed < thr.ear_close < profile.ear_open, (
                f"ear_close={thr.ear_close:.4f} hors de [{profile.ear_closed}, {profile.ear_open}]"
            )

    def test_ear_drowsy_above_ear_close(self):
        """ear_drowsy doit être supérieur à ear_close."""
        for profile in [PROFILE_LARGE, PROFILE_SMALL]:
            thr = derive_thresholds(profile)
            assert thr.ear_drowsy > thr.ear_close

    def test_mar_yawn_between_rest_and_yawn(self):
        """mar_yawn_thr doit être entre mar_rest et mar_yawn."""
        for profile in [PROFILE_LARGE, PROFILE_SMALL]:
            thr = derive_thresholds(profile)
            assert profile.mar_rest < thr.mar_yawn < profile.mar_yawn, (
                f"mar_yawn_thr={thr.mar_yawn:.4f} hors de [{profile.mar_rest}, {profile.mar_yawn}]"
            )

    def test_sensitivity_high_stricter_than_low(self):
        """Sensibilité Haute → seuils plus stricts (ear_close plus haut = fermeture détectée plus tôt)."""
        thr_high = derive_thresholds(PROFILE_LARGE, "Haute")
        thr_low = derive_thresholds(PROFILE_LARGE, "Basse")
        # Sensibilité haute → ear_close plus proche de ear_open → plus grand
        assert thr_high.ear_close > thr_low.ear_close

    def test_references_match_profile(self):
        """Les valeurs de référence dans Thresholds doivent correspondre au profil."""
        thr = derive_thresholds(PROFILE_LARGE)
        assert thr.ear_open_ref == PROFILE_LARGE.ear_open
        assert thr.mar_rest_ref == PROFILE_LARGE.mar_rest
        assert thr.pitch_neutral_ref == PROFILE_LARGE.pitch_neutral

    def test_large_eyes_larger_ear_close(self):
        """Profil grands yeux → ear_close absolu plus élevé que petits yeux."""
        thr_large = derive_thresholds(PROFILE_LARGE)
        thr_small = derive_thresholds(PROFILE_SMALL)
        assert thr_large.ear_close > thr_small.ear_close
