"""
Module calibration — Machine à états de la calibration guidée.

Responsabilités :
- Conduire l'utilisateur à travers 3 phases de mesure (yeux ouverts, yeux fermés, bâillement).
- Collecter les valeurs EAR, MAR et pitch par frame.
- Utiliser la médiane et rejeter les valeurs aberrantes (winsorisation).
- Valider la cohérence du profil et recommencer si nécessaire.
- Produire un UserProfile complet en sortie.

États : WAITING_FACE → PHASE_OPEN → PHASE_CLOSED → PHASE_YAWN → DONE (ou FAILED).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Callable

import numpy as np

from drowsiguard import config
from drowsiguard.profile import UserProfile, _is_valid

logger = logging.getLogger(__name__)


class CalibrationState(Enum):
    """États possibles de la machine à états de calibration."""

    WAITING_FACE = auto()   # Attente d'un visage stable
    PHASE_OPEN = auto()     # Yeux ouverts — mesure EAR_open, MAR_rest, pitch_neutral
    PHASE_CLOSED = auto()   # Yeux fermés — mesure EAR_closed
    PHASE_YAWN = auto()     # Bâillement — mesure MAR_yawn
    DONE = auto()           # Calibration réussie
    FAILED = auto()         # Échec — message + relance automatique


@dataclass
class CalibrationStatus:
    """État courant retourné à chaque itération."""

    state: CalibrationState
    """État actuel de la machine."""

    message: str
    """Consigne ou message d'erreur à afficher à l'utilisateur."""

    progress: float
    """Progression de 0.0 à 1.0 (pour la barre de progression)."""

    profile: UserProfile | None = None
    """Profil complet, disponible uniquement à l'état DONE."""


