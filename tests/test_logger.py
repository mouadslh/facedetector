"""Tests du module logger.py (sans webcam)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.logger import EventLogger


def test_logger_lifecycle(tmp_path: Path):
    db_path = tmp_path / "test_events.db"
    log = EventLogger(db_path=db_path)

    # Enregistrer quelques événements
    log.log_event("alert_vigilance", level="Vigilance", score=45.2, ear=0.22, perclos=0.18, causes=["yeux mi-clos"])
    log.log_event("alert_danger", level="Danger", score=78.5, ear=0.11, perclos=0.35, causes=["yeux fermés 2.6 s", "chute de tête"])

    history = log.get_history(limit=10)
    assert len(history) == 2
    assert history[0].level == "Danger"
    assert history[1].level == "Vigilance"
    assert history[0].event_type == "alert_danger"

    # Export CSV
    csv_path = tmp_path / "export.csv"
    res_path = log.export_csv(csv_path)
    assert res_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "alert_danger" in content
    assert "alert_vigilance" in content

    log.close()
