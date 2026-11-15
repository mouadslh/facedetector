"""
Configuration centrale de DrowsiGuard.

Ce fichier contient UNIQUEMENT :
  - des ratios (fractions sans dimension)
  - des durées (en secondes)
  - des indices de points de repère
  - des poids (pour le score de fatigue)
  - des valeurs de repli (utilisées UNIQUEMENT avant la fin de la calibration)

RÈGLE ABSOLUE : aucune valeur absolue de seuil EAR/MAR/pitch n'est codée ici.
Tous les seuils réels sont calculés dans thresholds.py à partir du profil personnel.
"""

# ---------------------------------------------------------------------------
# Indices des points de repère (MediaPipe Face Mesh, 468 points)
# ---------------------------------------------------------------------------

# Œil droit : [p1, p2, p3, p4, p5, p6]
# Formule EAR : (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
RIGHT_EYE_INDICES: list[int] = [33, 160, 158, 133, 153, 144]

# Œil gauche (symétrique)
LEFT_EYE_INDICES: list[int] = [362, 385, 387, 263, 373, 380]

# Bouche : [haut, bas, gauche, droite]
# Formule MAR : (||haut-bas||) / (||gauche-droite||)
MOUTH_INDICES: list[int] = [13, 14, 78, 308]

# Points pour l'estimation du pitch (inclinaison avant/arrière)
# Nez (bout), menton, milieu du front
PITCH_NOSE_TIP: int = 1
PITCH_CHIN: int = 152
PITCH_FOREHEAD: int = 10

# ---------------------------------------------------------------------------
# Ratios pour la dérivation des seuils (thresholds.py)
# ---------------------------------------------------------------------------
# Ces valeurs définissent la position du seuil entre les extrêmes calibrés.
# Exemple : EAR_CLOSE_RATIO = 0.40 signifie que le seuil de fermeture
# se situe à 40 % de la distance entre EAR_closed et EAR_open.

# Sensibilité Normale (valeurs par défaut)
EAR_CLOSE_RATIO: float = 0.40      # fraction entre EAR_closed et EAR_open
EAR_DROWSY_RATIO: float = 0.60     # fraction plus haute (yeux mi-clos)
MAR_YAWN_RATIO: float = 0.45       # fraction entre MAR_rest et MAR_yawn
HEAD_PITCH_RATIO: float = 0.50     # fraction de l'écart neutre/max toléré

# Modificateurs par niveau de sensibilité
SENSITIVITY_MODIFIERS: dict[str, float] = {
    "Basse":    0.80,   # seuils plus permissifs (moins d'alertes)
    "Normale":  1.00,   # valeur de référence
    "Haute":    1.20,   # seuils plus stricts (alertes plus précoces)
}

# ---------------------------------------------------------------------------
# Durées (secondes)
# ---------------------------------------------------------------------------

# Durée minimale de fermeture pour un micro-sommeil confirmé
MICROSLEEP_DURATION_S: float = 1.5

# Durée après laquelle le niveau passe à Danger
DANGER_DURATION_S: float = 2.5

# Durée de la fenêtre glissante pour le PERCLOS
PERCLOS_WINDOW_S: float = 60.0

# Durée minimale entre deux bâillements comptés
YAWN_COOLDOWN_S: float = 3.0

# Les bâillements n'entretiennent la vigilance que pendant cette fenêtre.
YAWN_ALERT_WINDOW_S: float = 30.0

# Durée minimale d'un bâillement (MAR au-dessus du seuil)
YAWN_MIN_DURATION_S: float = 0.5

# ---------------------------------------------------------------------------
# Phases de calibration (secondes)
# ---------------------------------------------------------------------------

# Phase 1 : yeux ouverts, mesure EAR_open + MAR_rest + pitch_neutral
CALIB_PHASE_OPEN_S: float = 4.0

# Phase 2 : yeux fermés, mesure EAR_closed
CALIB_PHASE_CLOSED_S: float = 2.0

# Phase 3 : bâillement, mesure MAR_yawn
CALIB_PHASE_YAWN_S: float = 3.0

