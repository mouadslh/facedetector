"""
Module pipeline — Orchestration complète du traitement.

Responsabilités :
- Enchaîner caméra → landmarks → qualité → (calibration | surveillance) → état → alarme → log.
- Retourner l'image annotée et un objet PipelineStatus à chaque itération.
- Fonctionner sans Streamlit (pour les tests et evaluate.py).
- Annoter l'image avec le maillage du visage, les métriques et le niveau.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from drowsiguard import config
from drowsiguard.adaptive import AdaptiveBaseline
from drowsiguard.alarm import AlarmManager
from drowsiguard.calibration import CalibrationEngine, CalibrationState, CalibrationStatus
from drowsiguard.camera import CameraCapture
from drowsiguard.landmarks import FaceMeshDetector
from drowsiguard.logger import EventLogger
from drowsiguard.metrics import eye_aspect_ratio, head_pitch, mouth_aspect_ratio
from drowsiguard.profile import UserProfile, load_profile, save_profile
from drowsiguard.quality import QualityResult, check_quality
from drowsiguard.state import AlertLevel, DrowsinessState, StateResult
from drowsiguard.thresholds import Thresholds, derive_thresholds

logger = logging.getLogger(__name__)


@dataclass
class PipelineStatus:
    """État retourné par Pipeline.process() pour une frame."""

    quality: QualityResult
    calibration: CalibrationStatus | None = None
    state_result: StateResult | None = None
    ear: float = 0.0
    mar: float = 0.0
    pitch: float = 0.0
    fps: float = 0.0
    is_calibrated: bool = False
    profile: UserProfile | None = None
    thresholds: Thresholds | None = None


class Pipeline:
    """
    Orchestre l'ensemble du pipeline de détection de somnolence.

    Parameters
    ----------
    sensitivity :
        Sensibilité : "Basse", "Normale" ou "Haute".
    muted :
        Si True, pas d'alarme sonore.
    on_profile_saved :
        Callback appelé quand un profil est sauvegardé.
    """

    def __init__(
        self,
        sensitivity: str = "Normale",
        muted: bool = False,
        on_profile_saved: Callable[[UserProfile], None] | None = None,
    ) -> None:
        self._sensitivity = sensitivity
        self._muted = muted
        self._on_profile_saved = on_profile_saved

        # Composants
        self._detector = FaceMeshDetector()
        self._alarm = AlarmManager(muted=muted)
        self._event_log = EventLogger()

        # Calibration
        self._calibration = CalibrationEngine(on_done=self._on_calibration_done)
        self._profile: UserProfile | None = None
        self._thresholds: Thresholds | None = None

        # Détection
        self._drowsiness: DrowsinessState | None = None
        self._adaptive: AdaptiveBaseline | None = None

        # FPS
        self._last_ts: float = time.monotonic()
        self._fps: float = 0.0

        # Suivi des événements pour éviter les écritures SQLite redondantes
        self._last_logged_microsleep: int = 0
        self._last_logged_yawn: int = 0

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    def load_existing_profile(self) -> UserProfile | None:
        """Tente de charger le profil sauvegardé. Retourne None si absent."""
        profile = load_profile()
        if profile is not None:
            self._apply_profile(profile)
        return profile

    def start_calibration(self) -> None:
        """Relance la calibration (efface le profil courant)."""
        self._calibration.reset()
        self._profile = None
        self._thresholds = None
        self._drowsiness = None
        self._adaptive = None
        self._last_logged_microsleep = 0
        self._last_logged_yawn = 0

    def process(
        self,
        frame: np.ndarray,
        timestamp: float | None = None,
    ) -> tuple[np.ndarray, PipelineStatus]:
        """
        Traite une frame et retourne l'image annotée + le statut.

        Parameters
        ----------
        frame :
            Image BGR.
        timestamp :
            Horodatage (secondes). Si None, utilise time.time().

        Returns
        -------
        tuple[np.ndarray, PipelineStatus]
            (image_annotée, statut)
        """
        ts = timestamp if timestamp is not None else time.time()
        self._update_fps()

        annotated = frame.copy()

        # 1. Détection des landmarks
        landmarks = self._detector.detect(frame)

        # 2. Contrôle qualité
        quality = check_quality(
            frame,
            landmarks,
            calibration_mode=(self._profile is None),
        )

        # 3. Calcul des métriques (si qualité ok)
        ear, mar, pitch = 0.0, 0.0, 0.0
        if quality.ok and landmarks is not None:
            h, w = frame.shape[:2]
            right_pts = self._detector.get_pixels(landmarks, config.RIGHT_EYE_INDICES, (h, w))
            left_pts = self._detector.get_pixels(landmarks, config.LEFT_EYE_INDICES, (h, w))
            mouth_pts = self._detector.get_pixels(landmarks, config.MOUTH_INDICES, (h, w))
            nose_pt = self._detector.get_pixels(landmarks, [config.PITCH_NOSE_TIP], (h, w))[0]
            chin_pt = self._detector.get_pixels(landmarks, [config.PITCH_CHIN], (h, w))[0]
            fore_pt = self._detector.get_pixels(landmarks, [config.PITCH_FOREHEAD], (h, w))[0]

            ear = eye_aspect_ratio(right_pts, left_pts)
            mar = mouth_aspect_ratio(mouth_pts)
            pitch = head_pitch(nose_pt, chin_pt, fore_pt)

        # 4. Calibration ou surveillance
        calib_status: CalibrationStatus | None = None
        state_result: StateResult | None = None

        if self._profile is None:
            # Mode calibration
            calib_status = self._calibration.update(
                ear=ear, mar=mar, pitch=pitch, face_ok=quality.ok, timestamp=ts
            )
        else:
            # Mode surveillance
            assert self._drowsiness is not None
            assert self._adaptive is not None

            # Mise à jour de la ligne de base adaptative
            self._adaptive.update(ear, ts)

            # Calcul de l'état
            state_result = self._drowsiness.update(ear, mar, pitch, ts)

            # Alarme
            self._trigger_alarm(state_result, ts)

            # Log des événements significatifs
            self._log_if_needed(state_result, ear, mar, pitch, ts)

        # 5. Annotation de l'image
        annotated = self._annotate(
            annotated, landmarks, quality, ear, mar, pitch, state_result
        )

        status = PipelineStatus(
            quality=quality,
            calibration=calib_status,
            state_result=state_result,
            ear=ear,
            mar=mar,
            pitch=pitch,
            fps=self._fps,
            is_calibrated=(self._profile is not None),
            profile=self._profile,
            thresholds=self._thresholds,
        )
        return annotated, status

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_calibration_done(self, profile: UserProfile) -> None:
        """Appelé par CalibrationEngine quand la calibration réussit."""
        self._apply_profile(profile)
        save_profile(profile)
        if self._on_profile_saved:
            self._on_profile_saved(profile)

    # ------------------------------------------------------------------
    # Internes
    # ------------------------------------------------------------------

    def _apply_profile(self, profile: UserProfile) -> None:
        """Initialise les composants de détection avec un profil."""
        self._profile = profile
        self._thresholds = derive_thresholds(profile, self._sensitivity)
        self._drowsiness = DrowsinessState(self._thresholds)
        self._adaptive = AdaptiveBaseline(
            ear_open_initial=profile.ear_open,
            ear_close_threshold=self._thresholds.ear_close,
        )
        logger.info("Profil appliqué : ear_open=%.3f, ear_close=%.3f",
                    profile.ear_open, self._thresholds.ear_close)

    def _trigger_alarm(self, result: StateResult, ts: float) -> None:
        """Déclenche l'alarme selon le niveau."""
        if result.level == AlertLevel.DANGER:
            self._alarm.alert_danger(ts)
        elif result.level == AlertLevel.VIGILANCE:
            self._alarm.alert_vigilance(ts)

    def _log_if_needed(
        self, result: StateResult, ear: float, mar: float, pitch: float, ts: float
    ) -> None:
        """Enregistre les événements significatifs (micro-sommeils, bâillements) une seule fois par événement."""
        if result.microsleep_count > self._last_logged_microsleep:
            self._last_logged_microsleep = result.microsleep_count
            self._event_log.log_event(
                event_type="microsleep",
                level=result.level.value,
                ear=ear,
                mar=mar,
                pitch=pitch,
                perclos=result.perclos,
                score=result.score,
                causes=result.reasons,
            )
        if result.yawn_count > self._last_logged_yawn:
            self._last_logged_yawn = result.yawn_count
            self._event_log.log_event(
                event_type="yawn",
                level=result.level.value,
                ear=ear,
                mar=mar,
                pitch=pitch,
                perclos=result.perclos,
                score=result.score,
                causes=result.reasons,
            )

    def _update_fps(self) -> None:
        """Met à jour l'estimation du FPS."""
        now = time.monotonic()
        dt = now - self._last_ts
        self._last_ts = now
        alpha = 0.1
        self._fps = alpha * (1.0 / max(dt, 1e-6)) + (1.0 - alpha) * self._fps

    def _annotate(
        self,
        frame: np.ndarray,
        landmarks: list | None,
        quality: QualityResult,
        ear: float,
        mar: float,
        pitch: float,
        state_result: StateResult | None,
    ) -> np.ndarray:
        """
        Dessine le maillage, les métriques et le statut sur la frame.
        """
        h, w = frame.shape[:2]

        # Couleur du cadre selon le niveau (palette sémantique 60/30/10 en BGR)
        if state_result is not None:
            level_colors = {
                AlertLevel.NORMAL: (94, 197, 34),     # #22C55E
                AlertLevel.VIGILANCE: (11, 158, 245),  # #F59E0B
                AlertLevel.DANGER: (68, 68, 239),     # #EF4444
            }
            border_color = level_colors.get(state_result.level, (94, 197, 34))
        else:
            border_color = (191, 163, 143)  # #8FA3BF

        # Cadre de niveau (épaisseur 4 px selon spécification UI)
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), border_color, 4)

        # Maillage du visage (points clés uniquement pour la performance)
        if landmarks is not None:
            key_indices = (
                config.RIGHT_EYE_INDICES
                + config.LEFT_EYE_INDICES
                + config.MOUTH_INDICES
                + [config.PITCH_NOSE_TIP, config.PITCH_CHIN, config.PITCH_FOREHEAD]
            )
            for idx in key_indices:
                lm = landmarks[idx]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 2, (0, 255, 128), -1)

        # Texte de statut qualité
        cv2.putText(
            frame, quality.message, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (255, 255, 255) if quality.ok else (0, 100, 255), 2,
        )

        # Métriques
        if quality.ok:
            cv2.putText(frame, f"EAR: {ear:.3f}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 1)
            cv2.putText(frame, f"MAR: {mar:.3f}", (10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 1)
            cv2.putText(frame, f"FPS: {self._fps:.0f}", (w - 80, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        # Niveau de somnolence
        if state_result is not None:
            level_text = f"Niveau : {state_result.level.value}"
            level_color = level_colors.get(state_result.level, (255, 255, 255))
            cv2.putText(frame, level_text, (10, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, level_color, 2)
            cv2.putText(frame, f"Score : {state_result.score:.0f}/100", (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        return frame

    def set_sensitivity(self, sensitivity: str) -> None:
        """Change la sensibilité et recalcule les seuils si calibré."""
        self._sensitivity = sensitivity
        if self._profile is not None:
            self._apply_profile(self._profile)

    def set_muted(self, muted: bool) -> None:
        """Active ou désactive le son."""
        self._muted = muted
        self._alarm.muted = muted

    def test_alarm(self, level: str) -> bool:
        """Joue un son de test pour vérifier la sortie audio locale."""
        return self._alarm.test_sound(level)

    def close(self) -> None:
        """Libère toutes les ressources."""
        self._detector.close()
        self._alarm.close()
        self._event_log.close()
