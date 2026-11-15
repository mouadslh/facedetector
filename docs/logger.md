# logger.md — Documentation

## 1. Rôle
Enregistre les événements de somnolence horodatés dans une base SQLite et offre lecture + export CSV.

## 2. Schéma de la table `events`

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER | Clé primaire auto |
| `timestamp` | TEXT | ISO 8601 UTC |
| `event_type` | TEXT | 'microsleep', 'yawn', 'alert_vigilance', 'alert_danger' |
| `level` | TEXT | 'Normal', 'Vigilance', 'Danger' |
| `ear` | REAL | EAR au moment de l'événement |
| `mar` | REAL | MAR |
| `pitch` | REAL | Pitch |
| `perclos` | REAL | PERCLOS [0,1] |
| `score` | REAL | Score de fatigue |
| `causes` | TEXT | Causes lisibles (séparées par ", ") |

## 3. API publique

| Méthode | Paramètres | Retour |
|---|---|---|
| `EventLogger(db_path)` | Path | — |
| `log_event(event_type, level, ...)` | scalaires, listes | — |
| `get_history(limit)` | int | `list[EventRecord]` |
| `export_csv(output_path)` | Path | Path |
| `close()` | — | — |

## 4. Sécurité

- `check_same_thread=False` pour la compatibilité Streamlit (threads multiples).
- Toutes les erreurs SQLite sont attrapées et loggées sans crash.
