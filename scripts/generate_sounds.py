"""
Script de génération des sons d'alarme.

Génère deux fichiers WAV avec NumPy + scipy :
  - assets/alert_low.wav  : bip grave (440 Hz) pour le niveau Vigilance
  - assets/alert_high.wav : bip aigu  (880 Hz) pour le niveau Danger

Utilisation :
    python scripts/generate_sounds.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wavfile

# Ajouter src/ au chemin
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from drowsiguard import config

ASSETS_DIR = Path(__file__).parent.parent / "assets"
SAMPLE_RATE = 44100


def _generate_beep(
    frequency: int,
    duration_s: float,
    sample_rate: int = SAMPLE_RATE,
    amplitude: float = 0.6,
) -> np.ndarray:
    """
    Génère un bip sinusoïdal avec enveloppe ADSR simple (attaque + déclin).

    Parameters
    ----------
    frequency :
        Fréquence en Hz.
    duration_s :
        Durée en secondes.
    sample_rate :
        Fréquence d'échantillonnage.
    amplitude :
        Amplitude maximale [0, 1].

    Returns
    -------
    np.ndarray
        Signal audio (int16).
    """
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    signal = amplitude * np.sin(2.0 * np.pi * frequency * t)

    # Enveloppe : attaque 5 ms, déclin 10 % de la durée
    attack_n = int(0.005 * sample_rate)
    decay_n = int(0.10 * len(signal))
    envelope = np.ones(len(signal))
    if attack_n > 0:
        envelope[:attack_n] = np.linspace(0, 1, attack_n)
    if decay_n > 0:
        envelope[-decay_n:] = np.linspace(1, 0, decay_n)
    signal *= envelope

    return (signal * 32767).astype(np.int16)


def main() -> None:
    """Génère et sauvegarde les deux fichiers sons."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Son Vigilance (grave)
    low_path = ASSETS_DIR / "alert_low.wav"
    low_signal = _generate_beep(config.ALARM_FREQ_LOW, config.ALARM_DURATION_LOW_S)
    wavfile.write(str(low_path), SAMPLE_RATE, low_signal)
    print(f"✅ Généré : {low_path}")

    # Son Danger (aigu, double bip)
    high_path = ASSETS_DIR / "alert_high.wav"
    silence = np.zeros(int(0.05 * SAMPLE_RATE), dtype=np.int16)
    bip = _generate_beep(config.ALARM_FREQ_HIGH, config.ALARM_DURATION_HIGH_S)
    high_signal = np.concatenate([bip, silence, bip])
    wavfile.write(str(high_path), SAMPLE_RATE, high_signal)
    print(f"✅ Généré : {high_path}")

    print("\nSons générés avec succès dans assets/")
    print("Vous pouvez maintenant lancer : streamlit run app.py")


if __name__ == "__main__":
    main()
