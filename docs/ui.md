# ui.md — Documentation de l'Interface Utilisateur

## 1. Rôle et Architecture

Le package `src/drowsiguard/ui/` gère la présentation visuelle de DrowsiGuard selon le principe strict : **aucune logique métier**. Il comprend :
- `theme.py` : Définition unique de la charte 60 / 30 / 10, des couleurs sémantiques et des styles CSS globaux.
- `components.py` : Composants Streamlit et générateurs vectoriels SVG (en-tête, badge, jauge, cartes sparkline, compteurs).
- `charts.py` : Visualisations Plotly interactives optimisées pour le temps réel.

---

## 2. Palette 60 / 30 / 10 (`theme.py`)

- **Dominante (60 %)** : `#0B1220` (Bleu nuit très sombre)
- **Secondaire (30 %)** : `#162033` (Bleu ardoise)
- **Accent (10 %)** : `#22D3EE` (Cyan électrique)
- **Couleurs d'état sémantiques** :
  - Normal : `#22C55E`
  - Vigilance : `#F59E0B`
  - Danger : `#EF4444`

---

## 3. Composants Visuels (`components.py`)

| Fonction | Rôle & Paramètres | Rendu visuel |
|---|---|---|
| `render_header(status_label, session_dur_s)` | En-tête supérieur global | Logo, statut système en pastille, chronomètre session |
| `render_quality_badge(quality)` | Statut sous le flux caméra | Badge couleur avec icône (OK, Visage perdu, Rapprochez-vous...) |
| `render_fatigue_section(result)` | Niveau + cause + jauge | Grand badge de niveau, cause en français, jauge circulaire SVG 0–100 |
| `render_metrics_cards(...)` | 5 métriques clés | EAR, MAR, PERCLOS, Fermeture yeux, Inclinaison tête avec sparklines SVG |
| `render_counters_bar(result, alert_count)` | Statistiques de session | 3 cartes : Bâillements, Micro-sommeils, Alertes Danger |
| `render_calibration_screen(status)` | Écran de guidage initial | Consignes en grand format, barre de progression en cyan accent |

---

## 4. Graphiques Plotly (`charts.py`)

Trois graphiques synchronisés affichés côte à côte (historique glissant de 60 secondes) :
1. `ear_chart(ear_history, thresholds)` : Historique de l'EAR avec zone de fermeture et seuil de somnolence.
2. `mar_chart(mar_history, thresholds)` : Historique du MAR avec zone et seuil de bâillement.
3. `perclos_score_chart(perclos_history, score_history)` : Double tracé PERCLOS (%) et Score de fatigue (0–100).

Optimisation :
- Barre d'outils désactivée (`displayModeBar: False`).
- Rafraîchissement cadencé à 5–6 FPS pour préserver la fluidité vidéo de 30 FPS.
