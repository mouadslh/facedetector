# DrowsiGuard 🛡️💤

**Détection de somnolence en temps réel — zéro seuil absolu codé en dur.**

DrowsiGuard analyse en direct le flux de votre webcam, se calibre automatiquement sur votre morphologie faciale (~12 s), puis surveille en temps réel les signes physiologiques de fatigue (fermeture prolongée des yeux, micro-sommeils, bâillements, affaissement de la tête) avec une alarme sonore graduée.

---

## 🎨 Charte Visuelle & Système de Couleurs (60 / 30 / 10)

L'interface professionnelle repose sur un système dark mode à fort contraste :

| Part | Rôle | Code Hex | Utilisation |
|---|---|---|---|
| **60 %** | **Dominante** | `#0B1220` | Bleu nuit très sombre : fond d'écran principal |
| **30 %** | **Secondaire** | `#162033` | Bleu ardoise : cartes métriques, sidebar, conteneurs |
| **10 %** | **Accent** | `#22D3EE` | Cyan vif : boutons phares, titres, valeurs critiques, courbes |

### Couleurs d'État Sémantiques (Réservées au niveau de fatigue)
- 🟢 **Normal** (`#22C55E`) : État de veille optimal.
- 🟠 **Vigilance** (`#F59E0B`) : Premiers signes de fatigue (bâillements, paupières lourdes).
- 🔴 **Danger** (`#EF4444`) : Alerte immédiate (yeux fermés > 1.5 s, micro-sommeil).

---

## 🖥️ Disposition en Écran Large (Cockpit temps réel)

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

> **Sans défilement** : En résolution standard (≥ 1280 px), la caméra et toutes les métriques sont visibles simultanément en haut d'écran.

---

## 🚀 Installation & Démarrage rapide

```bash
# 1. Cloner le projet et entrer dans le dossier
cd DrowsiGuard

# 2. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate   # macOS / Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Générer les fichiers sons WAV
python scripts/generate_sounds.py

# 5. Lancer l'application Streamlit
streamlit run app.py
```

---

## 🧪 Tests & Qualité

```bash
# Lancer les tests unitaires et d'interface
venv/bin/pytest tests/ -v
```

---

## 📁 Architecture du projet

```
DrowsiGuard/
├── app.py                     # Point d'entrée Streamlit (vue principale)
├── .streamlit/
│   └── config.toml            # Thème sombre officiel (60/30/10)
├── src/drowsiguard/
│   ├── config.py              # Configuration et constantes
│   ├── camera.py              # Capture vidéo robuste
│   ├── landmarks.py           # Détecteur MediaPipe FaceMesh
│   ├── quality.py             # Contrôle qualité de la frame
│   ├── metrics.py             # Calculs EAR, MAR, Pitch
│   ├── profile.py             # Gestion du profil morphologique
│   ├── calibration.py         # Machine à états de calibration
│   ├── thresholds.py          # Seuils personnalisés relatifs
│   ├── adaptive.py            # Ligne de base adaptative
│   ├── state.py               # Évaluation de la somnolence & score
│   ├── alarm.py               # Gestionnaire d'alerte sonore non bloquant
│   ├── logger.py              # Enregistrement SQLite & export CSV
│   ├── pipeline.py            # Orchestrateur central sans Streamlit
│   └── ui/
│       ├── theme.py           # Système de design 60/30/10 & CSS
│       ├── components.py      # Composants UI (jauge, badges, sparklines)
│       └── charts.py          # Graphiques Plotly haute fidélité
├── docs/                      # Documentation technique
│   └── design_system.md       # Charte graphique détaillée
└── tests/                     # Suite de tests automatisés (pytest)
```

---

## 🔒 Confidentialité en mode hébergé

En mode hébergé, la webcam est activée dans le navigateur avec l'accord de l'élève, puis le flux vidéo est transmis au serveur par WebRTC pour le traitement. Les profils et journaux sont séparés par session et enregistrés sur le serveur. N'utilisez pas cette version avec des données sensibles sans informer les élèves et définir une politique de conservation. Pour un usage 100 % local, lancez l'application sur l'ordinateur concerné.

## 🌐 Déploiement pour une classe

L'application utilise `streamlit-webrtc` : chaque élève ouvre le lien, clique sur **Start** dans le lecteur vidéo et autorise la webcam. Le site doit être servi en HTTPS. Le serveur d'hébergement doit aussi autoriser le trafic WebRTC; certains réseaux scolaires ou hébergeurs filtrent les connexions vidéo, auquel cas un serveur TURN sera nécessaire.

1. Publiez ce dépôt sur GitHub. Vérifiez que `assets/face_landmarker.task` est bien inclus.
2. Créez une application Streamlit Community Cloud reliée au dépôt, avec `app.py` comme fichier principal.
3. Dans les paramètres avancés, choisissez Python 3.11 (les dépendances de vision du projet ciblent Python 3.10–3.12).
4. Attendez la fin de l'installation, puis partagez l'URL HTTPS générée.
5. Demandez à chaque élève d'ouvrir le lien avec Chrome ou Edge, d'autoriser la caméra et d'appuyer sur **Start**.

Chaque session reçoit son propre identifiant temporaire pour isoler son profil et son journal. Les données écrites sur un hébergement éphémère peuvent disparaître lors d'un redémarrage. Pour une classe entière, faites d'abord un essai simultané avec quelques élèves : le traitement vidéo consomme des ressources CPU par personne connectée.
