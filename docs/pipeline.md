# pipeline.md — Documentation

## 1. Rôle

Orchestre l'ensemble du pipeline de détection : caméra → landmarks → qualité → calibration ou surveillance → alarme → journal. Retourne l'image annotée et un `PipelineStatus` à chaque frame. Fonctionne sans Streamlit.

## 2. Séquence d'une itération

1. Lecture d'une frame (caméra déjà ouverte en dehors du pipeline).
2. Détection des landmarks (FaceMeshDetector).
3. Contrôle qualité (check_quality).
4. Si qualité ok : extraction des métriques EAR/MAR/pitch.
5. Si pas encore calibré → `CalibrationEngine.update()`.
6. Si calibré → `AdaptiveBaseline.update()` + `DrowsinessState.update()`.
7. Déclenchement de l'alarme si nécessaire.
8. Enregistrement des événements significatifs.
9. Annotation de l'image (cadre coloré, métriques en surimpression).
10. Retour de `(annotated_frame, PipelineStatus)`.

## 3. API publique

| Méthode | Paramètres | Retour |
|---|---|---|
| `Pipeline(sensitivity, muted, on_profile_saved)` | options | — |
| `load_existing_profile()` | — | `UserProfile \| None` |
| `start_calibration()` | — | — |
| `process(frame, timestamp)` | image BGR, ts injectable | `(ndarray, PipelineStatus)` |
| `set_sensitivity(s)` | "Basse"/"Normale"/"Haute" | — |
| `set_muted(b)` | bool | — |
| `close()` | — | — |

## 4. Utilisation sans Streamlit

```python
from drowsiguard.camera import CameraCapture
from drowsiguard.pipeline import Pipeline

cam = CameraCapture()
cam.open()
pipe = Pipeline()
while True:
    ret, frame = cam.read()
    annotated, status = pipe.process(frame)
    cv2.imshow("DrowsiGuard", annotated)
    if cv2.waitKey(1) == ord('q'):
        break
cam.release()
pipe.close()
```
