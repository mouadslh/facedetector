# metrics.py — Documentation

## 1. Rôle

Calcule les métriques faciales à partir des coordonnées pixel des points de repère.
Module de calcul pur : **aucune dépendance** vers d'autres modules DrowsiGuard.
Toutes les divisions par zéro sont protégées.

## 2. Ce que le fichier fait

1. `eye_aspect_ratio` : reçoit 2 tableaux de 6 points (œil droit, œil gauche), applique la formule EAR et retourne la moyenne des deux yeux.
2. `_single_eye_ear` : calcule l'EAR d'un œil (fonction interne).
3. `mouth_aspect_ratio` : reçoit 4 points (haut, bas, gauche, droite), retourne MAR = vertical / horizontal.
4. `head_pitch` : reçoit 3 points (nez, menton, front), retourne la déviation normalisée par rapport à la position neutre (≈ 0.55).

## 3. Entrées / Sorties

| Fonction | Entrée | Sortie | Unité |
|---|---|---|---|
| `eye_aspect_ratio` | 2× `ndarray(6,2)` float | float | sans dimension [0, 0.5] |
| `mouth_aspect_ratio` | `ndarray(4,2)` float | float | sans dimension [0, 1] |
| `head_pitch` | 3× `ndarray(2,)` float | float | normalisé (≈ 0 neutre) |

## 4. API publique

| Fonction | Paramètres | Retour | Effets de bord |
|---|---|---|---|
| `eye_aspect_ratio(right, left)` | 2 tableaux (6,2) | float | Aucun |
| `mouth_aspect_ratio(pts)` | tableau (4,2) | float | Aucun |
| `head_pitch(nose, chin, forehead)` | 3 tableaux (2,) | float | Aucun |

## 5. Dépendances

- **Utilise** : `numpy` uniquement
- **Utilisé par** : `pipeline.py`, `calibration.py`, `quality.py` (indirectement)

## 6. Paramètres de config.py concernés

- `RIGHT_EYE_INDICES`, `LEFT_EYE_INDICES` : indices passés par `pipeline.py`
- `MOUTH_INDICES` : idem
- `PITCH_NOSE_TIP`, `PITCH_CHIN`, `PITCH_FOREHEAD` : idem

## 7. Cas limites

- Dénominateur nul (distance horizontale = 0) → retourne 0.0
- Hauteur du visage nulle → `head_pitch` retourne 0.0

## 8. Exemple

```python
import numpy as np
from drowsiguard.metrics import eye_aspect_ratio

right = np.array([[0,0],[20,-10],[40,-10],[60,0],[40,10],[20,10]], dtype=float)
left  = np.array([[0,0],[20,-10],[40,-10],[60,0],[40,10],[20,10]], dtype=float)
ear = eye_aspect_ratio(right, left)  # ≈ 0.333
```

## 9. Tests associés

`tests/test_metrics.py` — classes `TestEyeAspectRatio`, `TestMouthAspectRatio`, `TestHeadPitch`.

## 10. Limites connues

- `head_pitch` est une estimation empirique (pas une homographie 3D).
- L'EAR peut être légèrement faussé par une très forte inclinaison de la tête (> 30°).
