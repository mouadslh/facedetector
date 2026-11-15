# adaptive.md — Documentation

## 1. Rôle
Re-estime lentement `EAR_open` en conditions réelles pour compenser les changements de lumière ou de posture. Bloque l'adaptation pendant les fermetures prolongées.

## 2. Algorithme

1. Si `ear >= ear_close_threshold` → ajouter l'échantillon au buffer.
2. Purger les échantillons > `window_s` secondes.
3. Si ≥ 10 échantillons : calculer le percentile 90.
4. Clipper la cible dans `[ear_open_initial × (1-max_drift), ear_open_initial × (1+max_drift)]`.
5. Appliquer la cible avec vitesse limitée (`max_speed × dt`).

## 3. API publique

| Méthode | Paramètres | Retour |
|---|---|---|
| `AdaptiveBaseline(ear_open_initial, ear_close_threshold, ...)` | scalaires | — |
| `update(ear, timestamp)` | float, float | `float` (ear_open courant) |
| `reset(ear_open, ear_close_threshold)` | floats | — |
| `ear_open` | — | `float` |

## 4. Paramètres de config.py

`ADAPTIVE_WINDOW_S`, `ADAPTIVE_PERCENTILE`, `ADAPTIVE_MAX_SPEED`, `ADAPTIVE_MAX_DRIFT`

## 5. Tests associés

`tests/test_adaptive.py`