class CalibrationEngine:
    """
    Machine à états de calibration guidée.

    Parameters
    ----------
    on_done :
        Callback appelé avec le UserProfile dès la fin de la calibration.
    """

    # Durées totale de calibration (utilisées pour la barre de progression)
    _TOTAL_S: float = (
        config.CALIB_STABILIZE_S
        + config.CALIB_PHASE_OPEN_S
        + config.CALIB_STABILIZE_S
        + config.CALIB_PHASE_CLOSED_S
        + config.CALIB_STABILIZE_S
        + config.CALIB_PHASE_YAWN_S
    )

    def __init__(self, on_done: Callable[[UserProfile], None] | None = None) -> None:
        self._on_done = on_done
        self._reset()

    def _reset(self) -> None:
        """Réinitialise la machine à états."""
        self._state = CalibrationState.WAITING_FACE
        self._phase_start_ts: float = 0.0
        self._stable_face_start: float | None = None
        self._elapsed_calib: float = 0.0

        # Buffers de mesure
        self._ear_open_buf: list[float] = []
        self._mar_rest_buf: list[float] = []
        self._pitch_buf: list[float] = []
        self._ear_closed_buf: list[float] = []
        self._mar_yawn_buf: list[float] = []

        self._last_profile: UserProfile | None = None
        self._fail_message: str = ""

    def reset(self) -> None:
        """Relance la calibration depuis le début."""
        self._reset()

    @property
    def state(self) -> CalibrationState:
        """État courant."""
        return self._state

    @property
    def profile(self) -> UserProfile | None:
        """Profil produit (disponible après DONE)."""
        return self._last_profile

    def update(
        self,
        ear: float,
        mar: float,
        pitch: float,
        face_ok: bool,
        timestamp: float,
    ) -> CalibrationStatus:
        """
        Avance la machine à états d'une frame.

        Parameters
        ----------
        ear :
            EAR courant (moyennés sur les deux yeux).
        mar :
            MAR courant.
        pitch :
            Pitch normalisé courant.
        face_ok :
            True si la qualité est suffisante.
        timestamp :
            Horodatage Unix (secondes). Injectable pour les tests.

        Returns
        -------
        CalibrationStatus
            État et consignes à afficher.
        """
        if self._state == CalibrationState.DONE:
            return CalibrationStatus(
                state=self._state,
                message="Calibration terminée ✓",
                progress=1.0,
                profile=self._last_profile,
            )

        if self._state == CalibrationState.FAILED:
            return CalibrationStatus(
                state=self._state,
                message=self._fail_message,
                progress=0.0,
            )

        # --- Attente d'un visage stable ---
        if self._state == CalibrationState.WAITING_FACE:
            return self._step_waiting(face_ok, timestamp)

        # --- Phases de mesure ---
        if not face_ok:
            # Visage perdu pendant la calibration → on repart en attente
            self._state = CalibrationState.WAITING_FACE
            self._stable_face_start = None
            return CalibrationStatus(
                state=self._state,
                message="Visage perdu — repositionnez-vous",
                progress=self._progress(timestamp),
            )

        if self._state == CalibrationState.PHASE_OPEN:
            return self._step_open(ear, mar, pitch, timestamp)

        if self._state == CalibrationState.PHASE_CLOSED:
            return self._step_closed(ear, timestamp)

        if self._state == CalibrationState.PHASE_YAWN:
            return self._step_yawn(mar, timestamp)

        # Cas impossible
        return CalibrationStatus(state=self._state, message="", progress=0.0)

    # ------------------------------------------------------------------
    # Étapes internes
    # ------------------------------------------------------------------

    def _step_waiting(self, face_ok: bool, ts: float) -> CalibrationStatus:
        if not face_ok:
            self._stable_face_start = None
            return CalibrationStatus(
                state=self._state,
                message="Placez-vous face à la caméra pour démarrer la calibration",
                progress=0.0,
            )
        if self._stable_face_start is None:
            self._stable_face_start = ts
        elapsed = ts - self._stable_face_start
        if elapsed >= config.CALIB_STABILIZE_S:
            self._state = CalibrationState.PHASE_OPEN
            self._phase_start_ts = ts
            self._elapsed_calib = 0.0
            return CalibrationStatus(
                state=self._state,
                message="👀 Regardez devant vous — yeux ouverts, bouche fermée",
                progress=0.0,
            )
        return CalibrationStatus(
            state=self._state,
            message="Visage détecté — calibration dans {:.0f} s…".format(
                config.CALIB_STABILIZE_S - elapsed
            ),
            progress=0.0,
        )

    def _step_open(self, ear: float, mar: float, pitch: float, ts: float) -> CalibrationStatus:
        elapsed = ts - self._phase_start_ts
        # Ignorer les clignements (EAR trop bas pendant cette phase)
        if ear > config.FALLBACK_EAR_CLOSED + 0.02:
            self._ear_open_buf.append(ear)
            self._mar_rest_buf.append(mar)
            self._pitch_buf.append(pitch)

        progress = self._progress_phase(elapsed, 0, config.CALIB_PHASE_OPEN_S)

        if elapsed >= config.CALIB_PHASE_OPEN_S:
            if len(self._ear_open_buf) < 5:
                return self._fail("Données insuffisantes en phase 1. Recommencez.")
            self._state = CalibrationState.PHASE_CLOSED
            self._phase_start_ts = ts
            return CalibrationStatus(
                state=self._state,
                message="😌 Fermez les yeux doucement pendant 2 secondes",
                progress=progress,
            )

        return CalibrationStatus(
            state=self._state,
            message="👀 Regardez devant vous — yeux ouverts, bouche fermée",
            progress=progress,
        )

    def _step_closed(self, ear: float, ts: float) -> CalibrationStatus:
        elapsed = ts - self._phase_start_ts
        # Détection automatique de la fermeture (chute de l'EAR)
        open_median = float(np.median(self._ear_open_buf)) if self._ear_open_buf else config.FALLBACK_EAR_OPEN
        closed_threshold = open_median * 0.65
        if ear < closed_threshold:
            self._ear_closed_buf.append(ear)

        progress = self._progress_phase(
            elapsed,
            config.CALIB_PHASE_OPEN_S,
            config.CALIB_PHASE_OPEN_S + config.CALIB_PHASE_CLOSED_S,
        )

        if elapsed >= config.CALIB_PHASE_CLOSED_S:
            if len(self._ear_closed_buf) < 3:
                return self._fail(
                    "Yeux pas assez fermés en phase 2. Fermez bien les yeux et recommencez."
                )
            self._state = CalibrationState.PHASE_YAWN
            self._phase_start_ts = ts
            return CalibrationStatus(
                state=self._state,
                message="Ouvrez grand la bouche — comme pour bâiller",
                progress=progress,
            )

        return CalibrationStatus(
            state=self._state,
            message="😌 Fermez les yeux doucement…",
            progress=progress,
        )

    def _step_yawn(self, mar: float, ts: float) -> CalibrationStatus:
        elapsed = ts - self._phase_start_ts
        rest_median = float(np.median(self._mar_rest_buf)) if self._mar_rest_buf else config.FALLBACK_MAR_REST
        yawn_threshold = rest_median + config.CALIB_MAR_MIN_DELTA * 0.5
        if mar > yawn_threshold:
            self._mar_yawn_buf.append(mar)

        total_elapsed = (
            config.CALIB_PHASE_OPEN_S
            + config.CALIB_PHASE_CLOSED_S
            + elapsed
        )
        progress = self._progress_phase(
            total_elapsed,
            0,
            config.CALIB_PHASE_OPEN_S + config.CALIB_PHASE_CLOSED_S + config.CALIB_PHASE_YAWN_S,
        )

        if elapsed >= config.CALIB_PHASE_YAWN_S:
            return self._finalize(ts)

        return CalibrationStatus(
            state=self._state,
            message="Ouvrez grand la bouche — comme pour bâiller",
            progress=progress,
        )

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------

    def _finalize(self, ts: float) -> CalibrationStatus:
        """Calcule le profil à partir des buffers et valide."""
        ear_open = _trimmed_median(self._ear_open_buf, config.CALIB_OUTLIER_TRIM)
        ear_closed = _trimmed_median(self._ear_closed_buf, config.CALIB_OUTLIER_TRIM)
        mar_rest = _trimmed_median(self._mar_rest_buf, config.CALIB_OUTLIER_TRIM)
        mar_yawn_data = self._mar_yawn_buf if self._mar_yawn_buf else self._mar_rest_buf
        mar_yawn = _trimmed_median(mar_yawn_data, config.CALIB_OUTLIER_TRIM)
        pitch_neutral = _trimmed_median(self._pitch_buf, config.CALIB_OUTLIER_TRIM)

        profile = UserProfile(
            ear_open=ear_open,
            ear_closed=ear_closed,
            mar_rest=mar_rest,
            mar_yawn=mar_yawn,
            pitch_neutral=pitch_neutral,
            calibration_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if not _is_valid(profile):
            return self._fail(
                "Calibration incohérente (yeux pas assez distincts ou bâillement trop petit). "
                "Recommencez en exagérant les gestes."
            )

        self._state = CalibrationState.DONE
        self._last_profile = profile
        if self._on_done:
            self._on_done(profile)
        logger.info("Calibration réussie : %s", profile)
        return CalibrationStatus(
            state=self._state,
                message="Calibration terminée — surveillance démarrée",
            progress=1.0,
            profile=profile,
        )

    def _fail(self, message: str) -> CalibrationStatus:
        """Passe à l'état FAILED et prépare le message."""
        self._fail_message = message
        self._state = CalibrationState.FAILED
        logger.warning("Calibration échouée : %s", message)
        return CalibrationStatus(
            state=self._state,
            message=message,
            progress=0.0,
        )

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def _progress(self, ts: float) -> float:
        """Progression globale approximative (0-1)."""
        return min(1.0, self._elapsed_calib / self._TOTAL_S)

    def _progress_phase(self, elapsed: float, start: float, end: float) -> float:
        """Progression linéaire dans une phase."""
        total = self._TOTAL_S
        if total < 1e-6:
            return 0.0
        return min(1.0, (start + elapsed) / total)


# ---------------------------------------------------------------------------
# Utilitaire de statistique robuste
# ---------------------------------------------------------------------------


def _trimmed_median(values: list[float], trim: float) -> float:
    """
    Calcule la médiane après suppression des extrêmes (winsorisation).

    Parameters
    ----------
    values :
        Liste de valeurs brutes.
    trim :
        Fraction à éliminer de chaque côté (ex. 0.10 → 10 %).

    Returns
    -------
    float
        Médiane robuste. Retourne 0.0 si la liste est vide.
    """
    if not values:
        return 0.0
    arr = np.array(values, dtype=float)
    n = len(arr)
    k = max(0, int(n * trim))
    arr_sorted = np.sort(arr)
    trimmed = arr_sorted[k: n - k] if n - k > k else arr_sorted
    return float(np.median(trimmed))
