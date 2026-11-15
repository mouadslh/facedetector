# Architecture DrowsiGuard

## Flux de données

```mermaid
flowchart TD
    CAM[camera.py\nWebcam] --> LM[landmarks.py\nFace Mesh]
    LM --> QA[quality.py\nContrôle qualité]
    LM --> MX[metrics.py\nEAR / MAR / pitch]
    QA --> MX
    MX --> CAL[calibration.py\nMachine à états]
    MX --> STATE[state.py\nDrowsinessState]
    CAL --> PROF[profile.py\nUserProfile]
    PROF --> THR[thresholds.py\nDérivation des seuils]
    THR --> STATE
    MX --> ADAPT[adaptive.py\nLigne de base adaptative]
    ADAPT --> THR
    STATE --> ALARM[alarm.py\nAlarme sonore]
    STATE --> LOG[logger.py\nJournal SQLite]
    CAM --> PIPE[pipeline.py\nOrchestration]
    LM --> PIPE
    QA --> PIPE
    MX --> PIPE
    CAL --> PIPE
    STATE --> PIPE
    ALARM --> PIPE
    LOG --> PIPE
    PIPE --> APP[app.py\nStreamlit]
    APP --> UI[ui/\ncomponents + charts]
```

## Couches et règles de dépendance

| Couche | Modules | Règle |
|---|---|---|
| **Calcul pur** | `metrics.py` | Aucune dépendance interne DrowsiGuard |
| **Données** | `profile.py`, `config.py` | Aucune logique de détection |
| **Analyse** | `quality.py`, `calibration.py`, `thresholds.py`, `adaptive.py`, `state.py` | Dépend de calcul pur + données uniquement |
| **Effets** | `alarm.py`, `logger.py` | Dépend de state uniquement |
| **Orchestration** | `pipeline.py` | Dépend de tout sauf `ui/` et `app.py` |
| **Présentation** | `ui/`, `app.py` | Aucune logique métier — affichage uniquement |

## Règles absolues

1. `metrics.py` ne dépend d'aucun autre module DrowsiGuard.
2. `ui/components.py` et `ui/charts.py` ne contiennent **aucune logique de détection**.
3. `app.py` ne contient **aucune logique métier** — uniquement des appels à `pipeline.py` et `ui/`.
4. Toute logique métier est dans `src/drowsiguard/` — jamais dans `app.py`.
5. Le temps (`timestamp`) est toujours injectable pour les tests.
