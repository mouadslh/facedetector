"""
Module alarm — Alarme sonore graduée et non bloquante.

Responsabilités :
- Jouer un son d'alarme de niveau 1 (Vigilance) ou 2 (Danger).
- Utiliser un thread séparé pour ne pas bloquer la boucle vidéo.
- Respecter un cooldown entre deux alarmes du même niveau.
- Offrir une option muet.
- Ne jamais planter si l'audio est indisponible (fallback silencieux).
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Chemins des fichiers audio (générés par scripts/generate_sounds.py)
ASSETS_DIR = Path("assets")
SOUND_LOW = ASSETS_DIR / "alert_low.wav"
SOUND_HIGH = ASSETS_DIR / "alert_high.wav"


class AlarmManager:
    """
    Gestionnaire d'alarme sonore graduée.

    Parameters
    ----------
    muted :
        Si True, aucun son n'est émis.
    """

    def __init__(self, muted: bool = False) -> None:
        self._muted = muted
        self._pygame_ok = False
        self._sounds: dict[str, object] = {}
        self._lock = threading.Lock()
        self._last_played: dict[str, float] = {"low": 0.0, "high": 0.0}
        self._cooldowns: dict[str, float] = {}
        self._thread: threading.Thread | None = None

        self._afplay_ok = False
        self._init_audio()

    def _init_audio(self) -> None:
        """Initialise pygame.mixer ou détecte afplay sous macOS."""
        import shutil
        if shutil.which("afplay") is not None:
            self._afplay_ok = True

        try:
            import pygame
            pygame.mixer.init()
            self._pygame_ok = True
            self._load_sounds()
        except Exception as exc:
            logger.debug("Pygame indisponible, fallback afplay: %s", exc)
            self._pygame_ok = False

    def _load_sounds(self) -> None:
        """Charge les fichiers WAV si présents."""
        import pygame

        for key, path in [("low", SOUND_LOW), ("high", SOUND_HIGH)]:
            if path.exists():
                try:
                    self._sounds[key] = pygame.mixer.Sound(str(path))
                except Exception as exc:
                    logger.warning("Impossible de charger %s : %s", path, exc)
            else:
                logger.warning("Fichier son absent : %s — lancez scripts/generate_sounds.py", path)

    # ------------------------------------------------------------------
    # Interface publique
    # ------------------------------------------------------------------

    @property
    def muted(self) -> bool:
        """True si l'alarme est en mode muet."""
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        self._muted = value

    def alert_vigilance(self, timestamp: float | None = None) -> None:
        """
        Déclenche l'alarme de niveau Vigilance (son bas).

        Parameters
        ----------
        timestamp :
            Horodatage courant (injectable). Si None, utilise time.time().
        """
        self._trigger("low", timestamp)

    def alert_danger(self, timestamp: float | None = None) -> None:
        """
        Déclenche l'alarme de niveau Danger (son haut).

        Parameters
        ----------
        timestamp :
            Horodatage courant (injectable). Si None, utilise time.time().
        """
        self._trigger("high", timestamp)

    def stop(self) -> None:
        """Arrête toute alarme en cours."""
        if self._pygame_ok:
            try:
                import pygame
                pygame.mixer.stop()
            except Exception:
                pass

    def close(self) -> None:
        """Libère les ressources audio."""
        if self._pygame_ok:
            try:
                import pygame
                pygame.mixer.quit()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _trigger(self, level: str, timestamp: float | None) -> None:
        """Déclenche un son si le cooldown est écoulé et non muet."""
        if self._muted:
            return
        if not self._pygame_ok and not self._afplay_ok:
            return

        ts = timestamp if timestamp is not None else time.time()
        from drowsiguard import config

        cooldown = (
            config.ALARM_COOLDOWN_LOW_S if level == "low" else config.ALARM_COOLDOWN_HIGH_S
        )

        with self._lock:
            if ts - self._last_played.get(level, 0.0) < cooldown:
                return
            self._last_played[level] = ts

        # Jouer en arrière-plan
        sound_path = SOUND_LOW if level == "low" else SOUND_HIGH
        sound = self._sounds.get(level)
        t = threading.Thread(target=self._play, args=(sound, sound_path), daemon=True)
        t.start()

    def _play(self, sound: object, path: Path) -> None:
        """Joue le son dans un thread séparé (pygame ou afplay)."""
        if self._pygame_ok and sound is not None:
            try:
                sound.play()  # type: ignore[attr-defined]
                return
            except Exception as exc:
                logger.debug("Erreur lecture pygame : %s", exc)

        if self._afplay_ok and path.exists():
            try:
                import subprocess
                subprocess.run(
                    ["/usr/bin/afplay", str(path)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:
                logger.debug("Erreur lecture afplay : %s", exc)
