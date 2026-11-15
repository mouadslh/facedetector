"""
Script d'entraînement d'un classificateur ML léger (option).

Entraîne un RandomForest sur les features EAR/MAR/pitch/PERCLOS
extraites d'une session enregistrée.

Utilisation :
    python scripts/train_classifier.py --data data/export.csv --output data/classifier.pkl

NOTE : Ce script est optionnel et n'est pas requis pour le fonctionnement de DrowsiGuard.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Implémentation à venir (Étape 8 optionnelle)
def main() -> None:
    print("train_classifier.py — Étape 8 (optionnelle). Non implémenté pour l'instant.")


if __name__ == "__main__":
    main()
