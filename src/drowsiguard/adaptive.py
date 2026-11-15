"""
Module adaptive — Adaptation lente de la ligne de base EAR_open.

Responsabilités :
- Re-estimer lentement l'EAR en conditions d'éveil (percentile élevé sur fenêtre glissante).
- Exclure les périodes de fermeture prolongée pour ne pas dériver pendant une somnolence.
- Limiter l'amplitude et la vitesse d'adaptation.
- Mettre à jour le seuil dérivé de thresholds.py en conséquence.
"""

from __future__ import annotations

import logging
from collections import deque

import numpy as np

from drowsiguard import config

logger = logging.getLogger(__name__)


class AdaptiveBaseline:
    """
    Estime lentement la ligne de base EAR_open de l'utilisateur.

    L'estimation est bloquée si l'EAR est en dessous du seuil de fermeture
    (pour éviter de dériver pendant un micro-sommeil).

    Parameters
    ----------
    ear_open_initial :
        Valeur initiale de EAR_open (issue du profil calibré).
    ear_close_threshold :
        Seuil en dessous duquel l'œil est considéré fermé (issu de thresholds.py).
    window_s :
        Durée de la fenêtre glissante en secondes.
    percentile :
        Percentile utilisé pour estimer l'EAR_open (ex. 90).
    max_speed :
        Vitesse maximale d'adaptation par seconde (fraction).
    max_drift :
        Amplitude maximale de dérive autorisée (fraction de la valeur initiale).
    """

    def __init__(
        self,
        ear_open_initial: float,
        ear_close_threshold: float,
        window_s: float = config.ADAPTIVE_WINDOW_S,
        percentile: float = config.ADAPTIVE_PERCENTILE,
        max_speed: float = config.ADAPTIVE_MAX_SPEED,
        max_drift: float = config.ADAPTIVE_MAX_DRIFT,
    ) -> None:
        self._ear_open_initial = ear_open_initial
        self._ear_close_thr = ear_close_threshold
        self._window_s = window_s
        self._percentile = percentile
        self._max_speed = max_speed
        self._max_drift = max_drift

        self._ear_open_current = ear_open_initial
        # Deque de (timestamp, ear_value) pour les échantillons en éveil
        self._buffer: deque[tuple[float, float]] = deque()
        self._last_update_ts: float | None = None

    @property
    def ear_open(self) -> float:
        """Estimation courante de EAR_open."""
        return self._ear_open_current

    def update(self, ear: float, timestamp: float) -> float:
        """
        Met à jour l'estimation de EAR_open avec une nouvelle mesure.

        Parameters
        ----------
        ear :
            EAR mesuré à cet instant.
        timestamp :
            Horodatage Unix (secondes). Injectable pour les tests.

        Returns
        -------
        float
            Estimation courante mise à jour de EAR_open.
        """
        # Exclure les mesures pendant les fermetures
        if ear >= self._ear_close_thr:
            self._buffer.append((timestamp, ear))

        # Purger les échantillons trop anciens
        cutoff = timestamp - self._window_s
        while self._buffer and self._buffer[0][0] < cutoff:
            self._buffer.popleft()

        # Calculer la cible si assez d'échantillons
        if len(self._buffer) >= 10:
            values = np.array([v for _, v in self._buffer], dtype=float)
            target = float(np.percentile(values, self._percentile))

            # Limiter la dérive maximale par rapport à la valeur initiale
            lo = self._ear_open_initial * (1.0 - self._max_drift)
            hi = self._ear_open_initial * (1.0 + self._max_drift)
            target = float(np.clip(target, lo, hi))

            # Limiter la vitesse d'adaptation
            if self._last_update_ts is not None:
                dt = timestamp - self._last_update_ts
                max_delta = self._max_speed * dt
                delta = target - self._ear_open_current
                delta = float(np.clip(delta, -max_delta, max_delta))
                self._ear_open_current += delta
            else:
                self._ear_open_current = target

        self._last_update_ts = timestamp
        return self._ear_open_current

    def reset(self, ear_open: float, ear_close_threshold: float) -> None:
        """
        Réinitialise la ligne de base (après recalibration).

        Parameters
        ----------
        ear_open :
            Nouvelle valeur de référence.
        ear_close_threshold :
            Nouveau seuil de fermeture.
        """
        self._ear_open_initial = ear_open
        self._ear_open_current = ear_open
        self._ear_close_thr = ear_close_threshold
        self._buffer.clear()
        self._last_update_ts = None
        logger.info("AdaptiveBaseline réinitialisée : ear_open=%.3f", ear_open)
