"""App-wide CSS — Dunks & Threes inspired design system."""
from __future__ import annotations

import streamlit as st

# Design tokens
ORANGE     = "#ea580c"
ORANGE_D   = "#c2410c"
ORANGE_PAL = "#fff7ed"
NAVY       = "#0f172a"
INK        = "#111827"
MUTED      = "#6b7280"
BORDER     = "#e5e7eb"
BG         = "#f8f9fa"
SURFACE    = "#ffffff"
SIDEBAR_BG = "#111827"

# Legacy aliases used by utils.py
BLACK    = "#0b0f14"
RED      = ORANGE      # charts/plots now use orange
RED_DARK = ORANGE_D


def inject_sidebar_css() -> None:
    """No-op: sidebar CSS is now included in inject_app_style."""
    pass


def inject_app_style() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

            /* ── Tokens ──────────────────────────────────────────────── */
            :root {{
                --c-bg:      {BG};
                --c-surface: {SURFACE};
                --c-sidebar: {SIDEBAR_BG};
                --c-ink:     {INK};
                --c-muted:   {MUTED};
                --c-border:  {BORDER};
                --c-orange:  {ORANGE};
                --c-orange-d:{ORANGE_D};
                --c-orange-p:{ORANGE_PAL};
                --c-navy:    {NAVY};
            }}

            /* ── Base ───────────────────────────────────────────────── */
            html, body, [class*="css"] {{
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                font-feature-settings: "cv02","cv03","cv04","cv11";
            }}
            .stApp {{
                background: var(--c-bg) !important;
                color: var(--c-ink) !important;
            }}
            footer, #MainMenu {{ visibility: hidden; height: 0; }}
            header[data-testid="stHeader"] {{
                background: transparent !important;
                height: 2.4rem !important;
            }}
            header[data-testid="stHeader"]::before {{ background: transparent !important; }}
            .block-container {{
                max-width: 1480px !important;
                padding: .75rem 1.5rem 3rem !important;
            }}
            h1,h2,h3,h4,h5,h6,p,label,span {{ color: var(--c-ink); }}

            /* ── Sidebar ────────────────────────────────────────────── */
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] {{
                background: {SIDEBAR_BG} !important;
                border-right: 1px solid rgba(255,255,255,0.06) !important;
                box-shadow: 4px 0 24px rgba(0,0,0,0.22) !important;
                width: 16rem !important;
                min-width: 16rem !important;
                max-width: 16rem !important;
                color-scheme: dark !important;
            }}
            div[data-testid="stSidebar"] *,
            div[data-testid="stSidebar"] span,
            div[data-testid="stSidebar"] div,
            div[data-testid="stSidebar"] button,
            div[data-testid="stSidebar"] a,
            div[data-testid="stSidebar"] p,
            div[data-testid="stSidebar"] label {{ color: #d1d5db !important; }}

            /* Sidebar section headings */
            div[data-testid="stSidebar"] h3 {{
                color: #4b5563 !important;
                font-size: .6rem !important;
                font-weight: 700 !important;
                letter-spacing: .18em !important;
                text-transform: uppercase !important;
                padding: 0 .2rem !important;
                margin: 1.1rem 0 .3rem !important;
            }}

            /* Logo image */
            div[data-testid="stSidebar"] [data-testid="stImage"] img {{
                border-radius: 6px;
            }}

            /* Nav radio → sidebar links (hide radio circles) */
            div[data-testid="stSidebar"] [role="radiogroup"] {{
                display: grid !important;
                gap: .12rem !important;
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
                border-radius: 6px !important;
                padding: .54rem .78rem !important;
                cursor: pointer;
                font-size: .875rem !important;
                font-weight: 400 !important;
                color: #9ca3af !important;
                transition: background .1s ease, color .1s ease !important;
                min-height: auto !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
                background: rgba(255,255,255,0.05) !important;
                color: #f3f4f6 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
                background: rgba(234,88,12,0.12) !important;
                border-left: 2px solid {ORANGE} !important;
                padding-left: calc(.78rem - 2px) !important;
                color: #fdba74 !important;
                font-weight: 600 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span,
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {{
                color: #fdba74 !important;
            }}

            /* Sidebar selects / inputs */
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div {{
                background: rgba(255,255,255,0.05) !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 6px !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] span,
            div[data-testid="stSidebar"] [data-baseweb="select"] input,
            div[data-testid="stSidebar"] [data-baseweb="input"] input {{
                color: #e5e7eb !important;
                -webkit-text-fill-color: #e5e7eb !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] {{
                background: rgba(234,88,12,0.22) !important;
                border-radius: 4px !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] span {{
                color: #fed7aa !important;
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: rgba(255,255,255,0.07) !important;
                margin: .55rem 0 !important;
            }}

            /* Sidebar reset button → ghost outline */
            div[data-testid="stSidebar"] div.stButton > button {{
                background: transparent !important;
                border: 1px solid rgba(234,88,12,0.30) !important;
                border-radius: 6px !important;
                color: #9ca3af !important;
                font-size: .78rem !important;
                font-weight: 600 !important;
                min-height: 33px !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] div.stButton > button:hover {{
                background: rgba(234,88,12,0.10) !important;
                border-color: rgba(234,88,12,0.50) !important;
                color: #fed7aa !important;
            }}

            /* ── Main content inputs ────────────────────────────────── */
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: {SURFACE} !important;
                border: 1.5px solid #d1d5db !important;
                border-radius: 7px !important;
                box-shadow: none !important;
                transition: border-color .12s ease, box-shadow .12s ease !important;
            }}
            [data-baseweb="select"] > div:focus-within,
            [data-baseweb="input"] > div:focus-within,
            textarea:focus {{
                border-color: {ORANGE} !important;
                box-shadow: 0 0 0 3px rgba(234,88,12,0.10) !important;
            }}
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                box-shadow: 0 10px 36px rgba(15,23,42,0.12) !important;
                border-radius: 8px !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: {INK} !important;
                -webkit-text-fill-color: {INK} !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"],
            div[data-baseweb="popover"] [role="option"]:hover {{
                background: {ORANGE_PAL} !important;
            }}

            /* ── Hero ───────────────────────────────────────────────── */
            .mm-hero {{
                background: {NAVY} !important;
                border: 0 !important;
                border-radius: 10px !important;
                padding: 1.4rem 1.65rem 1.5rem !important;
                box-shadow: 0 4px 24px rgba(0,0,0,0.18) !important;
                position: relative;
                overflow: hidden;
                margin-bottom: .9rem;
            }}
            .mm-hero::before {{
                content: "" !important;
                display: block !important;
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 3px !important;
                background: {ORANGE} !important;
                border-radius: 10px 10px 0 0 !important;
            }}
            .mm-eyebrow {{
                color: #4b5563 !important;
                font-size: .67rem !important;
                font-weight: 700 !important;
                letter-spacing: .2em !important;
                text-transform: uppercase !important;
            }}
            .mm-title {{
                color: #f9fafb !important;
                font-size: clamp(1.85rem, 2.6vw, 2.75rem) !important;
                font-weight: 800 !important;
                letter-spacing: -.02em !important;
                line-height: 1.05 !important;
                margin: .2rem 0 .5rem !important;
            }}
            .mm-copy {{
                color: #9ca3af !important;
                font-size: .94rem !important;
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
                padding: 0 0 .5rem !important;
                margin: 1.5rem 0 .85rem !important;
                background: none !important;
                border-radius: 0 !important;
            }}
            .mm-section-title {{
                color: {INK} !important;
                font-size: .72rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .14em !important;
                display: inline-flex;
                align-items: center;
                gap: .45rem;
            }}
            .mm-section-title::before {{
                content: "" !important;
                display: inline-block !important;
                width: .32rem !important;
                height: .32rem !important;
                border-radius: 999px !important;
                background: {ORANGE} !important;
                box-shadow: none !important;
                flex-shrink: 0;
            }}
            .mm-section-note {{
                color: {MUTED} !important;
                font-size: .78rem !important;
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
                border-radius: 8px !important;
                box-shadow: 0 1px 3px rgba(15,23,42,0.05) !important;
            }}
            .mm-command-panel,
            .mm-read-card {{
                background: {NAVY} !important;
                border: 1px solid rgba(255,255,255,0.07) !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 16px rgba(0,0,0,0.20) !important;
            }}
            .mm-command-title,
            .mm-read-value {{ color: #f9fafb !important; }}
            .mm-command-label,
            .mm-read-title {{ color: #6b7280 !important; }}
            .mm-command-row {{ border-top-color: rgba(255,255,255,0.07) !important; }}
            .mm-command-value {{ color: #e5e7eb !important; }}

            /* Feature pill */
            .mm-feature-pill {{
                border-left: 3px solid {ORANGE} !important;
                padding: .82rem .92rem !important;
            }}
            .mm-feature-value {{
                color: {INK} !important;
                font-size: 1rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-feature-label {{
                color: {MUTED} !important;
                font-size: .66rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .07em !important;
                margin-top: .2rem !important;
            }}

            /* ── Home module nav cards ──────────────────────────────── */
            .mm-nav-card {{
                position: relative;
                overflow: hidden;
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 10px !important;
                padding: 1.05rem 1.1rem .82rem !important;
                min-height: 145px !important;
                box-shadow: 0 1px 3px rgba(15,23,42,0.04) !important;
                transition: box-shadow .15s ease, border-color .15s ease, transform .15s ease !important;
            }}
            .mm-nav-card:hover {{
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 18px rgba(15,23,42,0.08) !important;
                border-color: rgba(234,88,12,0.28) !important;
            }}
            .mm-nav-card::before {{
                content: "" !important;
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 3px !important;
                background: {ORANGE} !important;
                border-radius: 10px 10px 0 0 !important;
            }}
            .mm-card-kicker {{
                color: {ORANGE} !important;
                font-size: .64rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .12em !important;
                margin-bottom: .38rem !important;
            }}
            .mm-nav-title {{
                color: {INK} !important;
                font-size: 1rem !important;
                font-weight: 700 !important;
                margin-bottom: .3rem !important;
            }}
            .mm-nav-copy {{
                color: {MUTED} !important;
                font-size: .84rem !important;
                font-weight: 400 !important;
                line-height: 1.5 !important;
            }}
            .mm-nav-card-action {{
                margin-top: .38rem !important;
                margin-bottom: .85rem !important;
            }}
            .mm-nav-card-action div.stButton > button {{
                background: transparent !important;
                border: 1px solid {BORDER} !important;
                border-radius: 6px !important;
                color: {MUTED} !important;
                font-size: .78rem !important;
                font-weight: 600 !important;
                min-height: 30px !important;
                box-shadow: none !important;
                letter-spacing: 0 !important;
            }}
            .mm-nav-card-action div.stButton > button:hover {{
                background: {ORANGE_PAL} !important;
                border-color: {ORANGE} !important;
                color: {ORANGE} !important;
                box-shadow: none !important;
            }}

            /* ── Insight card ───────────────────────────────────────── */
            .mm-insight-card {{
                padding: .85rem .95rem .85rem 1.1rem !important;
                min-height: auto !important;
                position: relative;
            }}
            .mm-insight-card::before {{
                content: "";
                position: absolute;
                left: 0; top: 0; bottom: 0;
                width: 3px;
                background: {ORANGE};
                border-radius: 8px 0 0 8px;
            }}

            /* ── KPI / metric cards ─────────────────────────────────── */
            .mm-kpi-card,
            .mm-stat-card,
            div[data-testid="stMetric"] {{
                border-top: 2px solid {ORANGE} !important;
                padding: .85rem .95rem !important;
            }}
            .mm-kpi-card.is-red,
            .mm-stat-card.is-red {{ border-top-color: #ef4444 !important; }}
            div[data-testid="stMetric"]::before {{ display: none !important; }}
            .mm-kpi-label,
            .mm-stat-label,
            div[data-testid="stMetricLabel"] p {{
                color: {MUTED} !important;
                font-size: .67rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .07em !important;
            }}
            .mm-kpi-value,
            .mm-stat-value,
            div[data-testid="stMetricValue"] {{
                color: {INK} !important;
                font-size: 1.5rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.01em !important;
            }}
            .mm-kpi-help {{
                color: {MUTED} !important;
                font-size: .72rem !important;
                font-weight: 400 !important;
                line-height: 1.3 !important;
                margin-top: .28rem !important;
            }}

            /* ── Profile / workflow cards ───────────────────────────── */
            .mm-profile-card {{ border-left: 2px solid {ORANGE} !important; }}
            .mm-profile-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .86rem !important; }}
            .mm-profile-copy {{ color: {MUTED} !important; font-size: .78rem !important; line-height: 1.38 !important; }}
            .mm-rail-step::before {{ background: {ORANGE} !important; border-radius: 8px 0 0 8px !important; }}
            .mm-rail-label {{ color: {MUTED} !important; font-size: .62rem !important; letter-spacing: .1em !important; text-transform: uppercase !important; font-weight: 700 !important; }}
            .mm-rail-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .82rem !important; }}
            .mm-workflow-step {{ color: {ORANGE} !important; font-size: .65rem !important; font-weight: 700 !important; letter-spacing: .12em !important; text-transform: uppercase !important; }}
            .mm-workflow-title {{ color: {INK} !important; font-weight: 700 !important; }}
            .mm-workflow-copy {{ color: {MUTED} !important; font-size: .84rem !important; line-height: 1.45 !important; }}
            .mm-panel-title {{ color: {INK} !important; font-weight: 700 !important; font-size: .95rem !important; }}
            .mm-panel-copy {{ color: {MUTED} !important; font-size: .82rem !important; line-height: 1.42 !important; }}

            /* ── Filter summary ─────────────────────────────────────── */
            .mm-filter-summary {{ padding: .78rem 1rem !important; }}
            .mm-filter-count {{
                color: {INK} !important;
                font-size: .92rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-filter-card {{
                background: #f9fafb !important;
                border: 1px solid {BORDER} !important;
                border-radius: 6px !important;
            }}
            .mm-filter-label {{ color: {MUTED} !important; font-size: .56rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: .07em !important; }}
            .mm-filter-value {{ color: {INK} !important; font-size: .72rem !important; font-weight: 700 !important; }}
            .mm-chip,
            .mm-tiny {{
                background: #f3f4f6 !important;
                border: 1px solid {BORDER} !important;
                color: #374151 !important;
                border-radius: 6px !important;
                font-size: .72rem !important;
                font-weight: 700 !important;
            }}
            .mm-chip strong {{ color: {INK} !important; }}

            /* ── Empty state ────────────────────────────────────────── */
            .mm-empty-state {{ border-left: 3px solid {ORANGE} !important; }}
            .mm-empty-title {{ color: {INK} !important; font-weight: 700 !important; }}
            .mm-empty-copy {{ color: {MUTED} !important; }}

            /* ── Tables ─────────────────────────────────────────────── */
            [data-testid="stDataFrameResizable"] {{
                border-radius: 8px !important;
                overflow: hidden !important;
                border: 1px solid {BORDER} !important;
                box-shadow: 0 1px 3px rgba(15,23,42,0.05) !important;
                background: {SURFACE} !important;
            }}
            [data-testid="stDataFrame"] > div {{
                border-radius: 8px !important;
                overflow: hidden !important;
            }}
            [data-testid="stDataFrame"] iframe {{ border: 0 !important; }}
            .mm-table-note {{
                color: {MUTED} !important;
                font-size: .78rem !important;
                font-weight: 400 !important;
            }}

            /* ── Charts / images ────────────────────────────────────── */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 8px !important;
                padding: .65rem !important;
                box-shadow: 0 1px 3px rgba(15,23,42,0.05) !important;
            }}

            /* ── Tabs — segment control ─────────────────────────────── */
            div[data-testid="stTabs"] [role="tablist"] {{
                background: #f3f4f6 !important;
                border: 0 !important;
                border-radius: 8px !important;
                padding: .25rem !important;
                box-shadow: none !important;
                gap: .12rem !important;
                margin-bottom: .7rem !important;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 6px !important;
                color: {MUTED} !important;
                font-size: .82rem !important;
                font-weight: 500 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 32px !important;
                padding: .26rem .92rem !important;
                transition: background .1s ease, color .1s ease !important;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: rgba(255,255,255,0.75) !important;
                color: {INK} !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: {SURFACE} !important;
                color: {INK} !important;
                box-shadow: 0 1px 4px rgba(15,23,42,0.10) !important;
                font-weight: 700 !important;
            }}

            /* ── Primary buttons ────────────────────────────────────── */
            div.stButton > button {{
                background: {ORANGE} !important;
                border: 0 !important;
                border-radius: 7px !important;
                color: #ffffff !important;
                font-size: .82rem !important;
                font-weight: 600 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 38px !important;
                box-shadow: 0 1px 2px rgba(234,88,12,0.18) !important;
                transition: background .12s ease, box-shadow .12s ease !important;
            }}
            div.stButton > button:hover {{
                background: {ORANGE_D} !important;
                box-shadow: 0 3px 10px rgba(234,88,12,0.26) !important;
            }}
            div.stButton > button:active {{
                transform: translateY(1px) !important;
                box-shadow: none !important;
            }}

            /* Download → secondary outline */
            div[data-testid="stDownloadButton"] > button {{
                background: transparent !important;
                border: 1.5px solid #d1d5db !important;
                border-radius: 7px !important;
                color: #374151 !important;
                font-size: .82rem !important;
                font-weight: 600 !important;
                min-height: 38px !important;
                box-shadow: none !important;
                transition: border-color .12s ease, color .12s ease, background .12s ease !important;
            }}
            div[data-testid="stDownloadButton"] > button:hover {{
                background: {ORANGE_PAL} !important;
                border-color: {ORANGE} !important;
                color: {ORANGE} !important;
            }}

            /* ── Alerts ─────────────────────────────────────────────── */
            div[data-testid="stAlert"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 8px !important;
            }}
            div[data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{ color: {MUTED} !important; }}

            /* ── Tabular numbers everywhere ─────────────────────────── */
            div[data-testid="stMetricValue"],
            .mm-kpi-value,
            .mm-stat-value,
            .mm-feature-value,
            .mm-filter-count,
            .mm-kpi-deck {{
                font-variant-numeric: tabular-nums !important;
            }}

            /* ── Responsive ─────────────────────────────────────────── */
            @media (max-width: 760px) {{
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div,
                div[data-testid="stSidebar"] {{
                    width: 100% !important;
                    min-width: 100% !important;
                    max-width: 100% !important;
                }}
                .mm-title {{ font-size: 1.75rem !important; }}
                .block-container {{ padding: .65rem .85rem 2rem !important; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
