"""
Module quality — Contrôle qualité de la frame avant toute mesure.

Responsabilités :
- Vérifier la présence du visage.
- Vérifier la taille du visage (trop loin = mesures imprécises).
- Vérifier la luminosité (trop sombre ou surexposé).
- Vérifier l'inclinaison de la tête (trop inclinée = EAR/MAR faussés).
- Vérifier que le visage est suffisamment centré.
- Retourner un statut lisible et un message utilisateur.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from drowsiguard import config


@dataclass
class QualityResult:
    """Résultat du contrôle qualité d'une frame."""

    ok: bool
    """True si la qualité est suffisante pour la mesure."""

    status: str
    """Code interne du statut (ex. 'NO_FACE', 'TOO_DARK', 'OK')."""

    message: str
    """Message lisible pour l'interface utilisateur."""

    brightness: float = 0.0
    """Luminosité moyenne sur la région du visage (0-255)."""

    face_ratio: float = 0.0
    """Taille du visage en fraction de la hauteur de l'image."""

    pitch_deg: float = 0.0
    """Inclinaison de la tête estimée en degrés (positif = tête en avant)."""


def check_quality(
    frame: np.ndarray,
    landmarks: list[mp.framework.formats.landmark_pb2.NormalizedLandmark] | None,
    calibration_mode: bool = False,
) -> QualityResult:
    """
    Vérifie la qualité de la frame pour la détection ou la calibration.

    Parameters
    ----------
    frame :
        Image BGR (uint8).
    landmarks :
        Liste de 468 points normalisés ou None si aucun visage.
    calibration_mode :
        Si True, applique des critères plus stricts (inclinaison).

    Returns
    -------
    QualityResult
        Résultat du contrôle qualité.
    """
    h, w = frame.shape[:2]

    # 1. Visage détecté ?
    if landmarks is None:
        return QualityResult(
            ok=False,
            status="NO_FACE",
            message="Aucun visage détecté — placez-vous face à la caméra",
        )

    # 2. Taille du visage
    face_ratio = _estimate_face_ratio(landmarks, h)
    if face_ratio < config.QUALITY_MIN_FACE_RATIO:
        return QualityResult(
            ok=False,
            status="TOO_FAR",
            message="Rapprochez-vous de la caméra",
            face_ratio=face_ratio,
        )

    # 3. Luminosité
    brightness = _estimate_brightness(frame, landmarks, h, w)
    if brightness < config.QUALITY_MIN_BRIGHTNESS:
        return QualityResult(
            ok=False,
            status="TOO_DARK",
            message="Trop sombre — éclairez davantage votre visage",
            brightness=brightness,
            face_ratio=face_ratio,
        )
    if brightness > config.QUALITY_MAX_BRIGHTNESS:
        return QualityResult(
            ok=False,
            status="TOO_BRIGHT",
            message="Trop lumineux — réduisez l'éclairage",
            brightness=brightness,
            face_ratio=face_ratio,
        )

    # 4. Inclinaison (pitch)
    pitch_deg = _estimate_pitch_deg(landmarks, h)
    max_pitch = (
        config.QUALITY_MAX_PITCH_DEG_CALIB if calibration_mode else config.QUALITY_MAX_PITCH_DEG
    )
    if abs(pitch_deg) > max_pitch:
        return QualityResult(
            ok=False,
            status="TILTED",
            message="Visage trop incliné — regardez droit devant vous",
            brightness=brightness,
            face_ratio=face_ratio,
            pitch_deg=pitch_deg,
        )

    # 5. Centrage horizontal
    nose_x = landmarks[config.PITCH_NOSE_TIP].x
    if nose_x < 0.20 or nose_x > 0.80:
        return QualityResult(
            ok=False,
            status="OFF_CENTER",
            message="Visage trop excentré — recentrez-vous",
            brightness=brightness,
            face_ratio=face_ratio,
            pitch_deg=pitch_deg,
        )

    return QualityResult(
        ok=True,
        status="OK",
        message="Visage détecté ✓",
        brightness=brightness,
        face_ratio=face_ratio,
        pitch_deg=pitch_deg,
    )


# ---------------------------------------------------------------------------
# Fonctions auxiliaires internes
# ---------------------------------------------------------------------------


def _estimate_face_ratio(
    landmarks: list[mp.framework.formats.landmark_pb2.NormalizedLandmark],
    image_height: int,
) -> float:
    """
    Estime la hauteur du visage en fraction de la hauteur de l'image.

    Utilise la distance entre le point du front (10) et le menton (152).
    """
    y_top = landmarks[config.PITCH_FOREHEAD].y
    y_bottom = landmarks[config.PITCH_CHIN].y
    return abs(y_bottom - y_top)


def _estimate_brightness(
    frame: np.ndarray,
    landmarks: list[mp.framework.formats.landmark_pb2.NormalizedLandmark],
    h: int,
    w: int,
) -> float:
    """
    Estime la luminosité moyenne dans la région du visage.

    Convertit en niveaux de gris et calcule la moyenne sur une zone
    délimitée par les points extremes du visage.
    """
    ys = [lm.y for lm in landmarks]
    xs = [lm.x for lm in landmarks]
    y1 = max(0, int(min(ys) * h))
    y2 = min(h, int(max(ys) * h))
    x1 = max(0, int(min(xs) * w))
    x2 = min(w, int(max(xs) * w))

    region = frame[y1:y2, x1:x2]
    if region.size == 0:
        return 0.0
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def _estimate_pitch_deg(
    landmarks: list[mp.framework.formats.landmark_pb2.NormalizedLandmark],
    image_height: int,
) -> float:
    """
    Estime l'inclinaison avant/arrière de la tête (pitch) en degrés.

    Méthode simple : compare la position Y du nez et du menton normalisée
    par la hauteur du visage. Positif = tête penchée en avant (menton bas).
    Zéro = posture neutre.
    """
    nose_y = landmarks[config.PITCH_NOSE_TIP].y
    chin_y = landmarks[config.PITCH_CHIN].y
    forehead_y = landmarks[config.PITCH_FOREHEAD].y

    face_height = abs(chin_y - forehead_y)
    if face_height < 1e-6:
        return 0.0

    # Position relative du nez dans la hauteur du visage (0.5 = centre)
    nose_rel = (nose_y - forehead_y) / face_height
    # Déviation par rapport à la position neutre (~0.55)
    deviation = nose_rel - 0.55
    # Mise à l'échelle empirique vers des degrés approximatifs
    return float(deviation * 90.0)
