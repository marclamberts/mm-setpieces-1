"""App-wide CSS — modern premium analytics design."""
from __future__ import annotations

import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────────────
GREEN      = "#22c55e"
GREEN_D    = "#16a34a"
GREEN_PAL  = "#052e16"
NAVY       = "#0f1117"
SURFACE    = "#161922"
SURFACE_2  = "#1e2230"
SURFACE_3  = "#252d3d"
INK        = "#f1f5f9"
MUTED      = "#6b7280"
MUTED_2    = "#9ca3af"
BORDER     = "rgba(255,255,255,0.07)"
BORDER_2   = "rgba(255,255,255,0.11)"
SIDEBAR_BG = "#0d0f14"
AMBER      = "#f59e0b"

BLACK    = "#0b0f14"
RED      = GREEN
RED_DARK = GREEN_D


def inject_sidebar_css() -> None:
    pass


def inject_app_style() -> None:  # noqa: C901
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

            /* ── Tokens ─────────────────────────────────────────── */
            :root {{
                --c-bg:      {NAVY};
                --c-s1:      {SURFACE};
                --c-s2:      {SURFACE_2};
                --c-s3:      {SURFACE_3};
                --c-ink:     {INK};
                --c-muted:   {MUTED};
                --c-muted2:  {MUTED_2};
                --c-border:  {BORDER};
                --c-b2:      {BORDER_2};
                --c-green:   {GREEN};
                --c-green-d: {GREEN_D};
                --c-amber:   {AMBER};
            }}

            /* ── Base ───────────────────────────────────────────── */
            html, body, [class*="css"] {{
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-feature-settings: "cv02","cv03","cv04","cv11","tnum";
            }}
            .stApp {{ background: {NAVY} !important; color: #ffffff !important; }}
            footer, #MainMenu {{ visibility: hidden; height: 0; }}
            header[data-testid="stHeader"],
            button[data-testid="collapsedControl"],
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] {{
                display: none !important; height: 0 !important;
                width: 0 !important; min-width: 0 !important;
            }}
            .block-container {{
                max-width: 1560px !important;
                padding: 78px 1.6rem 4rem !important;
            }}
            h1,h2,h3,h4,h5,h6 {{ color: #ffffff !important; }}
            p {{ color: #d1d5db; }}
            label {{ color: #d1d5db !important; }}
            span {{ color: inherit; }}

            /* ── Top navigation bar ─────────────────────────────── */
            .mm-topbar {{
                position: fixed;
                top: 0; left: 0; right: 0;
                height: 58px;
                background: #1a1d23;
                border-bottom: 1px solid rgba(255,255,255,0.10);
                display: flex;
                align-items: center;
                padding: 0 1.8rem;
                z-index: 9999;
                gap: 1.6rem;
            }}
            .mm-topbar-brand {{
                display: flex; align-items: center;
                gap: .5rem;
                text-decoration: none;
                flex-shrink: 0;
            }}
            .mm-topbar-brand img {{
                height: 30px; width: auto; border-radius: 3px;
            }}
            .mm-topbar-brand span {{
                color: #ffffff; font-size: .95rem; font-weight: 700;
                white-space: nowrap;
            }}
            .mm-topbar-brand span strong {{ color: {GREEN}; }}
            .mm-topbar-links {{
                display: flex; align-items: stretch;
                gap: 0; overflow-x: auto; flex: 1; height: 58px;
                scrollbar-width: none; -ms-overflow-style: none;
            }}
            .mm-topbar-links::-webkit-scrollbar {{ display: none; }}
            .mm-topbar-links a,
            .mm-topbar-link {{
                display: flex; align-items: center;
                color: #9ca3af;
                font-size: .84rem; font-weight: 500;
                padding: 0 .95rem;
                text-decoration: none !important;
                white-space: nowrap;
                border-bottom: 2px solid transparent;
                transition: color .12s, border-color .12s;
                letter-spacing: .015em;
            }}
            .mm-topbar-links a:hover,
            .mm-topbar-link:hover {{
                color: #ffffff;
                text-decoration: none !important;
            }}
            .mm-topbar-links a.mm-active,
            .mm-topbar-link.mm-active {{
                color: #ffffff;
                font-weight: 600;
                border-bottom-color: {GREEN};
            }}
            .mm-topbar-right {{
                display: flex; align-items: center;
                gap: .6rem; flex-shrink: 0; margin-left: .4rem;
            }}
            .mm-topbar-ctx {{
                color: {MUTED_2};
                font-size: .72rem; font-weight: 500;
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 4px;
                padding: .22rem .65rem;
                letter-spacing: .01em;
                white-space: nowrap;
            }}

            /* ── Main-area inputs ───────────────────────────────── */
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: #2a2d35 !important;
                border: 1px solid rgba(255,255,255,0.12) !important;
                border-radius: 5px !important;
                box-shadow: none !important;
            }}
            [data-baseweb="select"] span,
            [data-baseweb="select"] input,
            [data-baseweb="input"] input,
            textarea {{
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }}
            [data-baseweb="select"] > div:focus-within,
            [data-baseweb="input"] > div:focus-within {{
                border-color: {GREEN} !important;
                box-shadow: 0 0 0 3px rgba(34,197,94,0.10) !important;
            }}
            [data-baseweb="tag"] {{
                background: rgba(34,197,94,0.15) !important; border-radius: 3px !important;
            }}
            [data-baseweb="tag"] span {{ color: #86efac !important; }}
            [data-baseweb="tag"] [role="button"] {{ color: #86efac !important; }}

            /* Dropdown popover */
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: #2a2d35 !important;
                border: 1px solid rgba(255,255,255,0.12) !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.55) !important;
                border-radius: 6px !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: #d1d5db !important;
                -webkit-text-fill-color: #d1d5db !important;
                background: transparent !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"],
            div[data-baseweb="popover"] [role="option"]:hover {{
                background: rgba(34,197,94,0.08) !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"] *,
            div[data-baseweb="popover"] [role="option"]:hover * {{
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }}

            /* Radio buttons */
            div[data-testid="stRadio"] label {{ color: #d1d5db !important; }}
            div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {{
                border-color: rgba(255,255,255,0.25) !important;
            }}
            div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] > div:first-child {{
                border-color: {GREEN} !important; background: {GREEN} !important;
            }}

            /* Checkboxes */
            div[data-testid="stCheckbox"] label {{ color: #d1d5db !important; }}
            div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child {{
                border-color: rgba(255,255,255,0.25) !important; background: #2a2d35 !important;
            }}

            /* Sliders */
            div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {{
                background: {GREEN} !important;
            }}
            div[data-testid="stSlider"] [data-baseweb="slider"] div:first-child div {{
                background: {SURFACE_3} !important;
            }}

            /* Expander */
            div[data-testid="stExpander"] {{
                background: #222428 !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 5px !important;
            }}
            div[data-testid="stExpander"] summary {{
                color: #d1d5db !important; font-weight: 600 !important;
                font-size: .79rem !important;
            }}
            div[data-testid="stExpander"] summary:hover {{ color: #ffffff !important; }}
            div[data-testid="stExpander"] svg {{ color: #d1d5db !important; }}

            /* ── Page header ────────────────────────────────────── */
            .mm-page-header {{
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 1.2rem;
                margin: 0 0 .85rem;
                padding: 0 0 .7rem;
                border-bottom: 1px solid {BORDER};
            }}
            .mm-page-title {{
                color: #ffffff !important;
                font-size: 1.4rem !important;
                font-weight: 800 !important;
                letter-spacing: -.032em !important;
                line-height: 1 !important;
            }}
            .mm-page-scope {{
                color: {MUTED} !important;
                font-size: .72rem !important;
                font-weight: 500 !important;
                white-space: nowrap;
                letter-spacing: .01em;
            }}
            .mm-page-scope strong {{
                color: {MUTED_2} !important;
                font-weight: 600 !important;
            }}

            /* ── Section divider ────────────────────────────────── */
            .mm-section {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                padding: .1rem 0 .4rem .72rem;
                margin: 1.2rem 0 .6rem;
                border-bottom: 1px solid {BORDER};
                border-left: 2px solid {GREEN};
            }}
            .mm-section-title {{
                color: {MUTED_2} !important;
                font-size: .7rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .13em !important;
            }}
            .mm-section-title::before {{ display: none !important; }}
            .mm-section-note {{
                color: {MUTED} !important;
                font-size: .72rem !important;
            }}

            /* ── Filter panel ───────────────────────────────────── */
            .mm-filter-panel {{
                background: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: .6rem .85rem .4rem;
                margin-bottom: .9rem;
            }}
            .mm-filter-panel-label {{
                color: {MUTED} !important;
                font-size: .57rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .13em !important;
                margin-bottom: .3rem !important;
                display: block;
            }}

            /* ── KPI deck ───────────────────────────────────────── */
            .mm-kpi-deck {{
                display: grid;
                grid-template-columns: repeat(6,minmax(0,1fr));
                gap: 1px;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                overflow: hidden;
                margin: .8rem 0 .6rem;
            }}
            .mm-kpi-card {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .75rem .85rem !important;
                min-height: 72px;
            }}
            .mm-kpi-card.is-red {{ background: rgba(245,158,11,0.06) !important; }}
            .mm-kpi-label {{
                color: {MUTED} !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .12em !important;
                margin-bottom: .24rem !important;
            }}
            .mm-kpi-value {{
                color: #ffffff !important;
                font-size: 1.4rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.03em !important;
                line-height: 1 !important;
            }}
            .mm-kpi-help {{
                color: {MUTED} !important;
                font-size: .65rem !important;
                line-height: 1.3 !important;
                margin-top: .2rem !important;
            }}

            /* ── Read strip ─────────────────────────────────────── */
            .mm-read-strip {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: 1px;
                background: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                overflow: hidden;
                margin: .6rem 0 1rem;
            }}
            .mm-read-card {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .8rem .9rem !important;
            }}
            .mm-read-title {{
                color: {MUTED} !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                letter-spacing: .12em !important;
                text-transform: uppercase !important;
                margin-bottom: .2rem !important;
            }}
            .mm-read-value {{
                color: #ffffff !important;
                font-size: .88rem !important;
                font-weight: 700 !important;
                line-height: 1.35 !important;
                overflow-wrap: anywhere;
            }}

            /* ── Feature strip ──────────────────────────────────── */
            .mm-feature-strip {{
                display: grid;
                grid-template-columns: repeat(4,minmax(0,1fr));
                gap: 1px;
                background: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                overflow: hidden;
                margin: .65rem 0 .9rem;
            }}
            .mm-feature-pill {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .8rem .9rem !important;
            }}
            .mm-feature-value {{
                color: #ffffff !important;
                font-size: 1.1rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-feature-label {{
                color: {MUTED} !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .1em !important;
                margin-top: .14rem !important;
            }}

            /* ── Stat grid ──────────────────────────────────────── */
            .mm-stat-grid {{
                display: grid;
                grid-template-columns: repeat(6,minmax(0,1fr));
                gap: 1px;
                background: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                overflow: hidden;
                margin: .65rem 0 .85rem;
            }}
            .mm-stat-card {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .75rem .8rem !important;
            }}
            .mm-stat-card.is-red {{ background: rgba(245,158,11,0.06) !important; }}
            .mm-stat-label {{
                color: {MUTED} !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .1em !important;
                margin-bottom: .14rem !important;
            }}
            .mm-stat-value {{
                color: #ffffff !important;
                font-size: 1.25rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                line-height: 1.05 !important;
                letter-spacing: -.02em !important;
            }}

            /* ── Workflow rail ──────────────────────────────────── */
            .mm-workflow-rail {{
                display: grid;
                grid-template-columns: repeat(4,minmax(0,1fr));
                gap: 1px;
                background: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                overflow: hidden;
                margin: .62rem 0 .8rem;
            }}
            .mm-rail-step {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .7rem .75rem !important;
                position: relative;
            }}
            .mm-rail-step::before {{
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 2px;
                background: {GREEN};
            }}
            .mm-rail-label {{
                color: {MUTED} !important;
                font-size: .58rem !important; font-weight: 700 !important;
                letter-spacing: .12em !important; text-transform: uppercase !important;
                margin-bottom: .12rem !important;
            }}
            .mm-rail-title {{
                color: #ffffff !important;
                font-weight: 700 !important; font-size: .82rem !important;
            }}

            /* ── Workflow grid ──────────────────────────────────── */
            .mm-workflow-grid {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: .55rem;
                margin: .72rem 0 1rem;
            }}
            .mm-workflow-card {{
                background: #222428 !important;
                border: 1px solid {BORDER} !important;
                border-radius: 5px !important;
                padding: .9rem !important;
            }}
            .mm-workflow-step {{
                color: {GREEN} !important;
                font-size: .58rem !important; font-weight: 700 !important;
                letter-spacing: .14em !important; text-transform: uppercase !important;
                margin-bottom: .26rem !important;
            }}
            .mm-workflow-title {{
                color: #ffffff !important;
                font-weight: 700 !important;
                margin-bottom: .2rem !important;
            }}
            .mm-workflow-copy {{
                color: {MUTED} !important;
                font-size: .82rem !important; line-height: 1.45 !important;
            }}

            /* ── Profile strip ──────────────────────────────────── */
            .mm-profile-strip {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: 1px;
                background: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                overflow: hidden;
                margin: .62rem 0;
            }}
            .mm-profile-card {{
                background: #222428 !important;
                border: none !important;
                border-radius: 0 !important;
                padding: .75rem .85rem !important;
                border-left: 2px solid {GREEN} !important;
            }}
            .mm-profile-title {{
                color: #ffffff !important;
                font-weight: 700 !important; font-size: .85rem !important;
                margin-bottom: .14rem !important;
            }}
            .mm-profile-copy {{
                color: {MUTED} !important;
                font-size: .77rem !important; line-height: 1.38 !important;
                overflow-wrap: anywhere;
            }}

            /* ── Scout shell / Command center ───────────────────── */
            .mm-scout-shell {{
                display: grid;
                grid-template-columns: minmax(0,1.28fr) minmax(300px,.72fr);
                gap: .88rem;
                margin: .8rem 0 1rem;
            }}
            .mm-command-center {{
                display: grid;
                grid-template-columns: minmax(0,1.05fr) minmax(310px,.95fr);
                gap: .82rem;
                margin: .8rem 0 1.1rem;
            }}
            .mm-panel {{
                background: #222428 !important;
                border: 1px solid {BORDER} !important;
                border-radius: 5px !important;
                padding: .9rem !important;
            }}
            .mm-panel-title {{
                color: #ffffff !important;
                font-weight: 700 !important; font-size: .9rem !important;
                margin-bottom: .16rem !important;
            }}
            .mm-panel-copy {{
                color: {MUTED} !important;
                font-size: .8rem !important; line-height: 1.42 !important;
                margin-bottom: .72rem !important;
            }}
            .mm-command-panel {{
                background: #2a2d35 !important;
                border: 1px solid {BORDER} !important;
                border-radius: 5px !important;
                padding: 1rem !important;
            }}
            .mm-command-title {{
                color: #ffffff !important;
                font-size: .78rem !important; font-weight: 700 !important;
                letter-spacing: .1em !important; text-transform: uppercase !important;
                margin-bottom: .65rem !important;
            }}
            .mm-command-row {{
                display: grid;
                grid-template-columns: 7rem minmax(0,1fr);
                gap: .65rem;
                padding: .55rem 0;
                border-top: 1px solid {BORDER};
            }}
            .mm-command-label {{
                color: {MUTED} !important;
                font-size: .6rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .1em !important;
            }}
            .mm-command-value {{
                color: {MUTED_2} !important;
                font-size: .85rem !important; line-height: 1.38 !important;
                overflow-wrap: anywhere;
            }}

            /* ── Insight card ───────────────────────────────────── */
            .mm-insight-card {{
                background: #222428 !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 5px !important;
                padding: .75rem .9rem .75rem 1rem !important;
                color: #d1d5db;
                line-height: 1.48;
                font-size: .86rem;
            }}
            .mm-insight-card strong {{ color: #ffffff !important; }}

            /* ── Native st.metric ───────────────────────────────── */
            div[data-testid="stMetric"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-top: 2px solid {GREEN} !important;
                border-radius: 6px !important;
                padding: .75rem .9rem .6rem !important;
                box-shadow: none !important;
            }}
            div[data-testid="stMetric"]::before {{ display: none !important; }}
            div[data-testid="stMetricLabel"] p {{
                color: {MUTED} !important;
                font-size: .57rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .13em !important;
                margin-bottom: .25rem !important;
            }}
            div[data-testid="stMetricValue"] {{
                color: #ffffff !important;
                font-size: 1.55rem !important; font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.035em !important;
                line-height: 1 !important;
            }}
            div[data-testid="stMetricDelta"] {{ display: none; }}

            /* ── Tables ─────────────────────────────────────────── */
            [data-testid="stDataFrameResizable"] {{
                border-radius: 5px !important;
                overflow: hidden !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                box-shadow: none !important;
                background: #222428 !important;
            }}
            [data-testid="stDataFrame"] > div {{
                border-radius: 5px !important; overflow: hidden !important;
            }}
            [data-testid="stDataFrame"] iframe {{ border: 0 !important; }}
            .mm-table-note {{
                color: #9ca3af !important; font-size: .74rem !important;
            }}

            /* ── Charts / images ────────────────────────────────── */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: #222428 !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 5px !important;
                padding: .5rem !important;
                box-shadow: none !important;
            }}

            /* ── Tabs ───────────────────────────────────────────── */
            div[data-testid="stTabs"] [role="tablist"] {{
                background: #1e2026 !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 5px !important;
                padding: .18rem !important;
                box-shadow: none !important;
                gap: .06rem !important;
                margin-bottom: .65rem !important;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 4px !important;
                color: #9ca3af !important;
                font-size: .76rem !important; font-weight: 500 !important;
                letter-spacing: .005em !important;
                min-height: 28px !important; padding: .2rem .85rem !important;
                transition: background .1s, color .1s !important;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: rgba(255,255,255,0.07) !important;
                color: #ffffff !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: #2e3038 !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                box-shadow: none !important;
            }}

            /* ── Primary buttons ────────────────────────────────── */
            div.stButton > button {{
                background: #2e3038 !important;
                border: 1px solid rgba(255,255,255,0.14) !important;
                border-radius: 5px !important;
                color: #ffffff !important;
                font-size: .8rem !important; font-weight: 600 !important;
                letter-spacing: .01em !important;
                min-height: 36px !important;
                box-shadow: none !important;
            }}
            div.stButton > button:hover {{
                background: #383b45 !important;
                border-color: rgba(255,255,255,0.22) !important;
                color: #ffffff !important;
            }}
            div.stButton > button:active {{ transform: translateY(1px) !important; }}

            /* Download button */
            div[data-testid="stDownloadButton"] > button {{
                background: #2e3038 !important;
                border: 1px solid rgba(255,255,255,0.14) !important;
                border-radius: 5px !important;
                color: #ffffff !important;
                font-size: .8rem !important; font-weight: 600 !important;
                min-height: 36px !important;
            }}
            div[data-testid="stDownloadButton"] > button:hover {{
                background: #383b45 !important;
                border-color: rgba(255,255,255,0.22) !important;
                color: #ffffff !important;
            }}

            /* ── Alerts ─────────────────────────────────────────── */
            div[data-testid="stAlert"] {{
                background: #222428 !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 5px !important;
            }}
            div[data-testid="stAlert"] * {{ color: #d1d5db !important; }}
            div[data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{ color: #9ca3af !important; }}

            /* ── Filter summary ─────────────────────────────────── */
            .mm-filter-summary {{
                background: transparent !important;
                border: none !important;
                border-bottom: 1px solid {BORDER} !important;
                border-radius: 0 !important;
                display: flex; align-items: center;
                justify-content: space-between; gap: .8rem;
                padding: 0 0 .65rem !important;
                margin: 0 0 .9rem;
                flex-wrap: wrap;
            }}
            .mm-filter-count {{
                color: {MUTED} !important;
                font-size: .76rem !important; font-weight: 600 !important;
                font-variant-numeric: tabular-nums !important;
                white-space: nowrap;
            }}
            .mm-filter-chips {{
                display: flex; flex-wrap: wrap;
                justify-content: flex-end; gap: .3rem;
            }}
            .mm-chip, .mm-tiny {{
                display: inline-flex; align-items: center; gap: .2rem;
                background: rgba(255,255,255,0.05) !important;
                border: 1px solid {BORDER} !important;
                color: {MUTED} !important;
                border-radius: 3px !important;
                padding: .18rem .45rem;
                font-size: .67rem !important; font-weight: 600 !important;
                line-height: 1.2; overflow-wrap: anywhere;
            }}
            .mm-chip strong {{ color: {MUTED_2} !important; }}
            .mm-filter-card {{
                background: rgba(255,255,255,0.03) !important;
                border: 1px solid {BORDER} !important;
                border-radius: 4px !important;
                padding: .38rem .48rem;
                margin: .2rem 0;
            }}
            .mm-filter-label {{
                color: {MUTED} !important;
                font-size: .52rem !important; font-weight: 700 !important;
                letter-spacing: .1em !important; text-transform: uppercase !important;
                margin-bottom: .12rem !important;
            }}
            .mm-filter-value {{
                color: {MUTED} !important;
                font-size: .72rem !important; font-weight: 600 !important;
                line-height: 1.25; overflow-wrap: anywhere;
            }}

            /* ── Empty state ────────────────────────────────────── */
            .mm-empty-state {{
                background: #222428 !important;
                border: 1px solid {BORDER} !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 5px !important;
                padding: .9rem 1rem !important;
                margin: .75rem 0 1rem;
            }}
            .mm-empty-title {{
                color: #ffffff !important; font-weight: 700 !important;
                margin-bottom: .18rem !important;
            }}
            .mm-empty-copy {{
                color: {MUTED} !important; font-size: .83rem !important;
                line-height: 1.45 !important;
            }}

            /* ── Hero (compact page-header re-use) ──────────────── */
            .mm-hero {{ margin-bottom: .9rem; }}
            .mm-eyebrow {{
                color: {MUTED} !important;
                font-size: .58rem !important; font-weight: 700 !important;
                letter-spacing: .2em !important; text-transform: uppercase !important;
            }}
            .mm-title {{
                color: #ffffff !important;
                font-size: 1.4rem !important;
                font-weight: 800 !important;
                letter-spacing: -.032em !important;
                line-height: 1 !important;
            }}
            .mm-copy {{
                color: {MUTED} !important;
                font-size: .78rem !important;
                font-weight: 500 !important;
                letter-spacing: .01em;
            }}

            /* ── Database stats bar ─────────────────────────────── */
            .mm-dbstats-bar {{
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 0;
                border-bottom: 1px solid {BORDER};
                margin: 0 0 1.2rem;
                padding-bottom: 0;
            }}
            .mm-dbstat {{
                display: flex;
                flex-direction: column;
                padding: .2rem 1.2rem .45rem 0;
                margin-right: 1.2rem;
                border-right: 1px solid {BORDER};
                flex-shrink: 0;
            }}
            .mm-dbstat:last-child {{
                border-right: none; margin-right: 0;
            }}
            .mm-dbstat-val {{
                color: #ffffff !important;
                font-size: 1.25rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.03em;
                line-height: 1.1;
            }}
            .mm-dbstat-lbl {{
                color: {MUTED} !important;
                font-size: .57rem !important;
                font-weight: 600 !important;
                text-transform: uppercase !important;
                letter-spacing: .1em !important;
            }}
            .mm-dbstat-icon {{ display: none; }}

            /* ── Module cards ───────────────────────────────────── */
            .mm-mod-card {{
                background: #222428;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 5px;
                padding: .8rem .9rem .7rem;
                min-height: 100px;
                position: relative;
                cursor: pointer;
                transition: border-color .15s;
            }}
            .mm-mod-card:hover {{
                border-color: {BORDER_2};
            }}
            .mm-mod-card + div > button,
            .mm-mod-card ~ div div.stButton > button {{
                position: absolute !important;
                inset: 0 !important;
                opacity: 0 !important;
                width: 100% !important;
                height: 100% !important;
                min-height: unset !important;
                border-radius: 5px !important;
                cursor: pointer !important;
            }}
            .mm-mod-icon {{
                font-size: 1.15rem;
                margin-bottom: .38rem;
                line-height: 1;
                opacity: .75;
            }}
            .mm-mod-title {{
                color: #ffffff !important;
                font-size: .88rem !important;
                font-weight: 700 !important;
                margin-bottom: .2rem !important;
                letter-spacing: -.012em;
            }}
            .mm-mod-desc {{
                color: {MUTED} !important;
                font-size: .76rem !important;
                line-height: 1.44 !important;
            }}
            .mm-mod-cta {{ display: none; }}

            /* Legacy nav cards */
            .mm-nav-card {{
                background: #222428;
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: .9rem 1rem .78rem;
                min-height: 118px;
                position: relative;
                cursor: pointer;
                transition: border-color .15s, background .15s;
            }}
            .mm-nav-card:hover {{
                background: #2a2d35;
                border-color: rgba(34,197,94,0.22);
            }}
            .mm-card-kicker {{
                color: {GREEN} !important;
                font-size: .58rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .16em !important;
                margin-bottom: .3rem !important;
            }}
            .mm-nav-title {{
                color: #ffffff !important;
                font-size: .9rem !important; font-weight: 700 !important;
                margin-bottom: .22rem !important;
            }}
            .mm-nav-copy {{
                color: {MUTED} !important;
                font-size: .78rem !important; font-weight: 400 !important;
                line-height: 1.45 !important;
            }}
            .mm-nav-card-action {{
                margin-top: .3rem !important;
                margin-bottom: .8rem !important;
            }}
            .mm-nav-card-action div.stButton > button {{
                background: #2e3038 !important;
                border: 1px solid rgba(255,255,255,0.14) !important;
                color: #ffffff !important;
                font-size: .72rem !important; font-weight: 600 !important;
                min-height: 26px !important;
            }}
            .mm-nav-card-action div.stButton > button:hover {{
                background: #383b45 !important;
                border-color: rgba(255,255,255,0.22) !important;
                color: #ffffff !important;
            }}

            /* ── Filter bar ─────────────────────────────────────── */
            .mm-filter-bar {{
                background: rgba(255,255,255,0.02);
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: .6rem .85rem;
                margin: 0 0 .9rem;
            }}
            .mm-filter-bar-label {{
                color: {MUTED};
                font-size: .58rem; font-weight: 700;
                text-transform: uppercase; letter-spacing: .12em;
                white-space: nowrap;
            }}

            /* ── Tabular nums everywhere ────────────────────────── */
            div[data-testid="stMetricValue"],
            .mm-kpi-value, .mm-stat-value, .mm-feature-value,
            .mm-filter-count, .mm-dbstat-val {{
                font-variant-numeric: tabular-nums !important;
            }}

            /* ── Responsive ─────────────────────────────────────── */
            @media (max-width: 1100px) {{
                .mm-kpi-deck, .mm-stat-grid {{
                    grid-template-columns: repeat(3,minmax(0,1fr));
                }}
                .mm-scout-shell, .mm-command-center {{
                    grid-template-columns: 1fr;
                }}
            }}
            @media (max-width: 760px) {{
                .mm-topbar {{ padding: 0 .9rem; gap: .8rem; }}
                .mm-topbar-links a {{ padding: 0 .5rem; font-size: .72rem; }}
                .block-container {{ padding: 58px .85rem 2rem !important; }}
                .mm-kpi-deck, .mm-stat-grid {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
                .mm-read-strip, .mm-profile-strip {{ grid-template-columns: 1fr; }}
                .mm-feature-strip, .mm-workflow-rail {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
