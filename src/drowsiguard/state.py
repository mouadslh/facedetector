"""
Module state — Calcul de l'état de somnolence en temps réel.

Responsabilités :
- Accumuler les mesures EAR, MAR et pitch frame par frame.
- Calculer le PERCLOS (pourcentage du temps yeux fermés) sur fenêtre glissante.
- Détecter les micro-sommeils, les bâillements, les chutes de tête.
- Calculer un score de fatigue pondéré (0-100) et le niveau (Normal, Vigilance, Danger).
- Retourner un StateResult complet à chaque appel de update().
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

from drowsiguard import config
from drowsiguard.thresholds import Thresholds

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Niveau d'alerte de somnolence."""

    NORMAL = "Normal"
    VIGILANCE = "Vigilance"
    DANGER = "Danger"


@dataclass
class StateResult:
    """Résultat retourné par DrowsinessState.update() pour une frame."""

    ear: float
    mar: float
    pitch: float

    perclos: float
    """Proportion des yeux fermés sur la fenêtre glissante [0, 1]."""

    closed_duration: float
    """Durée de fermeture continue actuelle (secondes)."""

    yawn_count: int
    """Nombre de bâillements depuis le début de la session."""

    microsleep_count: int
    """Nombre de micro-sommeils détectés."""

    score: float
    """Score de fatigue agrégé [0, 100]."""

    level: AlertLevel
    """Niveau d'alerte courant."""

    reasons: list[str]
    """Liste lisible des causes de somnolence détectées."""

    blink_duration: float = 0.0
    """Durée du clignement en cours (secondes), 0 si yeux ouverts."""


