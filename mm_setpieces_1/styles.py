"""App-wide CSS — Dunks & Threes dark theme design system."""
from __future__ import annotations

import streamlit as st

# Design tokens — dark theme with green accent
GREEN      = "#22c55e"
GREEN_D    = "#16a34a"
GREEN_PAL  = "#052e16"
GREEN_MID  = "#166534"
NAVY       = "#0f1117"
SURFACE    = "#161922"
SURFACE_2  = "#1e2230"
INK        = "#f1f5f9"
MUTED      = "#6b7280"
MUTED_2    = "#9ca3af"
BORDER     = "rgba(255,255,255,0.08)"
BORDER_2   = "rgba(255,255,255,0.12)"
SIDEBAR_BG = "#0d0f14"

# Legacy aliases used by utils.py charts
BLACK    = "#0b0f14"
RED      = GREEN       # charts now render in green
RED_DARK = GREEN_D


def inject_sidebar_css() -> None:
    """No-op: sidebar CSS is included in inject_app_style."""
    pass


def inject_app_style() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

            /* ── Tokens ──────────────────────────────────────────────── */
            :root {{
                --c-bg:       {NAVY};
                --c-surface:  {SURFACE};
                --c-surface2: {SURFACE_2};
                --c-sidebar:  {SIDEBAR_BG};
                --c-ink:      {INK};
                --c-muted:    {MUTED};
                --c-muted2:   {MUTED_2};
                --c-border:   {BORDER};
                --c-green:    {GREEN};
                --c-green-d:  {GREEN_D};
                --c-green-p:  {GREEN_PAL};
                --c-navy:     {NAVY};
            }}

            /* ── Base ───────────────────────────────────────────────── */
            html, body, [class*="css"] {{
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-feature-settings: "cv02","cv03","cv04","cv11";
            }}
            .stApp {{
                background: {NAVY} !important;
                color: {INK} !important;
            }}
            footer, #MainMenu {{ visibility: hidden; height: 0; }}
            header[data-testid="stHeader"] {{
                background: {SIDEBAR_BG} !important;
                border-bottom: 1px solid {BORDER} !important;
                height: 2.4rem !important;
            }}
            header[data-testid="stHeader"]::before {{ background: transparent !important; }}
            .block-container {{
                max-width: 1520px !important;
                padding: .75rem 1.5rem 3rem !important;
            }}
            h1,h2,h3,h4,h5,h6 {{ color: {INK} !important; }}
            p, label, span {{ color: {MUTED_2}; }}

            /* ── Sidebar ────────────────────────────────────────────── */
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] {{
                background: {SIDEBAR_BG} !important;
                border-right: 1px solid {BORDER} !important;
                box-shadow: none !important;
                width: 15.5rem !important;
                min-width: 15.5rem !important;
                max-width: 15.5rem !important;
                color-scheme: dark !important;
            }}
            div[data-testid="stSidebar"] *,
            div[data-testid="stSidebar"] span,
            div[data-testid="stSidebar"] div,
            div[data-testid="stSidebar"] button,
            div[data-testid="stSidebar"] a,
            div[data-testid="stSidebar"] p,
            div[data-testid="stSidebar"] label {{ color: {MUTED_2} !important; }}

            /* Sidebar logo */
            div[data-testid="stSidebar"] [data-testid="stImage"] img {{
                border-radius: 4px;
            }}

            /* Sidebar section headings */
            div[data-testid="stSidebar"] h3 {{
                color: #374151 !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                letter-spacing: .2em !important;
                text-transform: uppercase !important;
                padding: 0 .2rem !important;
                margin: 1.2rem 0 .28rem !important;
            }}

            /* Nav radio → sidebar links (hide radio circles) */
            div[data-testid="stSidebar"] [role="radiogroup"] {{
                display: grid !important;
                gap: .08rem !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] > div:first-child,
            div[data-testid="stSidebar"] [role="radiogroup"] [data-baseweb="radio"] svg {{
                display: none !important;
                width: 0 !important;
                height: 0 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label > div {{
                gap: 0 !important;
                padding-left: 0 !important;
                margin-left: 0 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 5px !important;
                padding: .5rem .75rem !important;
                cursor: pointer;
                font-size: .84rem !important;
                font-weight: 400 !important;
                color: #6b7280 !important;
                transition: background .1s ease, color .1s ease !important;
                min-height: auto !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
                background: rgba(255,255,255,0.04) !important;
                color: #d1d5db !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
                background: rgba(34,197,94,0.10) !important;
                border-left: 2px solid {GREEN} !important;
                padding-left: calc(.75rem - 2px) !important;
                color: {GREEN} !important;
                font-weight: 600 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span,
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {{
                color: {GREEN} !important;
            }}

            /* Sidebar selects / inputs */
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div {{
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(255,255,255,0.09) !important;
                border-radius: 6px !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] span,
            div[data-testid="stSidebar"] [data-baseweb="select"] input,
            div[data-testid="stSidebar"] [data-baseweb="input"] input {{
                color: #d1d5db !important;
                -webkit-text-fill-color: #d1d5db !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] {{
                background: rgba(34,197,94,0.18) !important;
                border-radius: 4px !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] span {{
                color: #86efac !important;
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: rgba(255,255,255,0.06) !important;
                margin: .5rem 0 !important;
            }}

            /* Sidebar filter label / value */
            .mm-filter-card {{
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                border-radius: 5px !important;
            }}
            .mm-filter-label {{ color: #374151 !important; }}
            .mm-filter-value {{ color: #d1d5db !important; }}

            /* Sidebar reset button → ghost */
            div[data-testid="stSidebar"] div.stButton > button {{
                background: transparent !important;
                border: 1px solid rgba(34,197,94,0.25) !important;
                border-radius: 5px !important;
                color: #6b7280 !important;
                font-size: .77rem !important;
                font-weight: 600 !important;
                min-height: 32px !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] div.stButton > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.45) !important;
                color: #86efac !important;
            }}

            /* ── Main content inputs ────────────────────────────────── */
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER_2} !important;
                border-radius: 6px !important;
                box-shadow: none !important;
                color: {INK} !important;
                transition: border-color .12s ease, box-shadow .12s ease !important;
            }}
            [data-baseweb="select"] span,
            [data-baseweb="select"] input,
            [data-baseweb="input"] input,
            textarea {{
                color: {INK} !important;
                -webkit-text-fill-color: {INK} !important;
            }}
            [data-baseweb="select"] > div:focus-within,
            [data-baseweb="input"] > div:focus-within,
            textarea:focus {{
                border-color: {GREEN} !important;
                box-shadow: 0 0 0 3px rgba(34,197,94,0.12) !important;
            }}
            /* Tag / multiselect chips in main area */
            [data-baseweb="tag"] {{
                background: rgba(34,197,94,0.18) !important;
                border-radius: 4px !important;
            }}
            [data-baseweb="tag"] span {{ color: #86efac !important; }}

            /* Dropdown popover */
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER_2} !important;
                box-shadow: 0 10px 36px rgba(0,0,0,0.45) !important;
                border-radius: 8px !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: {MUTED_2} !important;
                -webkit-text-fill-color: {MUTED_2} !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"],
            div[data-baseweb="popover"] [role="option"]:hover {{
                background: rgba(34,197,94,0.10) !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"] *,
            div[data-baseweb="popover"] [role="option"]:hover * {{
                color: {INK} !important;
                -webkit-text-fill-color: {INK} !important;
            }}

            /* Radio / checkboxes in main area */
            div[data-testid="stRadio"] label,
            div[data-testid="stCheckbox"] label {{ color: {MUTED_2} !important; }}

            /* ── Hero ───────────────────────────────────────────────── */
            .mm-hero {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 8px !important;
                padding: 1.3rem 1.6rem 1.4rem !important;
                box-shadow: none !important;
                position: relative;
                overflow: hidden;
                margin-bottom: .9rem;
            }}
            .mm-hero::before {{
                content: "" !important;
                display: block !important;
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 2px !important;
                background: {GREEN} !important;
                border-radius: 8px 8px 0 0 !important;
            }}
            .mm-eyebrow {{
                color: #374151 !important;
                font-size: .65rem !important;
                font-weight: 700 !important;
                letter-spacing: .2em !important;
                text-transform: uppercase !important;
            }}
            .mm-title {{
                color: {INK} !important;
                font-size: clamp(1.7rem, 2.4vw, 2.55rem) !important;
                font-weight: 800 !important;
                letter-spacing: -.02em !important;
                line-height: 1.05 !important;
                margin: .18rem 0 .45rem !important;
            }}
            .mm-copy {{
                color: {MUTED} !important;
                font-size: .93rem !important;
                font-weight: 400 !important;
                max-width: 820px;
                line-height: 1.6;
            }}

            /* ── Section divider ────────────────────────────────────── */
            .mm-section {{
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 1rem !important;
                border-bottom: 1px solid {BORDER} !important;
                padding: 0 0 .45rem !important;
                margin: 1.4rem 0 .8rem !important;
                background: none !important;
                border-radius: 0 !important;
            }}
            .mm-section-title {{
                color: {MUTED_2} !important;
                font-size: .68rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .16em !important;
                display: inline-flex;
                align-items: center;
                gap: .42rem;
            }}
            .mm-section-title::before {{
                content: "" !important;
                display: inline-block !important;
                width: .3rem !important;
                height: .3rem !important;
                border-radius: 999px !important;
                background: {GREEN} !important;
                flex-shrink: 0;
            }}
            .mm-section-note {{
                color: {MUTED} !important;
                font-size: .76rem !important;
                font-weight: 400 !important;
            }}

            /* ── Card surfaces ──────────────────────────────────────── */
            .mm-feature-pill,
            .mm-insight-card,
            .mm-panel,
            .mm-stat-card,
            .mm-profile-card,
            .mm-kpi-card,
            .mm-rail-step,
            .mm-workflow-card,
            .mm-filter-summary,
            .mm-empty-state,
            div[data-testid="stMetric"],
            [data-testid="stDataFrameResizable"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                box-shadow: none !important;
            }}
            .mm-command-panel,
            .mm-read-card {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                box-shadow: none !important;
            }}
            .mm-command-title {{ color: {INK} !important; font-size: .92rem !important; font-weight: 700 !important; }}
            .mm-command-label {{ color: {MUTED} !important; font-size: .68rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: .08em !important; }}
            .mm-command-value {{ color: {MUTED_2} !important; font-size: .86rem !important; line-height: 1.38 !important; }}
            .mm-command-row {{ border-top-color: {BORDER} !important; }}
            .mm-read-title {{ color: {MUTED} !important; font-size: .65rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: .1em !important; }}
            .mm-read-value {{ color: {INK} !important; font-size: .88rem !important; font-weight: 700 !important; line-height: 1.35 !important; }}

            /* Feature pill */
            .mm-feature-pill {{
                border-left: 2px solid {GREEN} !important;
                padding: .78rem .9rem !important;
            }}
            .mm-feature-value {{
                color: {INK} !important;
                font-size: .98rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-feature-label {{
                color: {MUTED} !important;
                font-size: .65rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .07em !important;
                margin-top: .18rem !important;
            }}

            /* ── Home module nav cards ──────────────────────────────── */
            .mm-nav-card {{
                position: relative;
                overflow: hidden;
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 8px !important;
                padding: 1rem 1.05rem .78rem !important;
                min-height: 140px !important;
                box-shadow: none !important;
                transition: border-color .15s ease, background .15s ease !important;
            }}
            .mm-nav-card:hover {{
                transform: none !important;
                background: {SURFACE_2} !important;
                border-color: rgba(34,197,94,0.25) !important;
            }}
            .mm-nav-card::before {{
                content: "" !important;
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 2px !important;
                background: {GREEN} !important;
                border-radius: 8px 8px 0 0 !important;
            }}
            .mm-card-kicker {{
                color: {GREEN} !important;
                font-size: .62rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .14em !important;
                margin-bottom: .35rem !important;
            }}
            .mm-nav-title {{
                color: {INK} !important;
                font-size: .96rem !important;
                font-weight: 700 !important;
                margin-bottom: .28rem !important;
            }}
            .mm-nav-copy {{
                color: {MUTED} !important;
                font-size: .82rem !important;
                font-weight: 400 !important;
                line-height: 1.48 !important;
            }}
            .mm-nav-card-action {{
                margin-top: .35rem !important;
                margin-bottom: .85rem !important;
            }}
            .mm-nav-card-action div.stButton > button {{
                background: transparent !important;
                border: 1px solid {BORDER_2} !important;
                border-radius: 5px !important;
                color: {MUTED} !important;
                font-size: .76rem !important;
                font-weight: 600 !important;
                min-height: 28px !important;
                box-shadow: none !important;
            }}
            .mm-nav-card-action div.stButton > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.35) !important;
                color: {GREEN} !important;
                box-shadow: none !important;
            }}

            /* ── Insight card ───────────────────────────────────────── */
            .mm-insight-card {{
                padding: .82rem .95rem .82rem 1.1rem !important;
                min-height: auto !important;
                position: relative;
            }}
            .mm-insight-card::before {{
                content: "";
                position: absolute;
                left: 0; top: 0; bottom: 0;
                width: 2px;
                background: {GREEN};
                border-radius: 7px 0 0 7px;
            }}

            /* ── KPI / metric cards ─────────────────────────────────── */
            .mm-kpi-card,
            .mm-stat-card,
            div[data-testid="stMetric"] {{
                border-top: 2px solid {GREEN} !important;
                padding: .82rem .9rem !important;
            }}
            .mm-kpi-card.is-red,
            .mm-stat-card.is-red {{ border-top-color: #ef4444 !important; }}
            div[data-testid="stMetric"]::before {{ display: none !important; }}
            .mm-kpi-label,
            .mm-stat-label,
            div[data-testid="stMetricLabel"] p {{
                color: {MUTED} !important;
                font-size: .65rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .08em !important;
            }}
            .mm-kpi-value,
            .mm-stat-value,
            div[data-testid="stMetricValue"] {{
                color: {INK} !important;
                font-size: 1.45rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.01em !important;
            }}
            .mm-kpi-help {{
                color: {MUTED} !important;
                font-size: .7rem !important;
                line-height: 1.3 !important;
                margin-top: .25rem !important;
            }}

            /* ── Profile / workflow ─────────────────────────────────── */
            .mm-profile-card {{ border-left: 2px solid {GREEN} !important; }}
            .mm-profile-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .85rem !important; }}
            .mm-profile-copy {{ color: {MUTED} !important; font-size: .77rem !important; line-height: 1.38 !important; }}
            .mm-rail-step::before {{ background: {GREEN} !important; border-radius: 7px 0 0 7px !important; }}
            .mm-rail-label {{ color: {MUTED} !important; font-size: .6rem !important; letter-spacing: .1em !important; text-transform: uppercase !important; font-weight: 700 !important; }}
            .mm-rail-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .82rem !important; }}
            .mm-workflow-step {{ color: {GREEN} !important; font-size: .63rem !important; font-weight: 700 !important; letter-spacing: .12em !important; text-transform: uppercase !important; }}
            .mm-workflow-title {{ color: {INK} !important; font-weight: 700 !important; }}
            .mm-workflow-copy {{ color: {MUTED} !important; font-size: .83rem !important; line-height: 1.45 !important; }}
            .mm-panel-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .92rem !important; }}
            .mm-panel-copy {{ color: {MUTED} !important; font-size: .81rem !important; line-height: 1.42 !important; }}

            /* ── Filter summary / chips ─────────────────────────────── */
            .mm-filter-summary {{ padding: .72rem .95rem !important; }}
            .mm-filter-count {{
                color: {INK} !important;
                font-size: .9rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-chip,
            .mm-tiny {{
                background: rgba(255,255,255,0.06) !important;
                border: 1px solid {BORDER_2} !important;
                color: {MUTED_2} !important;
                border-radius: 5px !important;
                font-size: .71rem !important;
                font-weight: 600 !important;
            }}
            .mm-chip strong {{ color: {INK} !important; }}

            /* ── Empty state ────────────────────────────────────────── */
            .mm-empty-state {{ border-left: 2px solid {GREEN} !important; }}
            .mm-empty-title {{ color: {INK} !important; font-weight: 700 !important; }}
            .mm-empty-copy {{ color: {MUTED} !important; }}

            /* ── Data tables ────────────────────────────────────────── */
            [data-testid="stDataFrameResizable"] {{
                border-radius: 7px !important;
                overflow: hidden !important;
                border: 1px solid {BORDER} !important;
                box-shadow: none !important;
                background: {SURFACE} !important;
            }}
            [data-testid="stDataFrame"] > div {{ border-radius: 7px !important; overflow: hidden !important; }}
            [data-testid="stDataFrame"] iframe {{ border: 0 !important; }}
            .mm-table-note {{ color: {MUTED} !important; font-size: .76rem !important; }}

            /* ── Charts / images ────────────────────────────────────── */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .6rem !important;
                box-shadow: none !important;
            }}

            /* ── Tabs — segment control ─────────────────────────────── */
            div[data-testid="stTabs"] [role="tablist"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .22rem !important;
                box-shadow: none !important;
                gap: .1rem !important;
                margin-bottom: .7rem !important;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 5px !important;
                color: {MUTED} !important;
                font-size: .8rem !important;
                font-weight: 500 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 30px !important;
                padding: .24rem .88rem !important;
                transition: background .1s ease, color .1s ease !important;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: rgba(255,255,255,0.05) !important;
                color: {INK} !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: {GREEN} !important;
                color: #052e16 !important;
                box-shadow: none !important;
                font-weight: 700 !important;
            }}

            /* ── Primary buttons ────────────────────────────────────── */
            div.stButton > button {{
                background: {GREEN} !important;
                border: 0 !important;
                border-radius: 6px !important;
                color: #052e16 !important;
                font-size: .81rem !important;
                font-weight: 700 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 36px !important;
                box-shadow: none !important;
                transition: background .12s ease !important;
            }}
            div.stButton > button:hover {{
                background: {GREEN_D} !important;
                color: #ffffff !important;
            }}
            div.stButton > button:active {{ transform: translateY(1px) !important; }}

            /* Download → outline */
            div[data-testid="stDownloadButton"] > button {{
                background: transparent !important;
                border: 1px solid {BORDER_2} !important;
                border-radius: 6px !important;
                color: {MUTED_2} !important;
                font-size: .81rem !important;
                font-weight: 600 !important;
                min-height: 36px !important;
                box-shadow: none !important;
            }}
            div[data-testid="stDownloadButton"] > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.35) !important;
                color: {GREEN} !important;
            }}

            /* ── Alerts ─────────────────────────────────────────────── */
            div[data-testid="stAlert"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
            }}
            div[data-testid="stAlert"] * {{ color: {MUTED_2} !important; }}
            div[data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{ color: {MUTED} !important; }}

            /* ── Sliders ────────────────────────────────────────────── */
            .stSlider [data-testid="stTickBar"] {{ opacity: .4; }}

            /* ── Tabular numbers everywhere ─────────────────────────── */
            div[data-testid="stMetricValue"],
            .mm-kpi-value,
            .mm-stat-value,
            .mm-feature-value,
            .mm-filter-count {{
                font-variant-numeric: tabular-nums !important;
            }}

            /* ── Landing screen (login) ─────────────────────────────── */
            .mm-landing-shell {{ background: {NAVY} !important; }}

            /* ── Responsive ─────────────────────────────────────────── */
            @media (max-width: 760px) {{
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div,
                div[data-testid="stSidebar"] {{
                    width: 100% !important;
                    min-width: 100% !important;
                    max-width: 100% !important;
                }}
                .mm-title {{ font-size: 1.7rem !important; }}
                .block-container {{ padding: .65rem .85rem 2rem !important; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
