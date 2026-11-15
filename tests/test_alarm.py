"""Tests du module alarm.py (sans matériel audio réel)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.alarm import AlarmManager


def test_alarm_muted():
    mgr = AlarmManager(muted=True)
    assert mgr.muted

    # Doit s'exécuter sans erreur ni son
    mgr.alert_vigilance(timestamp=10.0)
    mgr.alert_danger(timestamp=10.0)
    mgr.stop()
    mgr.close()


def test_alarm_unmuted_cooldown():
    mgr = AlarmManager(muted=False)
    assert not mgr.muted

    # Deux appels rapprochés respectent le cooldown
    mgr.alert_vigilance(timestamp=10.0)
    mgr.alert_vigilance(timestamp=10.5)  # En cooldown (< 3.0 s)
    mgr.alert_danger(timestamp=10.0)

    mgr.stop()
    mgr.close()
