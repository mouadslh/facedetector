# landmarks.md — Documentation

## 1. Rôle
Initialise MediaPipe Face Mesh et détecte les 468 points de repère du visage sur chaque frame. Convertit les coordonnées normalisées en pixels.

## 2. API publique

| Méthode | Paramètres | Retour |
|---|---|---|
| `FaceMeshDetector(...)` | paramètres MediaPipe | — |
| `detect(frame)` | image BGR | `list[NormalizedLandmark]\|None` |
| `get_pixels(landmarks, indices, shape)` | points + indices | `ndarray(N,2)` float32 |
| `close()` | — | — |

## 3. Performance

- Résolution recommandée : 640×480 → > 20 FPS sur Apple Silicon CPU.
- `refine_landmarks=False` (iris désactivé) pour économiser du CPU.
