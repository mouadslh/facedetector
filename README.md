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

## 🔒 Confidentialité & Traitement 100% Local

Aucune image ni vidéo n'est transmise ni enregistrée sur le réseau. L'intégralité du traitement par vision par ordinateur et du diagnostic de fatigue s'exécute localement sur la machine de chaque élève.

## 💻 Lancement facile pour les élèves

Partagez le dépôt GitHub : <https://github.com/mouadslh/facedetector>. Chaque élève installe Python 3.10, 3.11 ou 3.12, télécharge le projet et lance le script correspondant à son système. Le script installe les dépendances et démarre l'application.

**macOS / Linux** — dans Terminal :

```bash
git clone https://github.com/mouadslh/facedetector.git
cd facedetector
bash scripts/run_local.sh
```

**Windows** — dans PowerShell ou l'Invite de commandes :

```bat
git clone https://github.com/mouadslh/facedetector.git
cd facedetector
scripts\run_local.bat
```

Au premier lancement, l'installation peut prendre quelques minutes. Ensuite, chaque élève ouvre l'adresse locale affichée par Streamlit et autorise sa webcam.
