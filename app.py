"""
app.py — Point d'entrée de l'application DrowsiGuard.

Interface claire avec une mise en page lisible pour la surveillance en direct.

Disposition en page large (layout="wide") :
- Barre supérieure : identité de l'application et menu déroulant de contrôles
- Rangée principale : statistiques à gauche, caméra au centre, graphiques empilés à droite
- Bas de page : historique des événements récents en pleine largeur
"""

from __future__ import annotations

import sys
import time
import inspect
from pathlib import Path

import cv2
import streamlit as st

# Ajouter src/ au path Python
sys.path.insert(0, str(Path(__file__).parent / "src"))

from drowsiguard.camera import CameraCapture, CameraError
from drowsiguard.logger import EventLogger
from drowsiguard.pipeline import Pipeline
from drowsiguard.profile import load_profile
from drowsiguard.state import AlertLevel
from drowsiguard.ui.charts import ear_chart, mar_chart, perclos_score_chart, PLOTLY_CONFIG
from drowsiguard.ui.components import (
    render_calibration_screen,
    render_counters_bar,
    render_fatigue_section,
    render_header,
    render_metrics_cards,
    render_quality_badge,
)
from drowsiguard.ui.theme import (
    GLOBAL_CSS,
)

# ---------------------------------------------------------------------------
# Configuration de la page Streamlit
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="DrowsiGuard — Détection de somnolence",
    page_icon="D",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Injection de la charte CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Streamlit renamed this image sizing option in newer releases.
_IMAGE_WIDTH_OPTION = (
    "use_container_width"
    if "use_container_width" in inspect.signature(st.image).parameters
    else "use_column_width"
)


# ---------------------------------------------------------------------------
# Initialisation de la session
# ---------------------------------------------------------------------------


