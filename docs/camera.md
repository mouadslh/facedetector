# camera.md — Documentation

## 1. Rôle
Gère le cycle de vie complet de la webcam : ouverture automatique, lecture de frames, libération propre. Fournit des messages d'erreur clairs pour les problèmes courants sur macOS.

## 2. API publique

| Méthode | Paramètres | Retour | Effets de bord |
|---|---|---|---|
| `CameraCapture(candidates, width, height, fps)` | listes et entiers | — | — |
| `open()` | — | `int` (index) | Ouvre la caméra |
| `read()` | — | `(bool, ndarray\|None)` | — |
| `release()` | — | — | Libère la caméra |
| `is_open` | — | `bool` | — |
| `index` | — | `int` | -1 si fermée |

## 3. Erreurs gérées

- `CameraError` : aucune caméra disponible → message détaillé macOS (permissions, caméra occupée).
- `read()` échoue → retourne `(False, None)` sans lever d'exception.

## 4. Paramètres de config.py

`CAMERA_CANDIDATES`, `CAMERA_WIDTH`, `CAMERA_HEIGHT`, `CAMERA_FPS`
