"""
Script d'évaluation de DrowsiGuard sur des vidéos annotées.

Mesure : précision, rappel, F1 et FPS moyens.

Utilisation :
    python scripts/evaluate.py --video path/to/video.mp4 --labels path/to/labels.csv

Format du fichier labels.csv :
    frame_idx,label  (label : 0=normal, 1=vigilance, 2=danger)
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drowsiguard.pipeline import Pipeline
from drowsiguard.profile import load_profile
from drowsiguard.state import AlertLevel


def load_labels(path: Path) -> dict[int, int]:
    """Charge les étiquettes frame_idx → label depuis un CSV."""
    labels: dict[int, int] = {}
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels[int(row["frame_idx"])] = int(row["label"])
    return labels


def level_to_int(level: AlertLevel) -> int:
    """Convertit AlertLevel en entier pour la comparaison."""
    return {AlertLevel.NORMAL: 0, AlertLevel.VIGILANCE: 1, AlertLevel.DANGER: 2}[level]


def evaluate(video_path: Path, labels: dict[int, int]) -> None:
    """Lance l'évaluation sur la vidéo."""
    profile = load_profile()
    if profile is None:
        print("Aucun profil calibré trouvé. Lancez d'abord l'application et calibrez.")
        sys.exit(1)

    pipeline = Pipeline()
    pipeline.load_existing_profile()

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Impossible d'ouvrir la vidéo : {video_path}")
        sys.exit(1)

    y_true, y_pred = [], []
    frame_idx = 0
    fps_times = []

    print(f"Évaluation de {video_path.name}…")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        t0 = time.time()
        ts = frame_idx / max(cap.get(cv2.CAP_PROP_FPS), 1.0)
        _, status = pipeline.process(frame, timestamp=ts)
        fps_times.append(time.time() - t0)

        if frame_idx in labels and status.state_result is not None:
            y_true.append(labels[frame_idx])
            y_pred.append(level_to_int(status.state_result.level))

        frame_idx += 1

    cap.release()
    pipeline.close()

    if not y_true:
        print("Aucune frame annotée traitée.")
        return

    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred)

    # Calculs par classe
    print("\n=== Rapport d'évaluation ===")
    print(f"Frames évaluées : {len(y_true)}")
    print(f"FPS moyen       : {1.0 / max(np.mean(fps_times), 1e-6):.1f}")
    print()

    for cls, name in [(0, "Normal"), (1, "Vigilance"), (2, "Danger")]:
        tp = int(np.sum((y_true_np == cls) & (y_pred_np == cls)))
        fp = int(np.sum((y_true_np != cls) & (y_pred_np == cls)))
        fn = int(np.sum((y_true_np == cls) & (y_pred_np != cls)))
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-6)
        print(f"[{name:10s}]  Précision={precision:.2f}  Rappel={recall:.2f}  F1={f1:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluation DrowsiGuard")
    parser.add_argument("--video", required=True, type=Path, help="Chemin de la vidéo")
    parser.add_argument("--labels", required=True, type=Path, help="Fichier CSV des étiquettes")
    args = parser.parse_args()
    labels = load_labels(args.labels)
    evaluate(args.video, labels)


if __name__ == "__main__":
    main()
