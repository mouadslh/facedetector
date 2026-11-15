# tests.md — Documentation

## Lancer les tests

```bash
pytest tests/ -v
```

## Fichiers de tests

| Fichier | Module testé | Cas couverts |
|---|---|---|
| `test_metrics.py` | `metrics.py` | EAR ouvert > fermé, valeurs limites, division par zéro, MAR, head_pitch |
| `test_thresholds.py` | `thresholds.py` | Deux profils → seuils différents, ordres, effet sensibilité |
| `test_calibration.py` | `calibration.py` | Séquence complète, valeurs aberrantes ignorées, profil incohérent rejeté, perte du visage, reset |
| `test_state.py` | `state.py` | Clignement court sans alerte, fermeture longue → Danger, PERCLOS, bâillement compté une fois |
| `test_adaptive.py` | `adaptive.py` | Suivi d'une baisse, non-dérive pendant fermeture, max_drift, reset |

## Principe

- **Aucune webcam requise** : toutes les données d'entrée sont synthétiques.
- **Timestamp injectable** : le temps est simulé avec `start_ts` et `dt`.
- **Données synthétiques** : fonctions utilitaires `_make_open_eye()`, `_run_frames()`, etc.

## Couverture cible

Tous les chemins critiques des modules `metrics`, `thresholds`, `calibration`, `state` et `adaptive`.