class DrowsinessState:
    """
    Accumule les mesures et calcule l'état de somnolence en temps réel.

    Parameters
    ----------
    thresholds :
        Seuils personnalisés dérivés du profil.
    perclos_window_s :
        Durée de la fenêtre glissante pour le PERCLOS.
    """

    def __init__(
        self,
        thresholds: Thresholds,
        perclos_window_s: float = config.PERCLOS_WINDOW_S,
    ) -> None:
        self._thr = thresholds
        self._perclos_window_s = perclos_window_s

        # Buffer PERCLOS : (timestamp, is_closed)
        self._perclos_buf: deque[tuple[float, bool]] = deque()

        # Fermeture continue
        self._eyes_closed_start: float | None = None
        self._closed_duration: float = 0.0

        # Bâillements
        self._yawn_active: bool = False
        self._yawn_start: float | None = None
        self._yawn_last_seen: float | None = None
        self._yawn_count: int = 0
        self._last_yawn_end: float = -float("inf")

        # Micro-sommeils
        self._microsleep_count: int = 0
        self._microsleep_confirmed: bool = False

        # Score lissé
        self._score_smooth: float = 0.0

    def update(
        self,
        ear: float,
        mar: float,
        pitch: float,
        timestamp: float,
    ) -> StateResult:
        """
        Met à jour l'état avec les mesures de la frame courante.

        Parameters
        ----------
        ear :
            EAR mesuré.
        mar :
            MAR mesuré.
        pitch :
            Pitch normalisé mesuré.
        timestamp :
            Horodatage Unix (secondes). Injectable pour les tests.

        Returns
        -------
        StateResult
            État complet de somnolence.
        """
        is_closed = ear < self._thr.ear_close
        is_yawning = mar > self._thr.mar_yawn
        head_drop = pitch > self._thr.pitch_forward

        # --- PERCLOS ---
        perclos = self._update_perclos(is_closed, timestamp)

        # --- Durée de fermeture continue ---
        closed_duration, microsleep_new = self._update_closed_duration(is_closed, timestamp)

        # --- Bâillements ---
        yawn_detected = self._update_yawns(is_yawning, timestamp)

        # --- Score ---
        score = self._compute_score(ear, perclos, mar, pitch, closed_duration)

        # --- Niveau ---
        reasons: list[str] = []
        level = AlertLevel.NORMAL

        if closed_duration > config.MICROSLEEP_DURATION_S:
            reasons.append(f"yeux fermés {closed_duration:.1f} s")
        if closed_duration > config.DANGER_DURATION_S or self._microsleep_confirmed:
            level = AlertLevel.DANGER
        elif score > config.SCORE_DANGER:
            level = AlertLevel.DANGER
        elif score > config.SCORE_VIGILANCE:
            level = AlertLevel.VIGILANCE

        if perclos > 0.15:
            reasons.append(f"PERCLOS {perclos*100:.0f} %")
            if perclos > 0.25:
                level = AlertLevel.DANGER
            elif level == AlertLevel.NORMAL:
                level = AlertLevel.VIGILANCE

        if yawn_detected:
            reasons.append("bâillement")

        if self._yawn_count >= 3:
            reasons.append(f"{self._yawn_count} bâillements")
            if level == AlertLevel.NORMAL:
                level = AlertLevel.VIGILANCE

        if head_drop:
            reasons.append("chute de tête")
            if level == AlertLevel.NORMAL:
                level = AlertLevel.VIGILANCE

        return StateResult(
            ear=ear,
            mar=mar,
            pitch=pitch,
            perclos=perclos,
            closed_duration=closed_duration,
            yawn_count=self._yawn_count,
            microsleep_count=self._microsleep_count,
            score=score,
            level=level,
            reasons=reasons,
            blink_duration=closed_duration if is_closed else 0.0,
        )

    # ------------------------------------------------------------------
    # Méthodes internes
    # ------------------------------------------------------------------

    def _update_perclos(self, is_closed: bool, ts: float) -> float:
        """Met à jour le buffer PERCLOS et retourne la valeur courante."""
        self._perclos_buf.append((ts, is_closed))
        cutoff = ts - self._perclos_window_s
        while self._perclos_buf and self._perclos_buf[0][0] < cutoff:
            self._perclos_buf.popleft()
        if not self._perclos_buf:
            return 0.0
        closed_count = sum(1 for _, c in self._perclos_buf if c)
        return closed_count / len(self._perclos_buf)

    def _update_closed_duration(
        self, is_closed: bool, ts: float
    ) -> tuple[float, bool]:
        """
        Met à jour la durée de fermeture continue.

        Returns
        -------
        tuple[float, bool]
            (durée_courante, micro_sommeil_nouveau_confirmé)
        """
        microsleep_new = False
        if is_closed:
            if self._eyes_closed_start is None:
                self._eyes_closed_start = ts
                self._microsleep_confirmed = False
            self._closed_duration = ts - self._eyes_closed_start
            if (
                self._closed_duration >= config.MICROSLEEP_DURATION_S
                and not self._microsleep_confirmed
            ):
                self._microsleep_confirmed = True
                self._microsleep_count += 1
                microsleep_new = True
        else:
            self._eyes_closed_start = None
            self._closed_duration = 0.0
            self._microsleep_confirmed = False

        return self._closed_duration, microsleep_new

    def _update_yawns(self, is_yawning: bool, ts: float) -> bool:
        """
        Détecte les bâillements (début + durée minimale + cooldown).

        Returns
        -------
        bool
            True si un nouveau bâillement vient d'être confirmé.
        """
        if is_yawning:
            if not self._yawn_active:
                self._yawn_active = True
                self._yawn_start = ts
            self._yawn_last_seen = ts
        else:
            if self._yawn_active:
                duration = (self._yawn_last_seen or ts) - (self._yawn_start or ts)
                self._yawn_active = False
                if (
                    duration >= config.YAWN_MIN_DURATION_S
                    and ts - self._last_yawn_end >= config.YAWN_COOLDOWN_S
                ):
                    self._yawn_count += 1
                    self._last_yawn_end = ts
                    return True
                self._yawn_start = None
                self._yawn_last_seen = None
        return False

    def _compute_score(
        self,
        ear: float,
        perclos: float,
        mar: float,
        pitch: float,
        closed_duration: float,
    ) -> float:
        """
        Calcule le score de fatigue agrégé (0-100).

        Chaque sous-score est normalisé entre 0 et 1 puis pondéré.
        """
        thr = self._thr

        # Sous-score EAR : 1 = yeux fermés, 0 = grands ouverts
        ear_range = max(thr.ear_open_ref - thr.ear_close, 1e-6)
        ear_sub = float(max(0.0, min(1.0, (thr.ear_open_ref - ear) / ear_range)))

        # Sous-score PERCLOS : 0.25 → score 1.0
        perclos_sub = float(min(1.0, perclos / 0.25))

        # Sous-score MAR : 1 = bâillement complet
        mar_range = max(thr.mar_yawn - thr.mar_rest_ref, 1e-6)
        mar_sub = float(max(0.0, min(1.0, (mar - thr.mar_rest_ref) / mar_range)))

        # Sous-score tête
        pitch_range = max(thr.pitch_forward - thr.pitch_neutral_ref, 1e-6)
        head_sub = float(max(0.0, min(1.0, (pitch - thr.pitch_neutral_ref) / pitch_range)))

        # Score pondéré (somme des poids = 1.0 après normalisation)
        total_weight = (
            config.SCORE_WEIGHT_EAR
            + config.SCORE_WEIGHT_PERCLOS
            + config.SCORE_WEIGHT_MAR
            + config.SCORE_WEIGHT_HEAD
        )
        raw_score = (
            config.SCORE_WEIGHT_EAR * ear_sub
            + config.SCORE_WEIGHT_PERCLOS * perclos_sub
            + config.SCORE_WEIGHT_MAR * mar_sub
            + config.SCORE_WEIGHT_HEAD * head_sub
        ) / max(total_weight, 1e-6)

        # Lissage exponentiel (τ ≈ 5 frames)
        alpha = 0.2
        self._score_smooth = alpha * (raw_score * 100.0) + (1.0 - alpha) * self._score_smooth
        return round(self._score_smooth, 1)

    def reset(self, thresholds: Thresholds) -> None:
        """Réinitialise l'état (après recalibration)."""
        self._thr = thresholds
        self._perclos_buf.clear()
        self._eyes_closed_start = None
        self._closed_duration = 0.0
        self._yawn_active = False
        self._yawn_start = None
        self._yawn_count = 0
        self._last_yawn_end = 0.0
        self._microsleep_count = 0
        self._microsleep_confirmed = False
        self._score_smooth = 0.0
