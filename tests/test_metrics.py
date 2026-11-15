"""Tests du module metrics.py (fonctions pures, sans webcam)."""

from __future__ import annotations

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.metrics import eye_aspect_ratio, mouth_aspect_ratio, head_pitch


# ---------------------------------------------------------------------------
# Helpers : construction de points synthétiques
# ---------------------------------------------------------------------------


def _make_open_eye(width: float = 60.0, height: float = 15.0) -> np.ndarray:
    """
    Crée 6 points représentant un œil ouvert.

    p1 (coin gauche), p2, p3 (bord supérieur), p4 (coin droit), p5, p6 (bord inférieur)
    """
    return np.array([
        [0.0,      0.0],        # p1 : coin gauche
        [width/3,  -height],    # p2 : haut gauche
        [2*width/3,-height],    # p3 : haut droite
        [width,    0.0],        # p4 : coin droit
        [2*width/3, height],    # p5 : bas droite
        [width/3,  height],     # p6 : bas gauche
    ], dtype=np.float32)


def _make_closed_eye(width: float = 60.0) -> np.ndarray:
    """Crée 6 points représentant un œil fermé (hauteur quasi nulle)."""
    return np.array([
        [0.0,   0.0],
        [width/3, -0.5],
        [2*width/3, -0.5],
        [width, 0.0],
        [2*width/3, 0.5],
        [width/3,  0.5],
    ], dtype=np.float32)


def _make_mouth_closed(width: float = 50.0, height: float = 5.0) -> np.ndarray:
    """Points bouche fermée [haut, bas, gauche, droite]."""
    return np.array([
        [width/2,  -height/2],  # haut
        [width/2,   height/2],  # bas
        [0.0,       0.0],       # gauche
        [width,     0.0],       # droite
    ], dtype=np.float32)


def _make_mouth_open(width: float = 50.0, height: float = 30.0) -> np.ndarray:
    """Points bouche grande ouverte [haut, bas, gauche, droite]."""
    return np.array([
        [width/2, -height/2],
        [width/2,  height/2],
        [0.0,      0.0],
        [width,    0.0],
    ], dtype=np.float32)


# ---------------------------------------------------------------------------
# Tests EAR
# ---------------------------------------------------------------------------


class TestEyeAspectRatio:
    def test_open_eye_greater_than_closed(self):
        """EAR yeux ouverts doit être supérieur à EAR yeux fermés."""
        open_pts = _make_open_eye()
        closed_pts = _make_closed_eye()
        ear_open = eye_aspect_ratio(open_pts, open_pts)
        ear_closed = eye_aspect_ratio(closed_pts, closed_pts)
        assert ear_open > ear_closed, f"EAR_open={ear_open:.4f} devrait > EAR_closed={ear_closed:.4f}"

    def test_open_eye_value_range(self):
        """EAR yeux ouverts doit être dans [0.20, 0.50]."""
        pts = _make_open_eye(width=60, height=15)
        ear = eye_aspect_ratio(pts, pts)
        assert 0.20 <= ear <= 0.50, f"EAR_open inattendu : {ear}"

    def test_closed_eye_near_zero(self):
        """EAR yeux fermés doit être proche de 0."""
        pts = _make_closed_eye()
        ear = eye_aspect_ratio(pts, pts)
        assert ear < 0.05, f"EAR_closed devrait être < 0.05, obtenu : {ear}"

    def test_zero_width_protected(self):
        """Division par zéro (largeur nulle) doit retourner 0.0."""
        pts = np.zeros((6, 2), dtype=np.float32)
        ear = eye_aspect_ratio(pts, pts)
        assert ear == 0.0

    def test_asymmetric_eyes_averaged(self):
        """La moyenne des deux yeux est calculée correctement."""
        open_pts = _make_open_eye(width=60, height=15)
        closed_pts = _make_closed_eye(width=60)
        ear = eye_aspect_ratio(open_pts, closed_pts)
        ear_open = eye_aspect_ratio(open_pts, open_pts)
        ear_closed = eye_aspect_ratio(closed_pts, closed_pts)
        expected = (ear_open + ear_closed) / 2.0
        assert abs(ear - expected) < 1e-6


# ---------------------------------------------------------------------------
# Tests MAR
# ---------------------------------------------------------------------------


class TestMouthAspectRatio:
    def test_open_mouth_greater_than_closed(self):
        """MAR bouche ouverte > MAR bouche fermée."""
        closed = mouth_aspect_ratio(_make_mouth_closed())
        opened = mouth_aspect_ratio(_make_mouth_open())
        assert opened > closed, f"MAR_open={opened:.4f} devrait > MAR_closed={closed:.4f}"

    def test_zero_width_protected(self):
        """Division par zéro (largeur nulle) doit retourner 0.0."""
        pts = np.zeros((4, 2), dtype=np.float32)
        assert mouth_aspect_ratio(pts) == 0.0

    def test_closed_mouth_range(self):
        """MAR bouche fermée doit être < 0.30."""
        mar = mouth_aspect_ratio(_make_mouth_closed())
        assert mar < 0.30

    def test_open_mouth_range(self):
        """MAR grand bâillement doit être > 0.40."""
        mar = mouth_aspect_ratio(_make_mouth_open(height=30))
        assert mar > 0.40


# ---------------------------------------------------------------------------
# Tests head_pitch
# ---------------------------------------------------------------------------


class TestHeadPitch:
    def _make_neutral_points(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Points en posture neutre : nez à 55 % de la hauteur du visage."""
        forehead = np.array([320.0, 100.0])
        chin = np.array([320.0, 400.0])
        # nez à 55 % de la hauteur
        nose = np.array([320.0, 100.0 + 0.55 * 300.0])
        return nose, chin, forehead

    def test_neutral_near_zero(self):
        """Pitch en posture neutre doit être proche de 0."""
        nose, chin, forehead = self._make_neutral_points()
        p = head_pitch(nose, chin, forehead)
        assert abs(p) < 0.05, f"Pitch neutre inattendu : {p}"

    def test_head_forward_positive(self):
        """Tête penchée en avant (menton bas) → pitch positif."""
        forehead = np.array([320.0, 80.0])
        chin = np.array([320.0, 420.0])
        # nez plus bas que la position neutre
        nose = np.array([320.0, 80.0 + 0.70 * 340.0])
        p = head_pitch(nose, chin, forehead)
        assert p > 0.0, f"Pitch devrait être > 0 pour tête en avant, obtenu : {p}"

    def test_zero_face_height_protected(self):
        """Face de hauteur nulle → pitch = 0.0."""
        pt = np.array([0.0, 0.0])
        assert head_pitch(pt, pt, pt) == 0.0
