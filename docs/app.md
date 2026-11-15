# app.md — Documentation du Point d'Entrée

## 1. Rôle et Responsabilités

`app.py` orchestre l'interface utilisateur Streamlit de DrowsiGuard en mode large (`layout="wide"`). Il respecte scrupuleusement la séparation des responsabilités :
- **Aucune logique métier** (déléguée à `Pipeline`, `DrowsinessState`, `EventLogger`).
- Affichage temps réel fluide (vidéo à 30 FPS, panneaux métriques à 10 FPS, graphiques à 5 FPS).
- Zéro défilement vertical pour la zone de surveillance direct (caméra 60 % + métriques 40 %).

---

## 2. Variables de Session (`st.session_state`)

| Clé | Type | Description |
|---|---|---|
| `camera` | `CameraCapture \| None` | Instance de capture vidéo OpenCV |
| `pipeline` | `Pipeline \| None` | Orchestrateur de traitement et détection |
| `camera_running` | `bool` | Indicateur d'état actif de la webcam |
| `sensitivity` | `str` | Niveau sélectionné : "Basse", "Normale", "Haute" |
| `muted` | `bool` | État de sourdine des alarmes audio |
| `session_start` | `float \| None` | Timestamp de démarrage de la session |
| `alert_count` | `int` | Compteur d'épisodes de niveau Danger |
| `prev_alert_level` | `AlertLevel` | Dernier niveau pour détection du front montant d'alerte |
| `ear_history` | `list[float]` | Historique de l'Eye Aspect Ratio |
| `mar_history` | `list[float]` | Historique du Mouth Aspect Ratio |
| `perclos_history` | `list[float]` | Historique de la proportion d'yeux fermés |
| `score_history` | `list[float]` | Historique du score de fatigue |
| `profile_choice_done`| `bool` | Indicateur de sélection du profil de calibration |
| `camera_error` | `str \| None` | Message d'erreur explicatif en cas d'échec caméra |

---

## 3. Disposition Écran & Hiérarchie Visuelle

```
┌──────────────────────────────────────────────────────────────────────┐
│ EN-TÊTE : Logo DrowsiGuard   [État système]   [Durée session]        │
├───────────────────────────────────────────┬──────────────────────────┤
│                                           │  NIVEAU DE FATIGUE       │
│        FLUX CAMÉRA EN DIRECT              │  ● Grand badge + Cause   │
│   (maillage facial + cadre couleur 4px    │  Jauge circulaire 0-100  │
│    + bandeau de statut qualité)           ├──────────────────────────┤
│                                           │  5 CARTES MÉTRIQUES      │
│        ~60 % de la largeur                │  EAR, MAR, PERCLOS,      │
│                                           │  Yeux fermés, Inclinaison│
│                                           ├──────────────────────────┤
│                                           │  COMPTEURS (3 cartes)    │
│                                           │  Bâillements|Micro-S|Al. │
├───────────────────────────────────────────┴──────────────────────────┤
│ 3 GRAPHIQUES PLOTLY (60s) : EAR │ MAR │ PERCLOS & Score de fatigue   │
├──────────────────────────────────────────────────────────────────────┤
│ JOURNAL DES ÉVÉNEMENTS (Tableau avec pastilles) + Export CSV         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Stabilité et Résilience

- **Tolérance aux drops caméra** : La boucle tolère jusqu'à 30 trames perdues consécutives avant d'interrompre la capture, évitant les fermetures accidentelles sous charge système.
- **Protection anti-freeze** : Les opérations lourdes (graphiques Plotly, historique SQLite) sont cadencées à des fréquences adaptées pour préserver l'interactivité de la page.
