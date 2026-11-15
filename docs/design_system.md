# Système de Design — DrowsiGuard

Ce document formalise la charte graphique, les règles ergonomiques et les standards visuels de l'interface de surveillance de somnolence **DrowsiGuard**.

---

## 1. Règle de Répartition des Couleurs (60 / 30 / 10)

L'interface adopte une hiérarchie chromatique stricte garantissant une concentration maximale du conducteur/opérateur sans fatigue oculaire :

| Rôle | Part | Code Hex | Nom | Utilisation principale |
|---|---|---|---|---|
| **Dominante** | **60 %** | `#0B1220` | Bleu nuit très sombre | Arrière-plan général de l'application, grandes surfaces |
| **Secondaire** | **30 %** | `#162033` | Bleu ardoise | Cartes d'information, barre latérale, conteneurs de graphiques, panneaux |
| **Accent** | **10 %** | `#22D3EE` | Cyan vif électrique | Boutons d'action prioritaires, titres de section, valeurs phares, courbes principales, badges d'état système |

### Couleurs Complémentaires
- **Texte principal** : `#E6EDF7` (contraste élevé > 9:1 sur `#0B1220`).
- **Texte secondaire / libellés** : `#8FA3BF` (contraste conforme WCAG AA > 4.5:1).
- **Bordures et séparateurs** : `#24324A` (délimitation subtile des cartes).

---

## 2. Couleurs Sémantiques d'État (Réservées)

> [!IMPORTANT]
> Les couleurs d'état sont **exclusivement réservées** au niveau de fatigue et aux alertes physiologiques. Elles ne sont **jamais** utilisées pour de simples décorations, afin de préserver l'impact cognitif immédiat de l'alerte.

| Niveau | Couleur | Hexadécimal | Fond teinté | Rôle & Signification |
|---|---|---|---|---|
| **Normal** | Vert émeraude | `#22C55E` | `rgba(34, 197, 94, 0.12)` | Conducteur attentif, clignements physiologiques |
| **Vigilance** | Ambre chaud | `#F59E0B` | `rgba(245, 158, 11, 0.15)` | Signes précurseurs : bâillements répétés, regard fuyant |
| **Danger** | Rouge vif | `#EF4444` | `rgba(239, 68, 68, 0.20)` | Micro-sommeil (> 1.5s), yeux fermés prolongés, chute de tête |

---

## 3. Typographie

- **Famille de police** : `Inter`, avec fallback système sans-serif (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`).
- **Chiffres tabulaires (`tabular-nums`)** : Activés sur toutes les métriques dynamiques (EAR, MAR, PERCLOS, durées) pour empêcher tout tressautement visuel lors des variations de valeur.
- **Échelle typographique** :
  - **Titre d'application** : 24–28 px, graisse 800.
  - **Titres de sections** : 14 px, majuscules espacées (`letter-spacing: 0.12em`), couleur accent `#22D3EE`.
  - **Valeurs métriques phares** : 28–36 px, graisse 800, `tabular-nums`.
  - **Libellés et sous-titres** : 12–13 px, graisse 600, couleur `#8FA3BF`.
  - **Corps de texte** : 14 px, interlignage 1.4.

---

## 4. Composants Visuels

### A. Cartes Métriques (`dg-card`)
- Rayon de courbure : `border-radius: 14px`.
- Bordure fine : `1px solid #24324A`.
- Fond secondaire : `#162033`.
- Ombrage doux : `box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25)`.
- Transition fluide : `200ms ease` sur le survol.

### B. Jauge Circulaire de Fatigue
- Format vectoriel SVG (130×130 px), zéro latence.
- Anneau d'arrière-plan discret `#24324A`.
- Arc d'avancement coloré dynamiquement selon le niveau (`#22C55E` → `#F59E0B` → `#EF4444`).
- Score affiché au centre en grand format `0–100`.

### C. Sparklines Intégrées
- Graphiques polylignes SVG ultra-légers (hauteur 24 px, largeur 90 px) embarqués directement dans les cartes métriques.
- Trace en cyan `#22D3EE` des 30 dernières secondes d'observation.

### D. Graphiques Plotly
- Fond transparent harmonisé avec la carte `#162033`.
- Grille très discrète `#24324A`.
- Barres d'outils masquées (`displayModeBar: false`) pour une vue cockpit épurée.
- 3 courbes synchronisées sur les 60 dernières secondes :
  1. **EAR** : Ouverture oculaire avec seuils de fermeture et somnolence.
  2. **MAR** : Ouverture buccale avec seuil de bâillement.
  3. **PERCLOS & Score** : Proportion de temps yeux fermés et score composite.

---

## 5. Ergonomie et Accessibilité

1. **Règle du non-défilement** : En affichage 13 pouces ou plus (1280 px de large), le flux vidéo et les métriques critiques sont situés côte à côte (`[3, 2]`) dans le viewport supérieur sans aucun défilement nécessaire.
2. **Double encodage** : Tout état critique combine une icône explicite (🟢, 🟠, 🔴 ou 🚨), une étiquette textuelle en clair (`NORMAL`, `VIGILANCE`, `DANGER`), et une cause lisible en français.
3. **Pulsation d'alerte** : Le bandeau Danger clignote à une fréquence douce (1.2 s, oscillation d'opacité 0.85–1.0) sans aucun effet stroboscopique agressif.
