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
import threading
import uuid
from pathlib import Path

import streamlit as st
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# Ajouter src/ au path Python
sys.path.insert(0, str(Path(__file__).parent / "src"))

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


# ---------------------------------------------------------------------------
# Initialisation de la session
# ---------------------------------------------------------------------------


def _init_session() -> None:
    defaults = {
        "session_id": uuid.uuid4().hex,
        "frame_state": {"lock": threading.Lock(), "status": None, "frame_count": 0, "error": None},
        "pipeline": None,
        "sensitivity": "Normale",
        "muted": True,
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
    try:
        session_dir = Path("data/sessions") / st.session_state["session_id"]
        session_dir.mkdir(parents=True, exist_ok=True)
        st.session_state["pipeline"] = Pipeline(
            sensitivity=st.session_state["sensitivity"],
            muted=True,  # L'audio du serveur ne doit jamais alerter d'autres élèves.
            profile_path=session_dir / "profile.json",
            db_path=session_dir / "events.db",
        )
        st.session_state["camera_running"] = True
        st.session_state["camera_error"] = None
        if st.session_state["session_start"] is None:
            st.session_state["session_start"] = time.time()
    except Exception as exc:
        st.session_state["pipeline"] = None
        st.session_state["camera_error"] = str(exc)
        st.session_state["camera_running"] = False


def _stop_camera() -> None:
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

            st.caption("Les alertes sonores sont désactivées en mode hébergé pour ne pas jouer sur le serveur.")

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

            st.caption("La webcam se démarre depuis le lecteur vidéo. Cliquez sur Start et autorisez l'accès dans le navigateur.")

            st.subheader("Données et export")

            try:
                session_dir = Path("data/sessions") / st.session_state["session_id"]
                logger_inst = EventLogger(session_dir / "events.db")
                csv_file = logger_inst.export_csv(session_dir / "export.csv")
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

            st.caption("DrowsiGuard v0.3.0 · webcam du navigateur")


# ---------------------------------------------------------------------------
# Vérification des erreurs caméra
# ---------------------------------------------------------------------------

if st.session_state["camera_error"]:
    st.error("**Erreur lors de l'ouverture de la webcam**")
    st.code(st.session_state["camera_error"])
    st.info("La session n'a pas pu démarrer. Rechargez la page ou contactez l'enseignant.")
    st.stop()

if not st.session_state["camera_running"]:
    st.warning("La session est arrêtée. Rechargez la page pour recommencer.")
    st.stop()


# ---------------------------------------------------------------------------
# Choix du profil (uniquement au premier démarrage si profil existant)
# ---------------------------------------------------------------------------

pipeline: Pipeline = st.session_state["pipeline"]

if not st.session_state["profile_choice_done"]:
    session_dir = Path("data/sessions") / st.session_state["session_id"]
    saved_profile = load_profile(session_dir / "profile.json")
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
    def process_browser_frame(frame: av.VideoFrame) -> av.VideoFrame:
        try:
            image = frame.to_ndarray(format="bgr24")
            annotated, status = pipeline.process(image)
            state = frame_state
            with state["lock"]:
                state["status"] = status
                state["frame_count"] += 1
            return av.VideoFrame.from_ndarray(annotated, format="bgr24")
        except Exception as exc:
            state = frame_state
            with state["lock"]:
                state["error"] = str(exc)
            return frame

    frame_state = st.session_state["frame_state"]
    rtc_config = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    webrtc_streamer(
        key=f"camera-{st.session_state['session_id']}",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=process_browser_frame,
        rtc_configuration=rtc_config,
        media_stream_constraints={"video": {"width": 640, "height": 480}, "audio": False},
        async_processing=False,
    )
    camera_hint_ph = st.empty()
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
_last_ui_frame = 0
_CHART_REFRESH = 6  # Rafraîchir Plotly toutes les ~200 ms pour une réactivité optimale sans freeze
_PANEL_REFRESH = 3  # Rafraîchir les métriques numériques toutes les ~100 ms

consecutive_drops = 0
MAX_CONSECUTIVE_DROPS = 30  # Tolérance aux micro-sauts de trames

while st.session_state["camera_running"]:
    state = st.session_state["frame_state"]
    with state["lock"]:
        status = state["status"]
        _frame_count = state["frame_count"]
        frame_error = state["error"]
    if frame_error:
        st.error(f"Erreur de traitement vidéo : {frame_error}")
    if status is None:
        camera_hint_ph.info("Cliquez sur Start dans le lecteur vidéo et autorisez l'accès à votre webcam.")
        time.sleep(0.1)
        continue
    camera_hint_ph.empty()

    if _frame_count == _last_ui_frame:
        time.sleep(0.03)
        continue
    _last_ui_frame = _frame_count

    session_dur = time.time() - (st.session_state["session_start"] or time.time())

    # 1. En-tête (toutes les 15 frames)
    if _frame_count % 15 == 1:
        sys_status = "SURVEILLANCE ACTIVE" if status.is_calibrated else "EN CALIBRATION"
        with header_ph.container():
            render_header(sys_status, session_dur)

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
            g1_ph.plotly_chart(fig_ear, width="stretch", config=PLOTLY_CONFIG)

        if st.session_state["mar_history"]:
            fig_mar = mar_chart(st.session_state["mar_history"], thr)
            g2_ph.plotly_chart(fig_mar, width="stretch", config=PLOTLY_CONFIG)

        if st.session_state["score_history"]:
            fig_ps = perclos_score_chart(
                st.session_state["perclos_history"],
                st.session_state["score_history"],
            )
            g3_ph.plotly_chart(fig_ps, width="stretch", config=PLOTLY_CONFIG)

    # 5. Journal des événements (toutes les 40 frames)
    if _frame_count % 40 == 0:
        session_dir = Path("data/sessions") / st.session_state["session_id"]
        log_reader = EventLogger(session_dir / "events.db")
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
                st.dataframe(rows, width="stretch", hide_index=True)

    time.sleep(0.01)
