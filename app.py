"""SetPlayPro — thin router entry point.

All render logic lives in sections/. This file handles:
  - Streamlit page config
  - Authentication (password gate)
  - URL routing (section encoded in ?section= query param)
  - Sidebar navigation
  - Section dispatch
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from mm_setpieces_1.styles import inject_app_style, inject_sidebar_css
from mm_setpieces_1.utils import DATA_VERSION

from sections._shared import APP_SECTIONS, FILTER_PREFIXES, reset_current_filters
from sections.home import render_home
from sections.corners import render_corners
from sections.freekicks import render_freekicks
from sections.throwins import render_throwins
from sections.hops import render_hops
from sections.league_comparison import render_league_comparison
from sections.delay import render_delay

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "setplaypro-logo.jpg"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Michael Mackin Set Piece",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",  # collapsed on landing; expanded after auth
)

inject_app_style()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _check_password() -> bool:
    """Return True when the user has successfully authenticated this session."""
    if st.session_state.get("authenticated"):
        return True

    # Read password from Streamlit secrets, env var, or fall back to open access
    expected = None
    try:
        expected = st.secrets.get("SETPLAYPRO_PASSWORD") or os.environ.get("SETPLAYPRO_PASSWORD")
    except Exception:
        expected = os.environ.get("SETPLAYPRO_PASSWORD")

    _render_landing(password_required=bool(expected), expected=expected)
    return False


def _render_landing(password_required: bool, expected: str | None) -> None:
    """Full-page landing / login screen (no sidebar)."""
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"],
            [data-testid="stDecoration"],
            footer, #MainMenu {
                display: none !important; visibility: hidden !important; height: 0 !important;
            }
            html, body, .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"], .main {
                background: #ffffff !important; overflow: hidden !important;
            }
            .block-container {
                width: 100vw !important; max-width: 100vw !important;
                height: 100vh !important; min-height: 100vh !important;
                padding: 0 !important; display: flex !important;
                flex-direction: column !important; align-items: center !important;
                justify-content: center !important; gap: .9rem !important;
                background: #ffffff !important; overflow: hidden !important;
            }
            .block-container > div { width: min(380px, 76vw) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=320)
    else:
        st.markdown("## SetPlay**Pro**")

    if password_required:
        pwd = st.text_input("Password", type="password", key="login_pwd", label_visibility="collapsed", placeholder="Enter password")
        if st.button("Enter portal", key="portal_submit", use_container_width=True):
            if pwd == expected:
                st.session_state["authenticated"] = True
                st.session_state["section"] = "Home"
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        if st.button("Go to portal", key="portal_submit", use_container_width=True):
            st.session_state["authenticated"] = True
            st.session_state["section"] = "Home"
            st.rerun()


# ---------------------------------------------------------------------------
# URL routing
# ---------------------------------------------------------------------------

def _read_section_from_url() -> str | None:
    """Read ?section= from the URL, return it if it is a valid section name."""
    try:
        raw = st.query_params.get("section")
        if raw and raw in APP_SECTIONS:
            return raw
    except Exception:
        pass
    return None


def _write_section_to_url(section: str) -> None:
    try:
        st.query_params["section"] = section
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

def _render_sidebar() -> str:
    inject_sidebar_css()

    # Resolve pending navigation (from module buttons on Home)
    if "pending_section" in st.session_state:
        st.session_state["section_select"] = st.session_state.pop("pending_section")

    # On first load after auth, read section from URL
    if "section" not in st.session_state:
        url_section = _read_section_from_url()
        st.session_state["section"] = url_section or "Home"

    st.sidebar.markdown("### Pages")
    section = st.sidebar.radio(
        "Choose view",
        APP_SECTIONS,
        index=APP_SECTIONS.index(st.session_state.get("section_select", st.session_state["section"])),
        key="section_select",
        label_visibility="collapsed",
    )
    st.session_state["section"] = section
    _write_section_to_url(section)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    if section != "Home":
        if st.sidebar.button("Reset filters", key=f"reset_{section}", use_container_width=True):
            reset_current_filters(section)

    return section


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if not _check_password():
    st.stop()

# Ensure sidebar is visible after auth
st.markdown(
    "<style>section[data-testid='stSidebar'] { display: block !important; }</style>",
    unsafe_allow_html=True,
)

section = _render_sidebar()

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
