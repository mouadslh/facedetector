"""
Module camera — Ouverture automatique de la webcam.

Responsabilités :
- Détecter et ouvrir la première webcam disponible (indices 0, 1, 2).
- Lire les frames (images) en temps réel.
- Libérer proprement la ressource caméra.
- Fournir des messages d'erreur clairs en cas d'échec (permissions macOS,
  caméra occupée par une autre application).
"""

from __future__ import annotations

import os
import cv2
import numpy as np

# Laisser OpenCV déclencher la demande d'autorisation webcam de macOS.
os.environ.setdefault("OPENCV_AVFOUNDATION_SKIP_AUTH", "0")

from drowsiguard import config


class CameraError(Exception):
    """Levée quand aucune caméra n'est disponible ou ne peut être ouverte."""


class CameraCapture:
    """
    Gère le cycle de vie d'une webcam (ouverture, lecture, libération).

    Parameters
    ----------
    candidates :
        Liste ordonnée d'indices à tester. Par défaut : config.CAMERA_CANDIDATES.
    width :
        Largeur souhaitée en pixels. Par défaut : config.CAMERA_WIDTH.
    height :
        Hauteur souhaitée en pixels. Par défaut : config.CAMERA_HEIGHT.
    fps :
        FPS cible. Par défaut : config.CAMERA_FPS.
    """

    def __init__(
        self,
        candidates: list[int] | None = None,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
        fps: int = config.CAMERA_FPS,
    ) -> None:
        self._candidates = candidates if candidates is not None else config.CAMERA_CANDIDATES
        self._width = width
        self._height = height
        self._fps = fps
        self._cap: cv2.VideoCapture | None = None
        self._index: int = -1

    # ------------------------------------------------------------------
    # Ouverture
    # ------------------------------------------------------------------

    def open(self) -> int:
        """
        Ouvre la première webcam disponible parmi les candidats.

        Returns
        -------
        int
            Index de la caméra ouverte avec succès.

        Raises
        ------
        CameraError
            Si aucune caméra ne peut être ouverte.
        """
        for idx in self._candidates:
            for api_pref in [cv2.CAP_ANY, getattr(cv2, "CAP_AVFOUNDATION", cv2.CAP_ANY)]:
                cap = cv2.VideoCapture(idx, api_pref)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
                    cap.set(cv2.CAP_PROP_FPS, self._fps)
                    self._cap = cap
                    self._index = idx
                    return idx
                cap.release()

        raise CameraError(
            "Aucune webcam disponible.\n\n"
            "Vérifiez :\n"
            "  • Réglages Système > Confidentialité > Caméra → autoriser Terminal / votre app.\n"
            "  • Qu'aucune autre application n'utilise la caméra (FaceTime, Zoom…).\n"
            "  • Que la caméra est bien connectée (USB externe)."
        )

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    def read(self) -> tuple[bool, np.ndarray | None]:
        """
        Lit la prochaine frame de la caméra.

        Returns
        -------
        tuple[bool, np.ndarray | None]
            (succès, image BGR) ou (False, None) si la lecture échoue.
        """
        if self._cap is None:
            return False, None
        ret, frame = self._cap.read()
        if not ret:
            return False, None
        return True, frame

    # ------------------------------------------------------------------
    # Libération
    # ------------------------------------------------------------------

    def release(self) -> None:
        """Libère la ressource caméra proprement."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self._index = -1

    # ------------------------------------------------------------------
    # Propriétés
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        """Retourne True si la caméra est ouverte."""
        return self._cap is not None and self._cap.isOpened()

    @property
    def index(self) -> int:
        """Index de la caméra active (-1 si aucune)."""
        return self._index

    @property
    def actual_width(self) -> int:
        """Largeur réelle de la caméra (peut différer de la cible)."""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def actual_height(self) -> int:
        """Hauteur réelle de la caméra (peut différer de la cible)."""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # ------------------------------------------------------------------
    # Gestionnaire de contexte
    # ------------------------------------------------------------------

    def __enter__(self) -> "CameraCapture":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
