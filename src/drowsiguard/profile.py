"""
Module profile — Profil personnel de l'utilisateur.

Responsabilités :
- Définir la dataclass UserProfile (valeurs mesurées à la calibration).
- Sauvegarder et charger le profil depuis data/profile.json.
- Valider la cohérence du profil lors du chargement.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

PROFILE_PATH = Path("data/profile.json")


@dataclass
class UserProfile:
    """
    Profil calibré de l'utilisateur.

    Toutes les valeurs sont mesurées sur CETTE personne pendant la calibration.
    Elles servent à calculer les seuils personnalisés dans thresholds.py.
    """

    ear_open: float
    """EAR moyen yeux ouverts (phase 1)."""

    ear_closed: float
    """EAR moyen yeux fermés (phase 2)."""

    mar_rest: float
    """MAR bouche au repos (phase 1)."""

    mar_yawn: float
    """MAR pendant un bâillement (phase 3)."""

    pitch_neutral: float
    """Pitch normalisé en posture neutre (phase 1)."""

    calibration_timestamp: str = ""
    """Horodatage ISO 8601 de la calibration."""

    sensitivity: str = "Normale"
    """Sensibilité mémorisée lors de la dernière calibration."""

    def is_valid(self) -> bool:
        """Retourne True si les valeurs calibrées sont physiquement cohérentes."""
        return (
            self.ear_open > self.ear_closed
            and self.mar_yawn > self.mar_rest
            and self.ear_open > 0
            and self.ear_closed >= 0
        )


def save_profile(profile: UserProfile, path: Path = PROFILE_PATH) -> None:
    """
    Sauvegarde le profil utilisateur dans un fichier JSON.

    Parameters
    ----------
    profile :
        Profil à sauvegarder.
    path :
        Chemin du fichier JSON (créé si absent).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
    logger.info("Profil sauvegardé : %s", path)


def load_profile(path: Path = PROFILE_PATH) -> UserProfile | None:
    """
    Charge le profil utilisateur depuis un fichier JSON.

    Parameters
    ----------
    path :
        Chemin du fichier JSON.

    Returns
    -------
    UserProfile | None
        Le profil chargé et validé, ou None si le fichier est absent ou invalide.
    """
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        profile = UserProfile(**data)
        if _is_valid(profile):
            return profile
        logger.warning("Profil chargé mais invalide : %s", data)
        return None
    except (json.JSONDecodeError, TypeError, KeyError) as exc:
        logger.error("Impossible de charger le profil : %s", exc)
        return None


def _is_valid(profile: UserProfile) -> bool:
    """
    Vérifie la cohérence minimale du profil.

    Returns
    -------
    bool
        True si le profil est utilisable.
    """
    from drowsiguard import config

    if profile.ear_closed >= profile.ear_open:
        return False
    if (profile.ear_open - profile.ear_closed) < config.CALIB_EAR_MIN_DELTA:
        return False
    if profile.mar_yawn <= profile.mar_rest:
        return False
    if (profile.mar_yawn - profile.mar_rest) < config.CALIB_MAR_MIN_DELTA:
        return False
    return True
