# scripts.md — Documentation

## generate_sounds.py

Génère `assets/alert_low.wav` (440 Hz, 0.5 s) et `assets/alert_high.wav` (880 Hz, double bip) avec NumPy + scipy.io.wavfile.

```bash
python scripts/generate_sounds.py
```

## evaluate.py

Évalue DrowsiGuard sur une vidéo annotée.

```bash
python scripts/evaluate.py --video chemin/video.mp4 --labels chemin/labels.csv
```

**Format labels.csv** : `frame_idx,label` (0=Normal, 1=Vigilance, 2=Danger)

**Sorties** : Précision, Rappel, F1 par classe + FPS moyen.

## train_classifier.py

Squelette pour l'entraînement ML optionnel (Étape 8). Non implémenté.
