"""
Module thresholds — Dérivation des seuils personnalisés.

Responsabilités :
- Calculer tous les seuils de détection à partir du profil personnel et de la sensibilité.
- Aucun seuil absolu n'est utilisé : tout est relatif aux valeurs calibrées.
- Exposer une dataclass Thresholds utilisée par state.py et adaptive.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from drowsiguard import config
from drowsiguard.profile import UserProfile


@dataclass
class Thresholds:
    """
    Seuils de détection dérivés du profil personnel.

    Tous les seuils sont en unités naturelles (même échelle que EAR/MAR/pitch).
    """

    ear_close: float
    """EAR en dessous duquel l'œil est considéré fermé."""

    ear_drowsy: float
    """EAR en dessous duquel l'œil est considéré mi-clos (somnolence légère)."""

    mar_yawn: float
    """MAR au-dessus duquel la bouche est considérée en bâillement."""

    pitch_forward: float
    """Pitch au-delà duquel la tête est considérée tombante (vers l'avant)."""

    pitch_backward: float
    """Pitch en deçà duquel la tête est considérée trop relevée."""

    # Valeurs du profil mémorisées pour les graphiques
    ear_open_ref: float
    mar_rest_ref: float
    pitch_neutral_ref: float


def derive_thresholds(
    profile: UserProfile,
    sensitivity: str = "Normale",
) -> Thresholds:
    """
    Dérive les seuils à partir du profil et de la sensibilité.

    Formules :
        ear_close  = ear_closed + r_eye_close * (ear_open - ear_closed)
        ear_drowsy = ear_closed + r_eye_drowsy * (ear_open - ear_closed)
        mar_yawn   = mar_rest   + r_mouth      * (mar_yawn  - mar_rest)
        pitch_fwd  = pitch_neutral + r_pitch   * max_pitch_amplitude

    Les ratios r_* viennent de config.py et sont modulés par le modificateur
    de sensibilité.

    Parameters
    ----------
    profile :
        Profil utilisateur calibré.
    sensitivity :
        Niveau de sensibilité : "Basse", "Normale" ou "Haute".

    Returns
    -------
    Thresholds
        Seuils personnalisés prêts à l'emploi.
    """
    mod = config.SENSITIVITY_MODIFIERS.get(sensitivity, 1.0)

    ear_range = profile.ear_open - profile.ear_closed
    mar_range = profile.mar_yawn - profile.mar_rest

    # Seuil de fermeture : plus le ratio est bas, plus le seuil est strict
    r_close = config.EAR_CLOSE_RATIO * mod
    ear_close = profile.ear_closed + r_close * ear_range

    # Seuil de somnolence légère (mi-clos)
    r_drowsy = config.EAR_DROWSY_RATIO * mod
    ear_drowsy = profile.ear_closed + r_drowsy * ear_range

    # S'assurer que ear_drowsy >= ear_close (cohérence)
    ear_drowsy = max(ear_drowsy, ear_close + 0.01)

    # Seuil de bâillement (en sensibilité haute, un bâillement plus petit déclenche)
    r_mouth = config.MAR_YAWN_RATIO / mod
    mar_yawn_thr = profile.mar_rest + r_mouth * mar_range

    # Seuil de chute de tête (en sensibilité haute, une inclinaison moindre déclenche)
    max_amplitude = 0.30  # ≈ 27° en unité normalisée
    r_pitch = config.HEAD_PITCH_RATIO / mod
    pitch_forward = profile.pitch_neutral + r_pitch * max_amplitude
    pitch_backward = profile.pitch_neutral - r_pitch * max_amplitude * 0.5

    return Thresholds(
        ear_close=ear_close,
        ear_drowsy=ear_drowsy,
        mar_yawn=mar_yawn_thr,
        pitch_forward=pitch_forward,
        pitch_backward=pitch_backward,
        ear_open_ref=profile.ear_open,
        mar_rest_ref=profile.mar_rest,
        pitch_neutral_ref=profile.pitch_neutral,
    )
