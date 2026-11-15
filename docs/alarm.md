# alarm.md — Documentation

## 1. Rôle
Joue des sons d'alarme graduée (Vigilance = bip grave, Danger = double bip aigu) dans un thread séparé, avec cooldown et mode muet. Ne plante jamais si l'audio est indisponible.

## 2. API publique

| Méthode | Paramètres | Rôle |
|---|---|---|
| `AlarmManager(muted)` | bool | Initialise pygame.mixer |
| `alert_vigilance(timestamp)` | float\|None | Bip niveau 1 si cooldown écoulé |
| `alert_danger(timestamp)` | float\|None | Bip niveau 2 si cooldown écoulé |
| `stop()` | — | Arrête le son en cours |
| `close()` | — | Libère pygame.mixer |
| `muted` | — | Propriété get/set |

## 3. Fichiers sons

Générés par `scripts/generate_sounds.py` dans `assets/`. Avertissement affiché si absents (pas de crash).

## 4. Paramètres de config.py

`ALARM_FREQ_LOW`, `ALARM_FREQ_HIGH`, `ALARM_DURATION_LOW_S`, `ALARM_DURATION_HIGH_S`, `ALARM_COOLDOWN_LOW_S`, `ALARM_COOLDOWN_HIGH_S`
