"""App-wide CSS — dark theme, green accent, complete component coverage."""
from __future__ import annotations

import streamlit as st

# Design tokens
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
BORDER     = "rgba(255,255,255,0.08)"
BORDER_2   = "rgba(255,255,255,0.13)"
SIDEBAR_BG = "#0d0f14"
AMBER      = "#f59e0b"   # used for is-red / warning highlights

# Legacy aliases kept for chart code in utils.py
BLACK    = "#0b0f14"
RED      = GREEN
RED_DARK = GREEN_D


def inject_sidebar_css() -> None:
    """No-op: sidebar CSS is part of inject_app_style."""
    pass


def inject_app_style() -> None:  # noqa: C901
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

            /* ─── Tokens ─────────────────────────────────────────── */
            :root {{
                --c-bg:      {NAVY};
                --c-s1:      {SURFACE};
                --c-s2:      {SURFACE_2};
                --c-s3:      {SURFACE_3};
                --c-sidebar: {SIDEBAR_BG};
                --c-ink:     {INK};
                --c-muted:   {MUTED};
                --c-muted2:  {MUTED_2};
                --c-border:  {BORDER};
                --c-b2:      {BORDER_2};
                --c-green:   {GREEN};
                --c-green-d: {GREEN_D};
                --c-amber:   {AMBER};
            }}

            /* ─── Base ───────────────────────────────────────────── */
            html, body, [class*="css"] {{
                font-family: Inter, -apple-system, BlinkMacSystemFont,
                             "Segoe UI", sans-serif;
                font-feature-settings: "cv02","cv03","cv04","cv11";
            }}
            .stApp {{
                background: var(--c-bg) !important;
                color: var(--c-ink) !important;
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
                padding: .85rem 1.55rem 3rem !important;
            }}
            h1,h2,h3,h4,h5,h6 {{ color: {INK} !important; }}
            p {{ color: {MUTED_2}; }}
            label {{ color: {MUTED_2} !important; }}
            span {{ color: inherit; }}

            /* ─── Sidebar shell ──────────────────────────────────── */
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
            div[data-testid="stSidebar"] * {{ color: {MUTED_2} !important; }}

            /* Logo */
            div[data-testid="stSidebar"] [data-testid="stImage"] img {{ border-radius: 4px; }}

            /* Sidebar headings */
            div[data-testid="stSidebar"] h3 {{
                color: #374151 !important;
                font-size: .58rem !important;
                font-weight: 700 !important;
                letter-spacing: .2em !important;
                text-transform: uppercase !important;
                padding: 0 .2rem !important;
                margin: 1.2rem 0 .28rem !important;
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: rgba(255,255,255,0.06) !important;
                margin: .5rem 0 !important;
            }}

            /* Nav radio → sidebar links */
            div[data-testid="stSidebar"] [role="radiogroup"] {{
                display: grid !important;
                gap: .08rem !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"]
              [data-baseweb="radio"] > div:first-child,
            div[data-testid="stSidebar"] [role="radiogroup"]
              [data-baseweb="radio"] svg {{
                display: none !important;
                width: 0 !important; height: 0 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label > div {{
                gap: 0 !important; padding-left: 0 !important; margin-left: 0 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 5px !important;
                padding: .52rem .75rem !important;
                font-size: .84rem !important;
                font-weight: 400 !important;
                color: #6b7280 !important;
                cursor: pointer;
                transition: background .1s, color .1s !important;
                min-height: auto !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
                background: rgba(255,255,255,0.04) !important;
                color: #d1d5db !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"]
              label:has(input:checked) {{
                background: rgba(34,197,94,0.10) !important;
                border-left: 2px solid {GREEN} !important;
                padding-left: calc(.75rem - 2px) !important;
                color: {GREEN} !important;
                font-weight: 600 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"]
              label:has(input:checked) * {{ color: {GREEN} !important; }}

            /* Sidebar selects / inputs */
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div {{
                background: rgba(255,255,255,0.05) !important;
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

            /* Sidebar buttons */
            div[data-testid="stSidebar"] div.stButton > button {{
                background: transparent !important;
                border: 1px solid rgba(34,197,94,0.28) !important;
                border-radius: 5px !important;
                color: #6b7280 !important;
                font-size: .77rem !important;
                font-weight: 600 !important;
                min-height: 32px !important;
                text-transform: none !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] div.stButton > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.48) !important;
                color: #86efac !important;
            }}

            /* ─── Main area inputs ───────────────────────────────── */
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER_2} !important;
                border-radius: 6px !important;
                box-shadow: none !important;
                transition: border-color .12s, box-shadow .12s !important;
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
            [data-baseweb="tag"] {{
                background: rgba(34,197,94,0.18) !important;
                border-radius: 4px !important;
            }}
            [data-baseweb="tag"] span {{ color: #86efac !important; }}
            [data-baseweb="tag"] [role="button"] {{ color: #86efac !important; }}

            /* Dropdown popover */
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER_2} !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
                border-radius: 8px !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: {MUTED_2} !important;
                -webkit-text-fill-color: {MUTED_2} !important;
                background: transparent !important;
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

            /* Radio buttons (main content) */
            div[data-testid="stRadio"] label {{ color: {MUTED_2} !important; }}
            div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {{
                border-color: {BORDER_2} !important;
            }}
            div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"]
              > div:first-child {{
                border-color: {GREEN} !important;
                background: {GREEN} !important;
            }}

            /* Checkboxes */
            div[data-testid="stCheckbox"] label {{ color: {MUTED_2} !important; }}
            div[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child {{
                border-color: {BORDER_2} !important;
                background: {SURFACE_2} !important;
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
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
            }}
            div[data-testid="stExpander"] summary {{
                color: {MUTED_2} !important;
                font-weight: 600 !important;
            }}
            div[data-testid="stExpander"] summary:hover {{
                color: {INK} !important;
            }}
            div[data-testid="stExpander"] svg {{ color: {MUTED} !important; }}

            /* ─── Hero block ─────────────────────────────────────── */
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
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 2px !important;
                background: {GREEN} !important;
                border-radius: 8px 8px 0 0 !important;
            }}
            .mm-eyebrow {{
                color: #374151 !important;
                font-size: .64rem !important;
                font-weight: 700 !important;
                letter-spacing: .2em !important;
                text-transform: uppercase !important;
            }}
            .mm-title {{
                color: {INK} !important;
                font-size: clamp(1.65rem,2.3vw,2.5rem) !important;
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

            /* ─── Section divider ────────────────────────────────── */
            .mm-section {{
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 1rem !important;
                border-bottom: 1px solid {BORDER} !important;
                padding: 0 0 .42rem !important;
                margin: 1.45rem 0 .82rem !important;
                background: none !important;
                border-radius: 0 !important;
            }}
            .mm-section-title {{
                color: {MUTED_2} !important;
                font-size: .68rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .15em !important;
                display: inline-flex;
                align-items: center;
                gap: .4rem;
            }}
            .mm-section-title::before {{
                content: "" !important;
                display: inline-block !important;
                width: .28rem !important; height: .28rem !important;
                border-radius: 999px !important;
                background: {GREEN} !important;
                flex-shrink: 0;
            }}
            .mm-section-note {{
                color: {MUTED} !important;
                font-size: .75rem !important;
                font-weight: 400 !important;
            }}

            /* ─── KPI deck (6-col grid) ──────────────────────────── */
            .mm-kpi-deck {{
                display: grid;
                grid-template-columns: repeat(6,minmax(0,1fr));
                gap: .55rem;
                margin: .8rem 0 .55rem;
            }}
            .mm-kpi-card {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-top: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .78rem .88rem !important;
                box-shadow: none !important;
                min-height: 90px;
            }}
            .mm-kpi-card.is-red {{ border-top-color: {AMBER} !important; }}
            .mm-kpi-label {{
                color: {MUTED} !important;
                font-size: .63rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .08em !important;
                margin-bottom: .2rem !important;
            }}
            .mm-kpi-value {{
                color: {INK} !important;
                font-size: 1.42rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.01em !important;
                line-height: 1.1 !important;
            }}
            .mm-kpi-help {{
                color: {MUTED} !important;
                font-size: .68rem !important;
                line-height: 1.3 !important;
                margin-top: .22rem !important;
            }}

            /* ─── Read strip (3-col dark cards) ─────────────────── */
            .mm-read-strip {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: .55rem;
                margin: .6rem 0 1rem;
            }}
            .mm-read-card {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER} !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .72rem .8rem !important;
                box-shadow: none !important;
            }}
            .mm-read-title {{
                color: {MUTED} !important;
                font-size: .62rem !important;
                font-weight: 700 !important;
                letter-spacing: .1em !important;
                text-transform: uppercase !important;
                margin-bottom: .22rem !important;
            }}
            .mm-read-value {{
                color: {INK} !important;
                font-size: .88rem !important;
                font-weight: 700 !important;
                line-height: 1.35 !important;
                overflow-wrap: anywhere;
            }}

            /* ─── Feature strip (4-col) ──────────────────────────── */
            .mm-feature-strip {{
                display: grid;
                grid-template-columns: repeat(4,minmax(0,1fr));
                gap: .55rem;
                margin: .65rem 0 .9rem;
            }}
            .mm-feature-pill {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .78rem .88rem !important;
                box-shadow: none !important;
            }}
            .mm-feature-value {{
                color: {INK} !important;
                font-size: .98rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
            }}
            .mm-feature-label {{
                color: {MUTED} !important;
                font-size: .64rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .07em !important;
                margin-top: .18rem !important;
            }}

            /* ─── Stat grid (6-col) ──────────────────────────────── */
            .mm-stat-grid {{
                display: grid;
                grid-template-columns: repeat(6,minmax(0,1fr));
                gap: .5rem;
                margin: .65rem 0 .85rem;
            }}
            .mm-stat-card {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-top: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .7rem .78rem !important;
            }}
            .mm-stat-card.is-red {{ border-top-color: {AMBER} !important; }}
            .mm-stat-label {{
                color: {MUTED} !important;
                font-size: .64rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: .07em !important;
                margin-bottom: .16rem !important;
            }}
            .mm-stat-value {{
                color: {INK} !important;
                font-size: 1.2rem !important;
                font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                line-height: 1.1 !important;
            }}

            /* ─── Workflow rail (4-col) ──────────────────────────── */
            .mm-workflow-rail {{
                display: grid;
                grid-template-columns: repeat(4,minmax(0,1fr));
                gap: .5rem;
                margin: .62rem 0 .8rem;
            }}
            .mm-rail-step {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .62rem .7rem !important;
                position: relative;
            }}
            .mm-rail-step::before {{
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 2px;
                background: {GREEN};
                border-radius: 7px 0 0 7px;
            }}
            .mm-rail-label {{
                color: {MUTED} !important;
                font-size: .6rem !important; font-weight: 700 !important;
                letter-spacing: .1em !important; text-transform: uppercase !important;
                margin-bottom: .14rem !important;
            }}
            .mm-rail-title {{
                color: {INK} !important;
                font-weight: 700 !important; font-size: .82rem !important;
            }}

            /* ─── Workflow grid (3-col) ──────────────────────────── */
            .mm-workflow-grid {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: .62rem;
                margin: .72rem 0 1rem;
            }}
            .mm-workflow-card {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .88rem .9rem !important;
            }}
            .mm-workflow-step {{
                color: {GREEN} !important;
                font-size: .62rem !important; font-weight: 700 !important;
                letter-spacing: .12em !important; text-transform: uppercase !important;
                margin-bottom: .28rem !important;
            }}
            .mm-workflow-title {{
                color: {INK} !important;
                font-weight: 700 !important;
                margin-bottom: .22rem !important;
            }}
            .mm-workflow-copy {{
                color: {MUTED} !important;
                font-size: .83rem !important; line-height: 1.45 !important;
            }}

            /* ─── Profile strip (3-col) ──────────────────────────── */
            .mm-profile-strip {{
                display: grid;
                grid-template-columns: repeat(3,minmax(0,1fr));
                gap: .52rem;
                margin: .62rem 0;
            }}
            .mm-profile-card {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .7rem .78rem !important;
            }}
            .mm-profile-title {{
                color: {INK} !important;
                font-weight: 700 !important; font-size: .85rem !important;
                margin-bottom: .16rem !important;
            }}
            .mm-profile-copy {{
                color: {MUTED} !important;
                font-size: .77rem !important; line-height: 1.38 !important;
                overflow-wrap: anywhere;
            }}

            /* ─── Scout shell (2-col split) ──────────────────────── */
            .mm-scout-shell {{
                display: grid;
                grid-template-columns: minmax(0,1.28fr) minmax(300px,.72fr);
                gap: .88rem;
                margin: .8rem 0 1rem;
            }}

            /* ─── Command center (2-col) ─────────────────────────── */
            .mm-command-center {{
                display: grid;
                grid-template-columns: minmax(0,1.05fr) minmax(310px,.95fr);
                gap: .82rem;
                margin: .8rem 0 1.1rem;
            }}
            .mm-panel {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .92rem !important;
            }}
            .mm-panel-title {{
                color: {INK} !important;
                font-weight: 700 !important; font-size: .92rem !important;
                margin-bottom: .18rem !important;
            }}
            .mm-panel-copy {{
                color: {MUTED} !important;
                font-size: .81rem !important; line-height: 1.42 !important;
                margin-bottom: .72rem !important;
            }}
            .mm-command-panel {{
                background: {SURFACE_2} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: 1rem !important;
            }}
            .mm-command-title {{
                color: {INK} !important;
                font-size: .92rem !important; font-weight: 700 !important;
                letter-spacing: .06em !important; text-transform: uppercase !important;
                margin-bottom: .7rem !important;
            }}
            .mm-command-row {{
                display: grid;
                grid-template-columns: 7rem minmax(0,1fr);
                gap: .7rem;
                padding: .6rem 0;
                border-top: 1px solid {BORDER};
            }}
            .mm-command-label {{
                color: {MUTED} !important;
                font-size: .65rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .08em !important;
            }}
            .mm-command-value {{
                color: {MUTED_2} !important;
                font-size: .86rem !important; line-height: 1.38 !important;
                overflow-wrap: anywhere;
            }}

            /* ─── Insight card ───────────────────────────────────── */
            .mm-insight-card {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .82rem .95rem .82rem 1.1rem !important;
                min-height: auto !important;
                position: relative;
                box-shadow: none !important;
                color: {MUTED_2};
                line-height: 1.45;
                font-size: .88rem;
            }}
            .mm-insight-card::before {{
                content: "";
                position: absolute;
                left: 0; top: 0; bottom: 0;
                width: 2px;
                background: {GREEN};
                border-radius: 7px 0 0 7px;
            }}
            .mm-insight-card strong {{ color: {INK} !important; }}

            /* ─── Home module nav cards ──────────────────────────── */
            .mm-nav-card {{
                position: relative;
                overflow: hidden;
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 8px !important;
                padding: 1rem 1.05rem .78rem !important;
                min-height: 138px !important;
                box-shadow: none !important;
                transition: border-color .15s, background .15s !important;
            }}
            .mm-nav-card:hover {{
                background: {SURFACE_2} !important;
                border-color: rgba(34,197,94,0.28) !important;
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
                font-size: .62rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .14em !important;
                margin-bottom: .34rem !important;
            }}
            .mm-nav-title {{
                color: {INK} !important;
                font-size: .96rem !important; font-weight: 700 !important;
                margin-bottom: .26rem !important;
            }}
            .mm-nav-copy {{
                color: {MUTED} !important;
                font-size: .82rem !important; font-weight: 400 !important;
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
                font-size: .76rem !important; font-weight: 600 !important;
                min-height: 28px !important; box-shadow: none !important;
            }}
            .mm-nav-card-action div.stButton > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.38) !important;
                color: {GREEN} !important;
            }}

            /* ─── Filter summary ─────────────────────────────────── */
            .mm-filter-summary {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                display: flex; align-items: center;
                justify-content: space-between; gap: .8rem;
                padding: .7rem .95rem !important;
                margin: .75rem 0 1rem;
                flex-wrap: wrap;
            }}
            .mm-filter-count {{
                color: {INK} !important;
                font-size: .88rem !important; font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                white-space: nowrap;
            }}
            .mm-filter-chips {{
                display: flex; flex-wrap: wrap;
                justify-content: flex-end; gap: .35rem;
            }}
            .mm-chip, .mm-tiny {{
                display: inline-flex; align-items: center; gap: .22rem;
                background: rgba(255,255,255,0.06) !important;
                border: 1px solid {BORDER_2} !important;
                color: {MUTED_2} !important;
                border-radius: 5px !important;
                padding: .24rem .52rem;
                font-size: .7rem !important; font-weight: 600 !important;
                line-height: 1.15; overflow-wrap: anywhere;
            }}
            .mm-chip strong {{ color: {INK} !important; }}
            .mm-filter-card {{
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid {BORDER} !important;
                border-radius: 5px !important;
                padding: .42rem .5rem;
                margin: .24rem 0;
            }}
            .mm-filter-label {{
                color: {MUTED} !important;
                font-size: .54rem !important; font-weight: 700 !important;
                letter-spacing: .07em !important; text-transform: uppercase !important;
                margin-bottom: .14rem !important;
            }}
            .mm-filter-value {{
                color: {MUTED_2} !important;
                font-size: .72rem !important; font-weight: 600 !important;
                line-height: 1.25; overflow-wrap: anywhere;
            }}

            /* ─── Empty state ────────────────────────────────────── */
            .mm-empty-state {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-left: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: 1rem 1.05rem !important;
                margin: .75rem 0 1rem;
            }}
            .mm-empty-title {{
                color: {INK} !important; font-weight: 700 !important;
                margin-bottom: .2rem !important;
            }}
            .mm-empty-copy {{
                color: {MUTED} !important; font-size: .84rem !important;
                line-height: 1.45 !important;
            }}

            /* ─── Native st.metric ───────────────────────────────── */
            div[data-testid="stMetric"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-top: 2px solid {GREEN} !important;
                border-radius: 7px !important;
                padding: .82rem .9rem !important;
                box-shadow: none !important;
            }}
            div[data-testid="stMetric"]::before {{ display: none !important; }}
            div[data-testid="stMetricLabel"] p {{
                color: {MUTED} !important;
                font-size: .65rem !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: .08em !important;
            }}
            div[data-testid="stMetricValue"] {{
                color: {INK} !important;
                font-size: 1.45rem !important; font-weight: 800 !important;
                font-variant-numeric: tabular-nums !important;
                letter-spacing: -.01em !important;
            }}
            div[data-testid="stMetricDelta"] {{ display: none; }}

            /* ─── Tables ─────────────────────────────────────────── */
            [data-testid="stDataFrameResizable"] {{
                border-radius: 7px !important;
                overflow: hidden !important;
                border: 1px solid {BORDER} !important;
                box-shadow: none !important;
                background: {SURFACE} !important;
            }}
            [data-testid="stDataFrame"] > div {{
                border-radius: 7px !important; overflow: hidden !important;
            }}
            [data-testid="stDataFrame"] iframe {{ border: 0 !important; }}
            .mm-table-note {{
                color: {MUTED} !important; font-size: .76rem !important;
            }}

            /* ─── Charts / images ────────────────────────────────── */
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
                padding: .6rem !important;
                box-shadow: none !important;
            }}

            /* ─── Tabs ───────────────────────────────────────────── */
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
                font-size: .8rem !important; font-weight: 500 !important;
                letter-spacing: 0 !important; text-transform: none !important;
                min-height: 30px !important; padding: .24rem .9rem !important;
                transition: background .1s, color .1s !important;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: rgba(255,255,255,0.05) !important;
                color: {INK} !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: {GREEN} !important;
                color: {GREEN_PAL} !important;
                font-weight: 700 !important;
                box-shadow: none !important;
            }}

            /* ─── Primary buttons ────────────────────────────────── */
            div.stButton > button {{
                background: {GREEN} !important;
                border: 0 !important;
                border-radius: 6px !important;
                color: {GREEN_PAL} !important;
                font-size: .81rem !important; font-weight: 700 !important;
                letter-spacing: 0 !important; text-transform: none !important;
                min-height: 36px !important;
                box-shadow: none !important;
                transition: background .12s !important;
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
                font-size: .81rem !important; font-weight: 600 !important;
                min-height: 36px !important; box-shadow: none !important;
            }}
            div[data-testid="stDownloadButton"] > button:hover {{
                background: rgba(34,197,94,0.08) !important;
                border-color: rgba(34,197,94,0.38) !important;
                color: {GREEN} !important;
            }}

            /* ─── Alerts / info ──────────────────────────────────── */
            div[data-testid="stAlert"] {{
                background: {SURFACE} !important;
                border: 1px solid {BORDER} !important;
                border-radius: 7px !important;
            }}
            div[data-testid="stAlert"] * {{ color: {MUTED_2} !important; }}
            div[data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{ color: {MUTED} !important; }}

            /* ─── Tabular numbers everywhere ─────────────────────── */
            div[data-testid="stMetricValue"],
            .mm-kpi-value, .mm-stat-value, .mm-feature-value,
            .mm-filter-count {{ font-variant-numeric: tabular-nums !important; }}

            /* ─── Responsive grids ───────────────────────────────── */
            @media (max-width: 1100px) {{
                .mm-kpi-deck, .mm-stat-grid {{
                    grid-template-columns: repeat(3,minmax(0,1fr));
                }}
                .mm-scout-shell, .mm-command-center {{
                    grid-template-columns: 1fr;
                }}
            }}
            @media (max-width: 760px) {{
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div,
                div[data-testid="stSidebar"] {{
                    width: 100% !important;
                    min-width: 100% !important;
                    max-width: 100% !important;
                }}
                .mm-title {{ font-size: 1.65rem !important; }}
                .block-container {{ padding: .65rem .85rem 2rem !important; }}
                .mm-kpi-deck, .mm-stat-grid {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
                .mm-read-strip, .mm-profile-strip, .mm-workflow-grid {{
                    grid-template-columns: 1fr;
                }}
                .mm-feature-strip, .mm-workflow-rail {{
                    grid-template-columns: repeat(2,minmax(0,1fr));
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
