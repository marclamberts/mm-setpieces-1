"""SetPlayPro — thin router entry point."""
from __future__ import annotations

import base64
import hashlib
import os
import time
import urllib.parse
from pathlib import Path

import streamlit as st

from mm_setpieces_1.styles import inject_app_style
from mm_setpieces_1.utils import DATA_VERSION

from sections._shared import APP_SECTIONS, FILTER_PREFIXES, reset_current_filters
from sections.home import render_home
from sections.corners import render_corners
from sections.freekicks import render_freekicks
from sections.throwins import render_throwins
from sections.hops import render_hops
from sections.league_comparison import render_league_comparison
from sections.delay import render_delay
from sections.match_prep import render_match_prep
from sections.data_justification import render_data_justification
from sections.takers import render_takers
from sections.routines import render_routines
from sections.impact import render_impact
from sections.defensive import render_defensive
from sections.trends import render_trends
from sections.intel_card import render_intel_card

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "setplaypro-logo.jpg"

SECTION_ICONS = {
    "Home": "⌂",
    "Corners": "⚽",
    "Freekicks": "🎯",
    "Throw-ins": "↗",
    "HOPS": "🏃",
    "League Comparison": "📊",
    "Delay Analysis": "⏱",
    "Match Prep": "📋",
    "Data Justification": "📖",
    "Takers": "👤",
    "Routines": "📖",
    "Impact Score": "🏆",
    "Defensive": "🛡",
    "Trends": "📈",
    "Intel Card": "🗂",
}

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Michael Mackin Set Piece",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_app_style()


# ---------------------------------------------------------------------------
# Token-based auth (persists across page loads / nav clicks)
# ---------------------------------------------------------------------------

