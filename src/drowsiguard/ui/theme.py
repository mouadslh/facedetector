"""
Module ui.theme — Système de design et charte graphique de DrowsiGuard.

Thème clair : fond gris doux, surfaces blanches, texte ardoise et accent bleu modéré.

Couleurs d'état (sémantiques, exclusivement réservées au niveau de fatigue) :
- Normal : #22C55E
- Vigilance : #F59E0B
- Danger : #EF4444
"""

from __future__ import annotations

from drowsiguard.state import AlertLevel

# ---------------------------------------------------------------------------
# Constantes de couleurs (60 / 30 / 10)
# ---------------------------------------------------------------------------

COLOR_DOMINANT = "#F5F7FA"
COLOR_SECONDARY = "#FFFFFF"
COLOR_ACCENT = "#2878C7"

# Couleurs d'accompagnement
COLOR_TEXT_PRIMARY = "#182230"
COLOR_TEXT_MUTED = "#667085"
COLOR_BORDER = "#E2E7EE"

# Couleurs d'état (sémantiques pour la somnolence)
COLOR_STATE_NORMAL = "#22C55E"
COLOR_STATE_VIGILANCE = "#F59E0B"
COLOR_STATE_DANGER = "#EF4444"

# Association de niveau d'alerte -> couleur
ALERT_COLORS: dict[AlertLevel, str] = {
    AlertLevel.NORMAL: COLOR_STATE_NORMAL,
    AlertLevel.VIGILANCE: COLOR_STATE_VIGILANCE,
    AlertLevel.DANGER: COLOR_STATE_DANGER,
}

ALERT_BG_COLORS: dict[AlertLevel, str] = {
    AlertLevel.NORMAL: "rgba(34, 197, 94, 0.12)",
    AlertLevel.VIGILANCE: "rgba(245, 158, 11, 0.15)",
    AlertLevel.DANGER: "rgba(239, 68, 68, 0.20)",
}

ALERT_ICONS: dict[AlertLevel, str] = {
    AlertLevel.NORMAL: "✓",
    AlertLevel.VIGILANCE: "!",
    AlertLevel.DANGER: "!",
}


def get_alert_color(level: AlertLevel | str) -> str:
    """Retourne le code hexadécimal associé à un niveau d'alerte."""
    if isinstance(level, str):
        try:
            level = AlertLevel(level)
        except ValueError:
            return COLOR_STATE_NORMAL
    return ALERT_COLORS.get(level, COLOR_STATE_NORMAL)


# ---------------------------------------------------------------------------
# CSS Global injecté dans Streamlit
# ---------------------------------------------------------------------------

GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0,0');

:root {{ color-scheme: light; }}

/* Reset et base */
html, body, [class*="st-"], .stApp {{
    background-color: {COLOR_DOMINANT} !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}}

/* Chiffres tabulaires */
.tabular-nums {{
    font-variant-numeric: tabular-nums;
}}

/* Espacement container principal */
.block-container {{
    padding-top: 2.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 98% !important;
}}

/* Keep the first content row clear of Streamlit's top toolbar. */
[data-testid="stMainBlockContainer"] {{
    padding-top: 2.25rem !important;
}}

/* Titres */
h1, h2, h3, h4 {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    letter-spacing: -0.02em;
}}

.section-title {{
    color: {COLOR_ACCENT} !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    margin: 1.35rem 0 0.7rem 0 !important;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.material-symbols-rounded {{
    font-family: 'Material Symbols Rounded';
    font-weight: normal;
    font-style: normal;
    font-size: 1.1rem;
    line-height: 1;
    vertical-align: middle;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    direction: ltr;
    -webkit-font-smoothing: antialiased;
}}

/* Cartes stylées */
.dg-card {{
    background: {COLOR_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 3px 12px rgba(16, 24, 40, 0.06);
    transition: border-color 200ms ease, box-shadow 200ms ease;
}}

.dg-card:hover {{
    border-color: rgba(40, 120, 199, 0.45);
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {COLOR_SECONDARY} !important;
    border-right: 1px solid {COLOR_BORDER} !important;
}}

/* Widgets and data tables remain readable on the light canvas. */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background: #FFFFFF !important;
    border: 1px solid {COLOR_BORDER} !important;
    border-radius: 10px !important;
}}

div[data-testid="stAlert"] {{ border-radius: 10px !important; }}
input, textarea {{ color: {COLOR_TEXT_PRIMARY} !important; }}

/* Compact metric values so numbers and durations fit in the narrow side column. */
[data-testid="stMetricValue"] > div {{
    font-size: 1.3rem !important;
    line-height: 1.15 !important;
    white-space: normal !important;
    overflow: visible !important;
    overflow-wrap: anywhere !important;
    text-overflow: clip !important;
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem !important;
}}

/* Boutons principaux et secondaires */
.stButton > button {{
    background: {COLOR_SECONDARY} !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    border: 1px solid {COLOR_BORDER} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1rem !important;
    transition: all 200ms ease !important;
}}

.stButton > button:hover {{
    background: #EDF5FC !important;
    border-color: {COLOR_ACCENT} !important;
    color: {COLOR_ACCENT} !important;
    box-shadow: 0 2px 8px rgba(40, 120, 199, 0.12) !important;
}}

.stButton > button[kind="primary"] {{
    background: {COLOR_ACCENT} !important;
    color: {COLOR_DOMINANT} !important;
    border: none !important;
    font-weight: 700 !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: #1E66AA !important;
    box-shadow: 0 2px 10px rgba(40, 120, 199, 0.18) !important;
}}

/* Selectbox et widgets */
.stSelectbox div[data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    border-color: {COLOR_BORDER} !important;
    color: {COLOR_TEXT_PRIMARY} !important;
    border-radius: 8px !important;
}}

/* Animation clignotement doux pour le bandeau d'alerte DANGER */
@keyframes softPulse {{
    0% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.85; transform: scale(0.995); }}
    100% {{ opacity: 1; transform: scale(1); }}
}}

.danger-banner {{
    animation: softPulse 1.2s infinite ease-in-out;
}}
</style>
"""
