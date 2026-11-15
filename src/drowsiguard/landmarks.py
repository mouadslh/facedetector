"""
Module landmarks — Détection des points de repère faciaux.

Responsabilités :
- Initialiser MediaPipe Face Mesh ou MediaPipe FaceLandmarker (Tasks API).
- Convertir une frame BGR en une liste de points de repère normalisés (ou None).
- Extraire les coordonnées en pixels pour les indices demandés.
"""

from __future__ import annotations

import logging
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path("assets/face_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
)


def _ensure_task_model() -> Path:
    """Télécharge le modèle FaceLandmarker si absent."""
    if not MODEL_PATH.exists():
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        import urllib.request
        logger.info("Téléchargement du modèle FaceLandmarker (%s)...", MODEL_URL)
        urllib.request.urlretrieve(MODEL_URL, str(MODEL_PATH))
    return MODEL_PATH


class FaceMeshDetector:
    """
    Détecte les 468 points de repère du visage avec MediaPipe.
    Supporte à la fois l'API legacy solutions.face_mesh et la nouvelle API tasks.vision.

    Parameters
    ----------
    max_num_faces :
        Nombre maximal de visages à détecter simultanément (1 pour la surveillance).
    refine_landmarks :
        Active les points de repère affinés (iris).
    min_detection_confidence :
        Seuil de confiance pour la détection initiale.
    min_tracking_confidence :
        Seuil de confiance pour le suivi entre les frames.
    """

    def __init__(
        self,
        max_num_faces: int = 1,
        refine_landmarks: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self._use_tasks_api = False

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
            self._mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                max_num_faces=max_num_faces,
                refine_landmarks=refine_landmarks,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
        else:
            # API moderne MediaPipe Tasks (0.10.x+)
            self._use_tasks_api = True
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            model_file = _ensure_task_model()
            base_options = python.BaseOptions(model_asset_path=str(model_file))
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=max_num_faces,
                min_face_detection_confidence=min_detection_confidence,
                min_face_presence_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._face_landmarker = vision.FaceLandmarker.create_from_options(options)

    def detect(self, frame: np.ndarray) -> list[object] | None:
        """
        Détecte les points de repère du premier visage dans la frame.

        Parameters
        ----------
        frame :
            Image BGR (uint8, H×W×3).

        Returns
        -------
        list[NormalizedLandmark] | None
            Liste de 468+ points normalisés (x, y, z ∈ [0, 1]) ou None si
            aucun visage n'est détecté.
        """
        if self._use_tasks_api:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._face_landmarker.detect(mp_image)
            if not result.face_landmarks:
                return None
            return list(result.face_landmarks[0])
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = self._face_mesh.process(rgb)
            if not results.multi_face_landmarks:
                return None
            return list(results.multi_face_landmarks[0].landmark)

    def get_pixels(
        self,
        landmarks: list[object],
        indices: list[int],
        frame_shape: tuple[int, int],
    ) -> np.ndarray:
        """
        Convertit des indices de points de repère en coordonnées pixel.

        Parameters
        ----------
        landmarks :
            Liste complète des points normalisés.
        indices :
            Indices des points à extraire.
        frame_shape :
            (hauteur, largeur) de la frame.

        Returns
        -------
        np.ndarray
            Tableau (N, 2) de coordonnées (x, y) en pixels, dtype float32.
        """
        h, w = frame_shape[:2]
        pts = np.array(
            [[landmarks[i].x * w, landmarks[i].y * h] for i in indices],
            dtype=np.float32,
        )
        return pts

    def close(self) -> None:
        """Libère les ressources MediaPipe."""
        if self._use_tasks_api:
            if hasattr(self, "_face_landmarker"):
                self._face_landmarker.close()
        else:
            if hasattr(self, "_face_mesh"):
                self._face_mesh.close()

    def __enter__(self) -> "FaceMeshDetector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