def _auth_token() -> str:
    """Hourly HMAC token. When no password set, uses 'open' as secret."""
    secret = os.environ.get("SETPLAYPRO_PASSWORD") or "open"
    hour = int(time.time() // 3600)
    return hashlib.sha256(f"{secret}{hour}".encode()).hexdigest()[:16]


def _check_auth_token(tok: str) -> bool:
    secret = os.environ.get("SETPLAYPRO_PASSWORD") or "open"
    for offset in range(-12, 1):  # accept tokens up to 12 hours old
        hour = int(time.time() // 3600) + offset
        if tok == hashlib.sha256(f"{secret}{hour}".encode()).hexdigest()[:16]:
            return True
    return False


def _password_required() -> bool:
    try:
        pw = st.secrets.get("SETPLAYPRO_PASSWORD") or os.environ.get("SETPLAYPRO_PASSWORD")
    except Exception:
        pw = os.environ.get("SETPLAYPRO_PASSWORD")
    return bool(pw)


def _expected_password() -> str | None:
    try:
        return st.secrets.get("SETPLAYPRO_PASSWORD") or os.environ.get("SETPLAYPRO_PASSWORD")
    except Exception:
        return os.environ.get("SETPLAYPRO_PASSWORD")


def _check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True
    # Check URL token (persists after top-nav link clicks)
    tok = st.query_params.get("tok", "")
    if tok and _check_auth_token(tok):
        st.session_state["authenticated"] = True
        return True
    _render_landing()
    return False


def _render_landing() -> None:
    """Full-page login screen."""
    pw_required = _password_required()
    expected = _expected_password()

    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"], [data-testid="stDecoration"],
            footer, #MainMenu { display: none !important; visibility: hidden !important; height: 0 !important; }
            html, body, .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"], .main {
                background: #0f1117 !important; overflow: hidden !important;
            }
            .block-container {
                width: 100vw !important; max-width: 100vw !important;
                height: 100vh !important; min-height: 100vh !important;
                padding: 0 !important; display: flex !important;
                flex-direction: column !important; align-items: center !important;
                justify-content: center !important; gap: .9rem !important;
                background: #0f1117 !important; overflow: hidden !important;
            }
            .block-container > div { width: min(360px, 76vw) !important; }
            [data-baseweb="input"] > div {
                background: #1e2230 !important;
                border: 1px solid rgba(255,255,255,0.12) !important;
                border-radius: 7px !important;
            }
            [data-baseweb="input"] input { color: #f1f5f9 !important; -webkit-text-fill-color: #f1f5f9 !important; }
            div.stButton > button {
                background: #22c55e !important; border: 0 !important;
                color: #052e16 !important; font-weight: 700 !important;
                border-radius: 7px !important; min-height: 42px !important;
            }
            div.stButton > button:hover { background: #16a34a !important; color: #ffffff !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=300)
    else:
        st.markdown("## SetPlay**Pro**")

    if pw_required:
        pwd = st.text_input("Password", type="password", key="login_pwd",
                            label_visibility="collapsed", placeholder="Enter password")
        if st.button("Enter portal", key="portal_submit", use_container_width=True):
            if pwd == expected:
                st.session_state["authenticated"] = True
                st.query_params["tok"] = _auth_token()
                st.query_params["section"] = "Home"
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        if st.button("Go to portal", key="portal_submit", use_container_width=True):
            st.session_state["authenticated"] = True
            st.query_params["tok"] = _auth_token()
            st.query_params["section"] = "Home"
            st.rerun()


# ---------------------------------------------------------------------------
# Top navigation bar
# ---------------------------------------------------------------------------

def _logo_b64() -> str:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return ""


def _render_topnav(section: str) -> None:
    token = _auth_token()
    logo_b64 = _logo_b64()

    if logo_b64:
        brand_inner = f'<img src="data:image/jpeg;base64,{logo_b64}" alt="logo">'
    else:
        brand_inner = "<span>SetPlay<strong>Pro</strong></span>"

    links_html = ""
    for sec in APP_SECTIONS:
        icon = SECTION_ICONS.get(sec, "•")
        active_cls = " mm-active" if sec == section else ""
        href = f"?tok={urllib.parse.quote(token)}&section={urllib.parse.quote(sec)}"
        links_html += (
            f'<a href="{href}" class="mm-topbar-link{active_cls}">'
            f'{icon}&thinsp;{sec}</a>'
        )

    home_href = f"?tok={urllib.parse.quote(token)}&section=Home"

    ctx_rows = st.session_state.get("ctx_row_count", "")
    ctx_html = ""
    if section != "Home" and ctx_rows:
        ctx_html = f'<div class="mm-topbar-right"><span class="mm-topbar-ctx">{ctx_rows}</span></div>'

    st.markdown(
        f"""
        <nav class="mm-topbar">
            <a class="mm-topbar-brand" href="{home_href}">{brand_inner}</a>
            <div class="mm-topbar-links">{links_html}</div>
            {ctx_html}
        </nav>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Inline reset button
# ---------------------------------------------------------------------------

def _render_reset_button(section: str) -> None:
    _, right = st.columns([10, 1])
    with right:
        if st.button("↺ Reset", key=f"reset_{section}", help="Reset all filters"):
            reset_current_filters(section)
            st.rerun()


# ---------------------------------------------------------------------------
# URL routing
# ---------------------------------------------------------------------------

def _current_section() -> str:
    raw = st.query_params.get("section", "")
    if raw in APP_SECTIONS:
        return raw
    return st.session_state.get("section", "Home")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if not _check_password():
    st.stop()

# Ensure sidebar is fully hidden
st.markdown(
    "<style>"
    "section[data-testid='stSidebar'],button[data-testid='collapsedControl']"
    "{display:none!important;width:0!important;min-width:0!important}"
    "</style>",
    unsafe_allow_html=True,
)

section = _current_section()
st.session_state["section"] = section

_render_topnav(section)

if section != "Home":
    _render_reset_button(section)

if section == "Home":
    render_home()
elif section == "Corners":
    render_corners()
elif section == "Freekicks":
    render_freekicks()
elif section == "Throw-ins":
    render_throwins()
elif section == "HOPS":
    render_hops()
elif section == "League Comparison":
    render_league_comparison()
elif section == "Delay Analysis":
    render_delay()
elif section == "Match Prep":
    render_match_prep()
elif section == "Takers":
    render_takers()
elif section == "Routines":
    render_routines()
elif section == "Impact Score":
    render_impact()
elif section == "Defensive":
    render_defensive()
elif section == "Trends":
    render_trends()
elif section == "Intel Card":
    render_intel_card()
elif section == "Data Justification":
    render_data_justification()
