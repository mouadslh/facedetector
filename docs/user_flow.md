# Parcours utilisateur — DrowsiGuard

## Écran 1 : Démarrage

Dès le lancement de `streamlit run app.py` :

- La caméra s'ouvre **automatiquement** (aucune action requise).
- **Si la caméra est disponible** → passage immédiat à l'écran 2.
- **Si la caméra est indisponible** :
  ```
  Erreur caméra

  Aucune webcam disponible.

  Vérifiez :
  • Réglages Système > Confidentialité > Caméra → autoriser Terminal / votre app.
  • Qu'aucune autre application n'utilise la caméra (FaceTime, Zoom…).
  • Que la caméra est bien connectée (USB externe).
  ```
  Un bouton **▶️ Démarrer la caméra** apparaît dans le panneau latéral pour réessayer.

---

## Écran 2 : Choix du profil

Affiché uniquement si un `data/profile.json` valide existe.

```
Profil enregistré trouvé
Calibration du 2024-01-15 (sensibilité : Normale)

[ ✅ Utiliser le profil enregistré ]   [ 🔄 Recalibrer maintenant ]
```

- **Utiliser le profil** → passage direct à l'écran 4 (surveillance).
- **Recalibrer** → passage à l'écran 3.
- Si aucun profil → passage automatique à l'écran 3.

---

## Écran 3 : Calibration guidée (~12 s)

### Badge qualité (en haut)

| Statut | Message affiché |
|---|---|
| OK | ✅ Visage détecté ✓ |
| NO_FACE | 👤 Aucun visage détecté — placez-vous face à la caméra |
| TOO_FAR | ⚠️ Rapprochez-vous de la caméra |
| TOO_DARK | ⚠️ Trop sombre — éclairez davantage votre visage |
| TOO_BRIGHT | ⚠️ Trop lumineux — réduisez l'éclairage |
| TILTED | ⚠️ Visage trop incliné — regardez droit devant vous |
| OFF_CENTER | ⚠️ Visage trop excentré — recentrez-vous |

### Phases

**Attente** : `Placez-vous face à la caméra pour démarrer la calibration`  
→ Dès qu'un visage stable est détecté 1 s, la phase 1 démarre automatiquement.

**Phase 1 — Yeux ouverts** (4 s) :
```
👀
Regardez droit devant vous
yeux bien ouverts, bouche fermée
```
Barre de progression : 0 → 33 %

**Phase 2 — Yeux fermés** (2 s) :
```
😌
Fermez les yeux doucement
pendant 2 secondes
```
Barre de progression : 33 → 66 %

**Phase 3 — Bâillement** (3 s) :
```
😮
Ouvrez grand la bouche
comme pour bâiller
```
Barre de progression : 66 → 100 %

**Succès** :
```
✅
Calibration réussie !
Surveillance démarrée.
```
→ Profil sauvegardé dans `data/profile.json`, passage à l'écran 4.

**Échec** (profil incohérent) :
```
⚠️ Calibration incohérente (yeux pas assez distincts ou bâillement trop petit).
Recommencez en exagérant les gestes.

[ 🔄 Recommencer la calibration ]
```

---

## Écran 4 : Surveillance en temps réel

### Colonne gauche — Flux vidéo

- Flux annotés avec le maillage des points clés (yeux, bouche, nez).
- **Cadre de couleur** selon le niveau :
  - 🟢 Vert : Normal
  - 🟠 Orange : Vigilance
  - 🔴 Rouge : Danger
- Texte en surimpression : EAR, MAR, FPS, statut qualité, niveau.

### Colonne droite — Métriques

- **Jauge de fatigue** : barre colorée 0-100 avec le niveau textuel.
- **Bandeau de niveau** : Normal / Vigilance / Danger + causes lisibles.
- **Compteurs** : Durée session | Bâillements | Micro-sommeils | Alertes Danger.

### Graphiques (rafraîchis toutes les 10 frames)

- **EAR** : historique avec seuils personnels (yeux ouverts / mi-clos / fermés).
- **MAR** : historique avec seuil de bâillement.
- **PERCLOS** : pourcentage du temps yeux fermés (seuils 15 % / 25 %).
- **Score** : score de fatigue 0-100 (seuils Vigilance / Danger).

### Historique des événements

Table des 20 derniers événements (micro-sommeils, bâillements, alertes) avec export CSV.

---

## Panneau latéral

| Contrôle | Effet |
|---|---|
| **Sensibilité** : Basse / Normale / Haute | Modifie les ratios → recalcule les seuils |
| **🔇 Muet** | Active/désactive l'alarme sonore |
| **🔄 Recalibrer** | Relance la calibration depuis le début |
| **⏹️ Arrêter la caméra** | Libère la caméra proprement |
| **▶️ Démarrer la caméra** | Réouvre la caméra (si arrêtée) |
