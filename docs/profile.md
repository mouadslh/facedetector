# profile.md — Documentation

## 1. Rôle
Définit `UserProfile` (dataclass) et gère la sauvegarde/chargement JSON du profil calibré.

## 2. UserProfile

| Champ | Type | Signification |
|---|---|---|
| `ear_open` | float | EAR moyen yeux ouverts (phase 1) |
| `ear_closed` | float | EAR moyen yeux fermés (phase 2) |
| `mar_rest` | float | MAR bouche au repos (phase 1) |
| `mar_yawn` | float | MAR pendant un bâillement (phase 3) |
| `pitch_neutral` | float | Pitch en posture neutre (phase 1) |
| `calibration_timestamp` | str | ISO 8601 |
| `sensitivity` | str | Sensibilité mémorisée |

## 3. API publique

| Fonction | Paramètres | Retour |
|---|---|---|
| `save_profile(profile, path)` | UserProfile, Path | — |
| `load_profile(path)` | Path | `UserProfile\|None` |

## 4. Validation au chargement

- `ear_closed < ear_open` ET écart ≥ `CALIB_EAR_MIN_DELTA`
- `mar_yawn > mar_rest` ET écart ≥ `CALIB_MAR_MIN_DELTA`
- Profil invalide → retourne `None` (recalibration requise)