def _init_session() -> None:
    defaults = {
        "camera": None,
        "pipeline": None,
        "sensitivity": "Normale",
        "muted": False,
        "camera_running": False,
        "recalibrate": False,
        "profile_choice_done": False,
        "ear_history": [],
        "mar_history": [],
        "perclos_history": [],
        "score_history": [],
        "session_start": None,
        "alert_count": 0,
        "prev_alert_level": AlertLevel.NORMAL,
        "camera_error": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()


# ---------------------------------------------------------------------------
# Gestionnaires Caméra & Pipeline
# ---------------------------------------------------------------------------


def _start_camera() -> None:
    cam: CameraCapture | None = None
    try:
        cam = CameraCapture()
        cam.open()
        st.session_state["camera"] = cam
        st.session_state["pipeline"] = Pipeline(
            sensitivity=st.session_state["sensitivity"],
            muted=st.session_state["muted"],
        )
        st.session_state["camera_running"] = True
        st.session_state["camera_error"] = None
        if st.session_state["session_start"] is None:
            st.session_state["session_start"] = time.time()
    except Exception as exc:
        if cam is not None:
            cam.release()
        st.session_state["camera"] = None
        st.session_state["pipeline"] = None
        st.session_state["camera_error"] = str(exc)
        st.session_state["camera_running"] = False


def _stop_camera() -> None:
    if st.session_state["camera"] is not None:
        st.session_state["camera"].release()
        st.session_state["camera"] = None
    if st.session_state["pipeline"] is not None:
        st.session_state["pipeline"].close()
        st.session_state["pipeline"] = None
    st.session_state["camera_running"] = False


# Démarrage automatique au chargement
if not st.session_state["camera_running"] and st.session_state["camera_error"] is None:
    _start_camera()


# ---------------------------------------------------------------------------
# Barre de navigation avec menu déroulant de contrôles
# ---------------------------------------------------------------------------

with st.container(border=True):
    nav_brand, nav_controls = st.columns([5, 1])
    with nav_brand:
        st.subheader("DrowsiGuard")
        st.caption("Système embarqué anti-somnolence")

    with nav_controls:
        with st.popover("Contrôles", use_container_width=True):
            st.subheader("Paramètres")
            sensitivity = st.selectbox(
                "Sensibilité de détection",
                ["Basse", "Normale", "Haute"],
                index=["Basse", "Normale", "Haute"].index(st.session_state["sensitivity"]),
                help="Ajuste les seuils de tolérance d'alerte sans changer vos caractéristiques physiques.",
            )
            if sensitivity != st.session_state["sensitivity"]:
                st.session_state["sensitivity"] = sensitivity
                if st.session_state["pipeline"] is not None:
                    st.session_state["pipeline"].set_sensitivity(sensitivity)

            muted = st.toggle("Mode silencieux (Muet)", value=st.session_state["muted"])
            if muted != st.session_state["muted"]:
                st.session_state["muted"] = muted
                if st.session_state["pipeline"] is not None:
                    st.session_state["pipeline"].set_muted(muted)

            if not muted:
                with st.expander("Tester les sons"):
                    if st.button("Tester l'alerte vigilance", use_container_width=True):
                        if not st.session_state["pipeline"].test_alarm("low"):
                            st.warning("Son indisponible. Vérifiez que pygame est installé et que les fichiers WAV existent dans assets/.")
                    if st.button("Tester l'alerte danger", use_container_width=True):
                        if not st.session_state["pipeline"].test_alarm("high"):
                            st.warning("Son indisponible. Vérifiez que pygame est installé et que les fichiers WAV existent dans assets/.")

            st.subheader("Calibration")

            if st.button("Recalibrer", use_container_width=True):
                if st.session_state["pipeline"] is not None:
                    st.session_state["pipeline"].start_calibration()
                st.session_state["profile_choice_done"] = False
                st.session_state["ear_history"] = []
                st.session_state["mar_history"] = []
                st.session_state["perclos_history"] = []
                st.session_state["score_history"] = []
                st.session_state["alert_count"] = 0
                st.session_state["prev_alert_level"] = AlertLevel.NORMAL
                st.rerun()

            st.subheader("Contrôle caméra")

            if st.session_state["camera_running"]:
                if st.button("Arrêter la caméra", use_container_width=True):
                    _stop_camera()
                    st.rerun()
            else:
                if st.button("Démarrer la caméra", use_container_width=True):
                    _start_camera()
                    st.rerun()

            st.subheader("Données et export")

            try:
                logger_inst = EventLogger()
                csv_file = logger_inst.export_csv(Path("data/export.csv"))
                logger_inst.close()
                with open(csv_file, "rb") as f:
                    st.download_button(
                        "Exporter le journal (CSV)",
                        f.read(),
                        file_name="drowsiguard_events.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            except Exception:
                pass

            st.caption("DrowsiGuard v0.2.0 · 100 % local et privé")


# ---------------------------------------------------------------------------
# Vérification des erreurs caméra
# ---------------------------------------------------------------------------

if st.session_state["camera_error"]:
    st.error("**Erreur lors de l'ouverture de la webcam**")
    st.code(st.session_state["camera_error"])
    st.info(
        "Vérifications recommandées :\n"
        "• Autorisez le Terminal / Streamlit dans **Réglages Système → Confidentialité → Caméra**\n"
        "• Fermez toute autre application susceptible d'utiliser la webcam (FaceTime, Zoom...)\n"
        "• Branchez correctement votre caméra USB externe si applicable"
    )
    st.stop()

if not st.session_state["camera_running"]:
    st.warning("La caméra est actuellement arrêtée. Ouvrez le menu **Contrôles** dans la barre de navigation pour reprendre.")
    st.stop()


# ---------------------------------------------------------------------------
# Choix du profil (uniquement au premier démarrage si profil existant)
# ---------------------------------------------------------------------------

pipeline: Pipeline = st.session_state["pipeline"]
camera: CameraCapture = st.session_state["camera"]

if not st.session_state["profile_choice_done"]:
    saved_profile = load_profile()
    if saved_profile is not None:
        with st.container(border=True):
            st.subheader("Profil morphologique enregistré trouvé")
            st.write(
                f"Calibration du **{saved_profile.calibration_timestamp[:10]}** "
                f"(sensibilité : {saved_profile.sensitivity}). Souhaitez-vous "
                "l'utiliser ou recalibrer pour cette session ?"
            )
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("Utiliser le profil enregistré", use_container_width=True):
                pipeline.load_existing_profile()
                st.session_state["profile_choice_done"] = True
                st.rerun()
        with col_p2:
            if st.button("Lancer une nouvelle calibration", use_container_width=True):
                pipeline.start_calibration()
                st.session_state["profile_choice_done"] = True
                st.rerun()
        st.stop()
    else:
        st.session_state["profile_choice_done"] = True
        st.rerun()


# ---------------------------------------------------------------------------
# Mise en page principale : statistiques | caméra | graphiques
# ---------------------------------------------------------------------------

# Trois colonnes équilibrées : un peu plus d'espace est réservé au flux caméra.
col_stats, col_cam, col_charts = st.columns([1, 1.35, 1], gap="medium")

with col_stats:
    st.subheader("Statistiques en direct")
    fatigue_ph = st.empty()
    metrics_ph = st.empty()
    counters_ph = st.empty()

with col_cam:
    header_ph = st.empty()
    video_ph = st.empty()
    quality_ph = st.empty()

with col_charts:
    st.subheader("Graphiques temps réel — 60 dernières secondes")
    g1_ph = st.empty()
    g2_ph = st.empty()
    g3_ph = st.empty()

# Titre du journal
st.subheader("Derniers événements détectés")
hist_ph = st.empty()


# ---------------------------------------------------------------------------
# Boucle vidéo fluide et performante
# ---------------------------------------------------------------------------

_frame_count = 0
_CHART_REFRESH = 6  # Rafraîchir Plotly toutes les ~200 ms pour une réactivité optimale sans freeze
_PANEL_REFRESH = 3  # Rafraîchir les métriques numériques toutes les ~100 ms

consecutive_drops = 0
MAX_CONSECUTIVE_DROPS = 30  # Tolérance aux micro-sauts de trames

while st.session_state["camera_running"]:
    ret, frame = camera.read()
    if not ret or frame is None:
        consecutive_drops += 1
        if consecutive_drops >= MAX_CONSECUTIVE_DROPS:
            st.error("Flux caméra indisponible après plusieurs tentatives. Vérifiez votre webcam.")
            _stop_camera()
            break
        time.sleep(0.02)
        continue

    consecutive_drops = 0
    try:
        annotated, status = pipeline.process(frame)
    except Exception:
        time.sleep(0.01)
        continue

    _frame_count += 1

    session_dur = time.time() - (st.session_state["session_start"] or time.time())

    # 1. En-tête (toutes les 15 frames)
    if _frame_count % 15 == 1:
        sys_status = "SURVEILLANCE ACTIVE" if status.is_calibrated else "EN CALIBRATION"
        with header_ph.container():
            render_header(sys_status, session_dur)

    # 2. Flux caméra (rafraîchi à chaque frame)
    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    video_ph.image(rgb, channels="RGB", **{_IMAGE_WIDTH_OPTION: True})

    # Statut qualité sous la vidéo
    with quality_ph.container():
        render_quality_badge(status.quality)

# 3. Statistiques dans la colonne gauche
    if status.state_result is not None:
        result = status.state_result

        # Détection front montant alerte Danger
        if result.level == AlertLevel.DANGER:
            if st.session_state.get("prev_alert_level") != AlertLevel.DANGER:
                st.session_state["alert_count"] += 1
        st.session_state["prev_alert_level"] = result.level

        # Historisation
        st.session_state["ear_history"].append(status.ear)
        st.session_state["mar_history"].append(status.mar)
        st.session_state["perclos_history"].append(result.perclos)
        st.session_state["score_history"].append(result.score)

        # Rendu des widgets latéraux
        if _frame_count % _PANEL_REFRESH == 0:
            with fatigue_ph.container():
                render_fatigue_section(result)

            with metrics_ph.container():
                render_metrics_cards(
                    result=result,
                    ear=status.ear,
                    mar=status.mar,
                    pitch=status.pitch,
                    ear_history=st.session_state["ear_history"],
                    mar_history=st.session_state["mar_history"],
                    perclos_history=st.session_state["perclos_history"],
                    thresholds=status.thresholds,
                )

            with counters_ph.container():
                render_counters_bar(result, st.session_state["alert_count"])

    elif status.calibration is not None:
        with fatigue_ph.container():
            render_calibration_screen(status.calibration)
        metrics_ph.empty()
        counters_ph.empty()

    # 4. Graphiques Plotly empilés dans la colonne droite
    if _frame_count % _CHART_REFRESH == 0 and status.thresholds is not None:
        thr = status.thresholds
        if st.session_state["ear_history"]:
            fig_ear = ear_chart(st.session_state["ear_history"], thr)
            g1_ph.plotly_chart(fig_ear, use_container_width=True, config=PLOTLY_CONFIG)

        if st.session_state["mar_history"]:
            fig_mar = mar_chart(st.session_state["mar_history"], thr)
            g2_ph.plotly_chart(fig_mar, use_container_width=True, config=PLOTLY_CONFIG)

        if st.session_state["score_history"]:
            fig_ps = perclos_score_chart(
                st.session_state["perclos_history"],
                st.session_state["score_history"],
            )
            g3_ph.plotly_chart(fig_ps, use_container_width=True, config=PLOTLY_CONFIG)

    # 5. Journal des événements (toutes les 40 frames)
    if _frame_count % 40 == 0:
        log_reader = EventLogger()
        history = log_reader.get_history(limit=8)
        log_reader.close()
        if history:
            rows = []
            for r in history:
                rows.append(
                    {
                        "Horodatage": r.timestamp[:19].replace("T", " "),
                        "Événement": r.event_type.upper(),
                        "Niveau": r.level,
                        "Score": f"{r.score:.0f}/100" if r.score is not None else "—",
                        "Détails / Causes": r.causes,
                    }
                )
            with hist_ph.container():
                st.dataframe(rows, use_container_width=True, hide_index=True)

    time.sleep(0.01)
