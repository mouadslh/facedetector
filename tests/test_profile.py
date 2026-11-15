"""Tests du module profile.py (sans webcam)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.profile import UserProfile, load_profile, save_profile


def test_user_profile_validation():
    # Profil valide
    p = UserProfile(ear_open=0.35, ear_closed=0.10, mar_rest=0.20, mar_yawn=0.65, pitch_neutral=0.0)
    assert p.is_valid()

    # EAR fermé > ouvert (invalide)
    p_bad = UserProfile(ear_open=0.10, ear_closed=0.35, mar_rest=0.20, mar_yawn=0.65, pitch_neutral=0.0)
    assert not p_bad.is_valid()

    # MAR bâillement < repos (invalide)
    p_bad_mar = UserProfile(ear_open=0.35, ear_closed=0.10, mar_rest=0.65, mar_yawn=0.20, pitch_neutral=0.0)
    assert not p_bad_mar.is_valid()


def test_profile_save_and_load(tmp_path: Path):
    prof_path = tmp_path / "test_profile.json"
    p = UserProfile(ear_open=0.32, ear_closed=0.12, mar_rest=0.22, mar_yawn=0.60, pitch_neutral=-0.02)
    save_profile(p, prof_path)

    assert prof_path.exists()
    loaded = load_profile(prof_path)
    assert loaded is not None
    assert loaded.ear_open == pytest.approx(0.32)
    assert loaded.ear_closed == pytest.approx(0.12)
    assert loaded.mar_rest == pytest.approx(0.22)
    assert loaded.mar_yawn == pytest.approx(0.60)
    assert loaded.pitch_neutral == pytest.approx(-0.02)


def test_load_nonexistent_profile(tmp_path: Path):
    loaded = load_profile(tmp_path / "nonexistent.json")
    assert loaded is None
