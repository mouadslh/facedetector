# decisions.md — Choix architecturaux

## 1. Seuils relatifs au profil personnel

**Choix** : Tous les seuils sont des fractions des valeurs mesurées sur l'utilisateur.  
**Justification** : L'EAR varie fortement entre individus (forme des yeux, ethnie, âge) et entre conditions (éclairage, angle de la caméra). Un seuil absolu (ex. EAR < 0.25) serait trop strict pour certaines personnes et trop lâche pour d'autres. En positionnant le seuil à 40 % de la distance entre l'EAR yeux fermés et l'EAR yeux ouverts de CETTE personne, on garantit une sensibilité cohérente pour tout le monde.

---

## 2. Médiane + winsorisation au lieu de la moyenne

**Choix** : Utilisation de la médiane après suppression des 10 % extrêmes.  
**Justification** : Pendant la phase yeux ouverts, l'utilisateur cligne des yeux (clignements normaux). Ces clignements créent des valeurs EAR très basses qui fausseraient la moyenne. La médiane est robuste aux valeurs aberrantes. La winsorisation à 10 % élimine en plus les outliers aux deux extrêmes.

---

## 3. Machine à états pour la calibration (pas un minuteur seul)

**Choix** : Détection automatique de la fermeture des yeux en phase 2 (chute nette de l'EAR), pas seulement un minuteur.  
**Justification** : Si l'utilisateur ne ferme pas les yeux pendant la phase 2 (mal compris la consigne), un simple minuteur enregistrerait des données erronées. En détectant la chute de l'EAR, on s'assure que les données collectées correspondent réellement à des yeux fermés.

---

## 4. AdaptiveBaseline : compensation lente sans dérive

**Choix** : Re-estimation du percentile 90 de l'EAR sur une fenêtre de 2 min, bloquée pendant les fermetures.  
**Justification** : La lumière ambiante et la posture changent pendant une session longue. Sans adaptation, les seuils deviennent progressivement inadaptés. Le blocage pendant les fermetures empêche l'adaptation de "s'habituer" à une somnolence et de ne plus la détecter. La vitesse d'adaptation limitée (max_speed) empêche les changements brusques.

---

## 5. CPU uniquement, MediaPipe Face Mesh

**Choix** : MediaPipe Face Mesh (CPU) plutôt qu'un modèle PyTorch.  
**Justification** : Sur Mac Apple Silicon, MediaPipe CPU atteint facilement 20-30 FPS pour la détection faciale. Les modèles PyTorch sur CPU sont beaucoup plus lents pour des tâches comparables. De plus, MediaPipe est une dépendance bien packagée, sans CUDA requis, et expose directement les 468 points dont on a besoin.

---

## 6. Score de fatigue pondéré plutôt qu'un seul indicateur

**Choix** : Score = somme pondérée de sous-scores EAR, PERCLOS, MAR, pitch.  
**Justification** : Aucun indicateur seul n'est parfait. L'EAR instantané donne des faux positifs (clignements). Le PERCLOS est robuste mais réactif lentement. Les bâillements sont un signal précoce. La combinaison pondérée est plus fiable et plus graduée que n'importe quel indicateur pris seul.

---

## 7. SQLite pour le journal (pas de fichier CSV brut)

**Choix** : Journal en SQLite avec export CSV à la demande.  
**Justification** : SQLite est inclus dans la bibliothèque standard Python, gère le multi-accès, et permet des requêtes (filtres, tri) efficaces. L'export CSV reste disponible pour l'analyse externe. Écrire chaque frame dans un CSV serait trop lent et produirait des fichiers gigantesques.

---

## 8. Index de caméra : essai automatique de 0, 1, 2

**Choix** : Tester les indices 0, 1, 2 dans l'ordre et prendre le premier qui fonctionne.  
**Justification** : Sur macOS, l'index de la webcam intégrée est généralement 0, mais peut être 1 si une interface virtuelle (Continuity Camera) est active. Tester automatiquement évite à l'utilisateur de chercher l'index manuellement.

---

## 9. Un seul profil utilisateur

**Choix** : Un seul `data/profile.json` pour l'instant.  
**Justification** : Le cas d'usage principal est une personne au volant ou à son bureau. La gestion multi-profils complexifierait l'interface sans apporter de valeur immédiate. Elle peut être ajoutée en Étape 9 si nécessaire.
