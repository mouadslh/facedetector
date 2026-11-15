"""
Module metrics — Fonctions pures de calcul des métriques faciales.

Responsabilités :
- Calculer l'Eye Aspect Ratio (EAR) pour la détection de fermeture des yeux.
- Calculer le Mouth Aspect Ratio (MAR) pour la détection des bâillements.
- Estimer le pitch (inclinaison avant/arrière) de la tête.

Ce module ne dépend d'aucun autre module DrowsiGuard.
Toutes les divisions par zéro sont protégées.
"""

from __future__ import annotations

import numpy as np


def eye_aspect_ratio(
    right_eye_pts: np.ndarray,
    left_eye_pts: np.ndarray,
) -> float:
    """
    Calcule l'Eye Aspect Ratio (EAR) moyen des deux yeux.

    Formule par œil :
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    Les indices attendus pour chaque œil sont [p1, p2, p3, p4, p5, p6] :
    - Œil droit  : config.RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    - Œil gauche : config.LEFT_EYE_INDICES  = [362, 385, 387, 263, 373, 380]

    Parameters
    ----------
    right_eye_pts :
        Tableau (6, 2) de coordonnées pixel (x, y) de l'œil droit, dtype float.
    left_eye_pts :
        Tableau (6, 2) de coordonnées pixel (x, y) de l'œil gauche, dtype float.

    Returns
    -------
    float
        EAR moyen (≈ 0.30 yeux ouverts, ≈ 0.10 yeux fermés).
        Retourne 0.0 si le dénominateur est nul.
    """
    ear_right = _single_eye_ear(right_eye_pts)
    ear_left = _single_eye_ear(left_eye_pts)
    return (ear_right + ear_left) / 2.0


def _single_eye_ear(pts: np.ndarray) -> float:
    """
    Calcule l'EAR d'un seul œil.

    Parameters
    ----------
    pts :
        Tableau (6, 2) : [p1, p2, p3, p4, p5, p6].

    Returns
    -------
    float
        EAR de l'œil, 0.0 si dénominateur nul.
    """
    p1, p2, p3, p4, p5, p6 = pts
    vertical_1 = float(np.linalg.norm(p2 - p6))
    vertical_2 = float(np.linalg.norm(p3 - p5))
    horizontal = float(np.linalg.norm(p1 - p4))
    denominator = 2.0 * horizontal
    if denominator < 1e-6:
        return 0.0
    return (vertical_1 + vertical_2) / denominator


def mouth_aspect_ratio(mouth_pts: np.ndarray) -> float:
    """
    Calcule le Mouth Aspect Ratio (MAR).

    Formule :
        MAR = ||haut - bas|| / ||gauche - droite||

    Les indices attendus sont [haut, bas, gauche, droite] :
    - config.MOUTH_INDICES = [13, 14, 78, 308]

    Parameters
    ----------
    mouth_pts :
        Tableau (4, 2) de coordonnées pixel (x, y) [haut, bas, gauche, droite].

    Returns
    -------
    float
        MAR (≈ 0.20 bouche fermée, ≈ 0.70 grand bâillement).
        Retourne 0.0 si le dénominateur est nul.
    """
    top, bottom, left, right = mouth_pts
    vertical = float(np.linalg.norm(top - bottom))
    horizontal = float(np.linalg.norm(left - right))
    if horizontal < 1e-6:
        return 0.0
    return vertical / horizontal


def head_pitch(
    nose_tip: np.ndarray,
    chin: np.ndarray,
    forehead: np.ndarray,
) -> float:
    """
    Estime l'inclinaison avant/arrière de la tête (pitch) en unité normalisée.

    Méthode : position relative du bout du nez dans la hauteur du visage,
    soustraite de la position neutre (≈ 0.55).

    Parameters
    ----------
    nose_tip :
        Coordonnées (x, y) en pixels du bout du nez (point 1).
    chin :
        Coordonnées (x, y) en pixels du menton (point 152).
    forehead :
        Coordonnées (x, y) en pixels du milieu du front (point 10).

    Returns
    -------
    float
        Pitch normalisé (≈ 0 posture neutre, > 0 tête en avant, < 0 tête en arrière).
        Retourne 0.0 si la hauteur du visage est nulle.
    """
    face_height = float(np.abs(chin[1] - forehead[1]))
    if face_height < 1e-6:
        return 0.0
    nose_rel = float((nose_tip[1] - forehead[1]) / face_height)
    return nose_rel - 0.55
