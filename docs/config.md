# config.py — Documentation

## Rôle

Fichier de configuration central. Contient **uniquement** des ratios, durées, indices et poids.  
**Aucun seuil absolu de détection** n'est codé ici.

---

## Paramètres

### Indices de points de repère

| Nom | Valeur | Rôle |
|---|---|---|
| `RIGHT_EYE_INDICES` | `[33,160,158,133,153,144]` | Points de l'œil droit pour EAR |
| `LEFT_EYE_INDICES` | `[362,385,387,263,373,380]` | Points de l'œil gauche pour EAR |
| `MOUTH_INDICES` | `[13,14,78,308]` | Points [haut,bas,gauche,droite] pour MAR |
| `PITCH_NOSE_TIP` | `1` | Bout du nez pour le pitch |
| `PITCH_CHIN` | `152` | Menton pour le pitch |
| `PITCH_FOREHEAD` | `10` | Milieu du front pour le pitch |

### Ratios de détection

| Nom | Valeur | Unité | Rôle | ↑ hausse | ↓ baisse |
|---|---|---|---|---|---|
| `EAR_CLOSE_RATIO` | `0.40` | sans dimension | Position du seuil de fermeture entre EAR_closed et EAR_open | Seuil plus haut → détecte plus facilement | Moins sensible |
| `EAR_DROWSY_RATIO` | `0.60` | sans dimension | Position du seuil de somnolence légère | Détecte plus tôt les yeux mi-clos | Moins sensible |
| `MAR_YAWN_RATIO` | `0.45` | sans dimension | Position du seuil de bâillement | Plus facilement déclenché | Moins facilement |
| `HEAD_PITCH_RATIO` | `0.50` | sans dimension | Position du seuil de chute de tête | Détecte les inclinaisons moindres | Tolère plus d'inclinaison |

### Modificateurs de sensibilité

| Niveau | Modificateur | Effet |
|---|---|---|
| Basse | 1.20 | Seuils plus permissifs → moins d'alertes |
| Normale | 1.00 | Référence |
| Haute | 0.80 | Seuils plus stricts → plus d'alertes |

### Durées

| Nom | Valeur | Unité | Rôle |
|---|---|---|---|
| `MICROSLEEP_DURATION_S` | `1.5` | s | Durée minimale pour un micro-sommeil |
| `DANGER_DURATION_S` | `2.5` | s | Durée avant le niveau Danger |
| `PERCLOS_WINDOW_S` | `60.0` | s | Fenêtre du PERCLOS |
| `YAWN_COOLDOWN_S` | `3.0` | s | Délai minimum entre deux bâillements |
| `YAWN_MIN_DURATION_S` | `0.5` | s | Durée minimale d'un bâillement |

### Calibration

| Nom | Valeur | Unité | Rôle |
|---|---|---|---|
| `CALIB_PHASE_OPEN_S` | `4.0` | s | Durée de la phase yeux ouverts |
| `CALIB_PHASE_CLOSED_S` | `2.0` | s | Durée de la phase yeux fermés |
| `CALIB_PHASE_YAWN_S` | `3.0` | s | Durée de la phase bâillement |
| `CALIB_STABILIZE_S` | `1.0` | s | Délai de stabilisation avant chaque phase |
| `CALIB_EAR_MIN_DELTA` | `0.04` | sans dimension | Écart minimal EAR_open - EAR_closed pour valider |
| `CALIB_MAR_MIN_DELTA` | `0.10` | sans dimension | Écart minimal MAR_yawn - MAR_rest pour valider |
| `CALIB_OUTLIER_TRIM` | `0.10` | fraction | % éliminé de chaque côté (winsorisation) |

### Score de fatigue

| Nom | Valeur | Rôle |
|---|---|---|
| `SCORE_WEIGHT_EAR` | `0.35` | Poids de la fermeture des yeux |
| `SCORE_WEIGHT_PERCLOS` | `0.30` | Poids du PERCLOS |
| `SCORE_WEIGHT_MAR` | `0.20` | Poids des bâillements |
| `SCORE_WEIGHT_HEAD` | `0.15` | Poids de la chute de tête |
| `SCORE_VIGILANCE` | `40.0` | Score → niveau Vigilance |
| `SCORE_DANGER` | `70.0` | Score → niveau Danger |

### Valeurs de repli (avant calibration uniquement)

| Nom | Valeur | Usage |
|---|---|---|
| `FALLBACK_EAR_OPEN` | `0.30` | EAR_open générique |
| `FALLBACK_EAR_CLOSED` | `0.15` | EAR_closed générique |
| `FALLBACK_MAR_REST` | `0.20` | MAR_rest générique |
| `FALLBACK_MAR_YAWN` | `0.60` | MAR_yawn générique |
| `FALLBACK_PITCH_NEUTRAL` | `0.0` | Pitch neutre générique |
