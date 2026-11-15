# Documentation DrowsiGuard — Index

Documentation complète du projet, un fichier par module.

---

## Index des modules

| Fichier | Module | Description |
|---|---|---|
| [architecture.md](architecture.md) | Architecture | Diagramme Mermaid du flux, règles de dépendance |
| [user_flow.md](user_flow.md) | Parcours utilisateur | Écran par écran, messages affichés |
| [config.md](config.md) | `config.py` | Tous les paramètres (nom, valeur, unité, rôle) |
| [camera.md](camera.md) | `camera.py` | Ouverture automatique de la webcam |
| [landmarks.md](landmarks.md) | `landmarks.py` | Détection des 468 points faciaux MediaPipe |
| [quality.md](quality.md) | `quality.py` | Contrôle qualité de la frame avant toute mesure |
| [metrics.md](metrics.md) | `metrics.py` | Fonctions pures EAR, MAR, head_pitch |
| [profile.md](profile.md) | `profile.py` | UserProfile + sauvegarde/chargement JSON |
| [calibration.md](calibration.md) | `calibration.py` | Machine à états de la calibration guidée |
| [thresholds.md](thresholds.md) | `thresholds.py` | Dérivation des seuils depuis le profil |
| [adaptive.md](adaptive.md) | `adaptive.py` | Adaptation lente de la ligne de base EAR |
| [state.md](state.md) | `state.py` | DrowsinessState : PERCLOS, score, niveau |
| [alarm.md](alarm.md) | `alarm.py` | Alarme sonore graduée non bloquante |
| [logger.md](logger.md) | `logger.py` | Journal SQLite + export CSV |
| [pipeline.md](pipeline.md) | `pipeline.py` | Orchestration complète du traitement |
| [ui.md](ui.md) | `ui/` | Composants Streamlit et graphiques Plotly |
| [app.md](app.md) | `app.py` | Point d'entrée Streamlit |
| [scripts.md](scripts.md) | `scripts/` | Outils auxiliaires (sons, évaluation, ML) |
| [tests.md](tests.md) | `tests/` | Tests pytest, cas couverts |
| [decisions.md](decisions.md) | Décisions | Choix architecturaux et leurs justifications |