# Délai de stabilisation avant chaque phase
CALIB_STABILIZE_S: float = 1.0

# Écart minimal requis entre EAR_open et EAR_closed pour valider le profil
CALIB_EAR_MIN_DELTA: float = 0.04

# Écart minimal requis entre MAR_yawn et MAR_rest pour valider le profil
CALIB_MAR_MIN_DELTA: float = 0.10

# Fraction des valeurs aberrantes à écarter (winsorisation)
CALIB_OUTLIER_TRIM: float = 0.10

# ---------------------------------------------------------------------------
# Contrôle qualité de l'image (quality.py)
# ---------------------------------------------------------------------------

# Taille minimale du visage en fraction de la hauteur de l'image
QUALITY_MIN_FACE_RATIO: float = 0.18

# Luminosité minimale (valeur de pixel moyenne sur le visage, 0-255)
QUALITY_MIN_BRIGHTNESS: int = 40

# Luminosité maximale (surexposition)
QUALITY_MAX_BRIGHTNESS: int = 240

# Inclinaison de tête maximale tolérée (en degrés) pendant la surveillance
QUALITY_MAX_PITCH_DEG: float = 30.0

# Inclinaison de tête maximale tolérée pendant la calibration
QUALITY_MAX_PITCH_DEG_CALIB: float = 15.0

# ---------------------------------------------------------------------------
# Adaptation lente de la ligne de base (adaptive.py)
# ---------------------------------------------------------------------------

# Durée de la fenêtre glissante pour estimer EAR_open en conditions réelles
ADAPTIVE_WINDOW_S: float = 120.0

# Percentile utilisé pour estimer EAR_open (ex. 90e percentile)
ADAPTIVE_PERCENTILE: float = 90.0

# Vitesse maximale d'adaptation (fraction par seconde)
ADAPTIVE_MAX_SPEED: float = 0.002

# Amplitude maximale de dérive autorisée (fraction de EAR_open calibré)
ADAPTIVE_MAX_DRIFT: float = 0.20

# ---------------------------------------------------------------------------
# Score de fatigue — poids des sous-scores (state.py)
# ---------------------------------------------------------------------------
# Les poids sont normalisés automatiquement dans state.py.

SCORE_WEIGHT_EAR: float = 0.35         # fermeture / durée des yeux fermés
SCORE_WEIGHT_PERCLOS: float = 0.30     # proportion de temps yeux fermés
SCORE_WEIGHT_MAR: float = 0.20         # bâillements
SCORE_WEIGHT_HEAD: float = 0.15        # chute de tête

# Seuils du score pour les niveaux (0-100)
SCORE_VIGILANCE: float = 40.0
SCORE_DANGER: float = 70.0

# ---------------------------------------------------------------------------
# Valeurs de repli (utilisées AVANT la fin de la calibration uniquement)
# ---------------------------------------------------------------------------
# Ces valeurs sont des estimations génériques, pas des seuils de production.

FALLBACK_EAR_OPEN: float = 0.30
FALLBACK_EAR_CLOSED: float = 0.15
FALLBACK_MAR_REST: float = 0.20
FALLBACK_MAR_YAWN: float = 0.60
FALLBACK_PITCH_NEUTRAL: float = 0.0

# ---------------------------------------------------------------------------
# Alarme (alarm.py)
# ---------------------------------------------------------------------------

# Fréquences des bips (Hz)
ALARM_FREQ_LOW: int = 440
ALARM_FREQ_HIGH: int = 880

# Durées des bips (secondes)
ALARM_DURATION_LOW_S: float = 0.5
ALARM_DURATION_HIGH_S: float = 0.3

# Intervalle minimum entre deux alarmes du même niveau (secondes)
ALARM_COOLDOWN_LOW_S: float = 3.0
ALARM_COOLDOWN_HIGH_S: float = 1.0

# ---------------------------------------------------------------------------
# Caméra (camera.py)
# ---------------------------------------------------------------------------

# Indices à essayer, dans l'ordre
CAMERA_CANDIDATES: list[int] = [0, 1, 2]

# Résolution cible
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 480

# FPS cible
CAMERA_FPS: int = 15
