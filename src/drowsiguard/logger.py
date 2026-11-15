"""
Module logger — Journal d'événements dans SQLite.

Responsabilités :
- Créer et gérer la base de données SQLite data/events.db.
- Enregistrer les événements horodatés (type, niveau, valeurs, causes).
- Lire l'historique des événements.
- Exporter les événements en CSV.
"""

from __future__ import annotations

import csv
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path("data/events.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    level       TEXT    NOT NULL,
    ear         REAL,
    mar         REAL,
    pitch       REAL,
    perclos     REAL,
    score       REAL,
    causes      TEXT
);
"""


@dataclass
class EventRecord:
    """Un enregistrement d'événement lu depuis la base."""

    id: int
    timestamp: str
    event_type: str
    level: str
    ear: float | None
    mar: float | None
    pitch: float | None
    perclos: float | None
    score: float | None
    causes: str


class EventLogger:
    """
    Journal d'événements SQLite.

    Parameters
    ----------
    db_path :
        Chemin du fichier SQLite.
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    def log_event(
        self,
        event_type: str,
        level: str,
        ear: float | None = None,
        mar: float | None = None,
        pitch: float | None = None,
        perclos: float | None = None,
        score: float | None = None,
        causes: list[str] | None = None,
        timestamp: str | None = None,
    ) -> None:
        """
        Enregistre un événement dans la base.

        Parameters
        ----------
        event_type :
            Type d'événement : 'microsleep', 'yawn', 'alert_vigilance', 'alert_danger', etc.
        level :
            Niveau d'alerte : 'Normal', 'Vigilance', 'Danger'.
        causes :
            Liste de raisons lisibles (ex. ['yeux fermés 2.1 s', 'PERCLOS 18 %']).
        timestamp :
            ISO 8601. Si None, utilise l'heure courante UTC.
        """
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        causes_str = ", ".join(causes) if causes else ""
        try:
            self._conn.execute(
                "INSERT INTO events "
                "(timestamp, event_type, level, ear, mar, pitch, perclos, score, causes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, event_type, level, ear, mar, pitch, perclos, score, causes_str),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            logger.error("Erreur d'enregistrement SQLite : %s", exc)

    def get_history(self, limit: int = 200) -> list[EventRecord]:
        """
        Retourne les N derniers événements.

        Parameters
        ----------
        limit :
            Nombre maximum d'événements à retourner.

        Returns
        -------
        list[EventRecord]
            Liste triée du plus récent au plus ancien.
        """
        try:
            cursor = self._conn.execute(
                "SELECT id, timestamp, event_type, level, ear, mar, pitch, perclos, score, causes "
                "FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [EventRecord(*row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            logger.error("Erreur de lecture SQLite : %s", exc)
            return []

    def export_csv(self, output_path: Path) -> Path:
        """
        Exporte tous les événements vers un fichier CSV.

        Parameters
        ----------
        output_path :
            Chemin du fichier CSV à créer.

        Returns
        -------
        Path
            Chemin du fichier créé.
        """
        records = self.get_history(limit=100_000)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["id", "timestamp", "event_type", "level", "ear", "mar", "pitch", "perclos", "score", "causes"]
            )
            for r in records:
                writer.writerow(
                    [r.id, r.timestamp, r.event_type, r.level, r.ear, r.mar, r.pitch, r.perclos, r.score, r.causes]
                )
        logger.info("Export CSV : %s (%d lignes)", output_path, len(records))
        return output_path

    def close(self) -> None:
        """Ferme la connexion SQLite."""
        try:
            self._conn.close()
        except sqlite3.Error:
            pass
