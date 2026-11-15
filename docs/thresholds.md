# thresholds.md — Documentation

## 1. Rôle
Dérive tous les seuils de détection à partir du `UserProfile` et du niveau de sensibilité. Aucun seuil absolu.

## 2. Formules

```
ear_close  = ear_closed + (EAR_CLOSE_RATIO × mod) × (ear_open - ear_closed)
ear_drowsy = ear_closed + (EAR_DROWSY_RATIO × mod) × (ear_open - ear_closed)
mar_yawn   = mar_rest   + (MAR_YAWN_RATIO × mod)   × (mar_yawn - mar_rest)
pitch_fwd  = pitch_neutral + (HEAD_PITCH_RATIO × mod) × max_amplitude
```

`mod` = `SENSITIVITY_MODIFIERS[sensitivity]`

## 3. API publique

| Fonction | Paramètres | Retour |
|---|---|---|
| `derive_thresholds(profile, sensitivity)` | UserProfile, str | `Thresholds` |

## 4. Thresholds (dataclass)

`ear_close`, `ear_drowsy`, `mar_yawn`, `pitch_forward`, `pitch_backward`, `ear_open_ref`, `mar_rest_ref`, `pitch_neutral_ref`

## 5. Tests associés

`tests/test_thresholds.py`
