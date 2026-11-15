# calibration.md — Documentation

## 1. Rôle

Conduit l'utilisateur à travers 3 phases de mesure guidées pour établir son profil personnel.
Produit un `UserProfile` cohérent et validé, ou déclenche un `FAILED` avec un message explicatif.

## 2. Machine à états

```
WAITING_FACE → PHASE_OPEN → PHASE_CLOSED → PHASE_YAWN → DONE
                                                        ↘ FAILED → WAITING_FACE (reset)
```

| État | Déclencheur de sortie |
|---|---|
| `WAITING_FACE` | Visage stable détecté pendant ≥ `CALIB_STABILIZE_S` |
| `PHASE_OPEN` | Durée ≥ `CALIB_PHASE_OPEN_S` ET ≥ 5 échantillons valides |
| `PHASE_CLOSED` | Durée ≥ `CALIB_PHASE_CLOSED_S` ET ≥ 3 valeurs EAR basses |
| `PHASE_YAWN` | Durée ≥ `CALIB_PHASE_YAWN_S` |
| `DONE` | Profil validé par `_is_valid` |
| `FAILED` | Profil incohérent ou données insuffisantes |

## 3. API publique

| Méthode | Paramètres | Retour | Effets de bord |
|---|---|---|---|
| `CalibrationEngine(on_done)` | callback optionnel | — | Appelle `on_done(profile)` à `DONE` |
| `update(ear, mar, pitch, face_ok, timestamp)` | mesures courantes | `CalibrationStatus` | Met à jour l'état interne |
| `reset()` | — | — | Retour à `WAITING_FACE`, vide les buffers |
| `state` | — | `CalibrationState` | — |
| `profile` | — | `UserProfile \| None` | — |

## 4. Paramètres de config.py

`CALIB_PHASE_OPEN_S`, `CALIB_PHASE_CLOSED_S`, `CALIB_PHASE_YAWN_S`, `CALIB_STABILIZE_S`, `CALIB_EAR_MIN_DELTA`, `CALIB_MAR_MIN_DELTA`, `CALIB_OUTLIER_TRIM`

## 5. Validation

- `EAR_closed < EAR_open` avec écart ≥ `CALIB_EAR_MIN_DELTA`
- `MAR_yawn > MAR_rest` avec écart ≥ `CALIB_MAR_MIN_DELTA`

## 6. Robustesse

- Clignements ignorés en phase 1 (EAR trop bas = exclu du buffer)
- Médiane + winsorisation à 10 % sur chaque buffer
- Détection automatique de la fermeture en phase 2 (chute de l'EAR, pas seulement un minuteur)
- Perte du visage pendant la calibration → retour à `WAITING_FACE`
