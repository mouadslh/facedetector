# quality.md — Documentation

## 1. Rôle
Vérifie la qualité de la frame avant toute mesure. Retourne un `QualityResult` avec `ok=True` uniquement si toutes les conditions sont réunies.

## 2. Contrôles effectués (dans l'ordre)

1. **Visage présent** : `landmarks` is not None → sinon `NO_FACE`
2. **Taille** : hauteur du visage (front→menton) ≥ `QUALITY_MIN_FACE_RATIO` × hauteur image → sinon `TOO_FAR`
3. **Luminosité** : moyenne de la région du visage ∈ [MIN_BRIGHTNESS, MAX_BRIGHTNESS] → sinon `TOO_DARK` / `TOO_BRIGHT`
4. **Inclinaison** : |pitch_deg| ≤ seuil (plus strict en mode calibration) → sinon `TILTED`
5. **Centrage** : nez.x ∈ [0.20, 0.80] → sinon `OFF_CENTER`

## 3. API publique

| Fonction | Paramètres | Retour |
|---|---|---|
| `check_quality(frame, landmarks, calibration_mode)` | image, landmarks, bool | `QualityResult` |

## 4. Paramètres de config.py

`QUALITY_MIN_FACE_RATIO`, `QUALITY_MIN_BRIGHTNESS`, `QUALITY_MAX_BRIGHTNESS`, `QUALITY_MAX_PITCH_DEG`, `QUALITY_MAX_PITCH_DEG_CALIB`
