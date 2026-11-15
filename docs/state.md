# state.md — Documentation

## 1. Rôle

Accumule les mesures EAR/MAR/pitch frame par frame et produit à chaque appel un `StateResult` complet avec le score de fatigue, le niveau d'alerte et la liste des causes.

## 2. Ce que le fichier fait

1. Met à jour le buffer PERCLOS (deque glissante sur 60 s).
2. Mesure la durée de fermeture continue des yeux.
3. Détecte et compte les bâillements (avec durée minimale et cooldown).
4. Compte les micro-sommeils confirmés.
5. Calcule le score de fatigue pondéré (4 sous-scores normalisés).
6. Détermine le niveau : Normal / Vigilance / Danger.
7. Construit la liste `reasons` (causes lisibles).

## 3. Niveaux d'alerte

| Condition | Niveau |
|---|---|
| Score < `SCORE_VIGILANCE` ET aucune autre condition | Normal |
| Score ∈ [SCORE_VIGILANCE, SCORE_DANGER) | Vigilance |
| Score ≥ `SCORE_DANGER` | Danger |
| `closed_duration` > `DANGER_DURATION_S` | Danger (forcé) |
| Micro-sommeil confirmé | Danger (forcé) |
| PERCLOS > 25 % | Danger |
| PERCLOS ∈ [15 %, 25 %) | Vigilance |

## 4. Score de fatigue

```
score = (w_ear*ear_sub + w_perclos*perclos_sub + w_mar*mar_sub + w_head*head_sub) / total_w × 100
```
Lissage exponentiel α = 0.2 (≈ 5 frames de constante de temps).

## 5. API publique

| Méthode | Paramètres | Retour |
|---|---|---|
| `DrowsinessState(thresholds)` | seuils | — |
| `update(ear, mar, pitch, timestamp)` | mesures, horodatage injectable | `StateResult` |
| `reset(thresholds)` | nouveaux seuils | — |

## 6. Tests associés

`tests/test_state.py` — fermeture courte sans alerte, longue → Danger, PERCLOS, bâillements.
