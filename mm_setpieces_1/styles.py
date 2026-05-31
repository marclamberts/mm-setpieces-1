"""App-wide CSS injection. Extracted from utils.py to keep it readable."""
from __future__ import annotations

import streamlit as st

# Colour tokens (used as f-string vars inside the CSS)
BLACK = "#0b0f14"
RED = "#c1121f"
RED_DARK = "#780000"
INK = "#111827"
MUTED = "#475569"
BORDER = "rgba(17,24,39,0.12)"


def inject_sidebar_css() -> None:
    """Dark sidebar CSS injected on every non-landing page."""
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
                background-color: #07111d !important;
                color: #e5edf6 !important;
                color-scheme: dark !important;
            }
            section[data-testid="stSidebar"] * { color: #e5edf6 !important; }
            section[data-testid="stSidebar"] [data-baseweb="select"] > div,
            section[data-testid="stSidebar"] [data-baseweb="select"] span,
            section[data-testid="stSidebar"] [data-baseweb="select"] div {
                background-color: #0d1b2a !important;
                color: #f8fafc !important;
                border-color: rgba(148, 163, 184, 0.35) !important;
            }
            section[data-testid="stSidebar"] [data-baseweb="tag"] {
                background-color: #14324f !important; color: #f8fafc !important;
            }
            section[data-testid="stSidebar"] button {
                background-color: #c1121f !important; color: #ffffff !important;
                border: 1.5px solid #c1121f !important;
            }
            section[data-testid="stSidebar"] button:hover {
                background-color: #991b1b !important; color: #ffffff !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_app_style() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
            :root {{
                --mm-black: {BLACK};
                --mm-red: {RED};
                --mm-red-dark: {RED_DARK};
                --mm-ink: {INK};
                --mm-muted: {MUTED};
                --mm-border: {BORDER};
                --mm-surface: #ffffff;
                --mm-surface-soft: #f8fafc;
                --mm-page: #f6f7f9;
                --mm-line: #d9dee7;
                --mm-blue: #1d4ed8;
                --mm-green: #15803d;
                --mm-amber: #b45309;
            }}
            .stApp {{
                background:
                    linear-gradient(180deg, #eef1f5 0%, #f7f8fa 260px, #f6f7f9 100%);
                color: var(--mm-black);
            }}
            footer,
            #MainMenu {{
                visibility: hidden;
                height: 0;
            }}
            header[data-testid="stHeader"] {{
                visibility: visible !important;
                background: transparent !important;
                height: 2.6rem !important;
            }}
            header[data-testid="stHeader"]::before {{
                background: transparent !important;
            }}
            html, body, [class*="css"] {{
                font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            .block-container {{
                padding-top: .65rem;
                padding-bottom: 3rem;
                max-width: 1440px;
            }}
            h1, h2, h3, h4, h5, h6, p, label, span {{
                color: var(--mm-black);
            }}
            h1, h2, h3 {{
                letter-spacing: 0;
            }}
            section[data-testid="stSidebar"] {{
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                transform: none !important;
                min-width: 15rem !important;
                width: 15rem !important;
                max-width: 15rem !important;
            }}
            section[data-testid="stSidebar"] > div {{
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                width: 15rem !important;
            }}
            div[data-testid="stSidebar"] {{
                background: #ffffff;
                border-right: 1px solid #dbe3ee;
                min-width: 15rem !important;
                width: 15rem !important;
            }}
            div[data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
                display: none !important;
            }}
            div[data-testid="stSidebar"] *,
            div[data-testid="stSidebar"] span,
            div[data-testid="stSidebar"] div,
            div[data-testid="stSidebar"] button,
            div[data-testid="stSidebar"] a {{
                color: #111827 !important;
            }}
            div[data-testid="stSidebar"] h2,
            div[data-testid="stSidebar"] h3 {{
                color: #0b0f14 !important;
                font-weight: 800;
            }}
            div[data-testid="stSidebar"] label,
            div[data-testid="stSidebar"] p {{
                color: #111827 !important;
                font-weight: 650;
            }}
            div[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
            div[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
            div[data-testid="stSidebar"] [data-testid="stExpander"] summary,
            div[data-testid="stSidebar"] [data-testid="stExpander"] summary * {{
                color: #111827 !important;
            }}
            div[data-testid="stSidebar"] .st-emotion-cache-ue6h4q,
            div[data-testid="stSidebar"] .st-emotion-cache-16idsys p {{
                font-size: .78rem;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div {{
                background: #f8fafc !important;
                border-color: #cfd6e1 !important;
                border-radius: 6px;
                min-height: 38px;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] input,
            div[data-testid="stSidebar"] [data-baseweb="select"] span,
            div[data-testid="stSidebar"] [data-baseweb="tag"] span,
            div[data-testid="stSidebar"] [data-baseweb="input"] input {{
                color: #111827 !important;
                -webkit-text-fill-color: #111827 !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] {{
                background: #e2e8f0 !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label,
            div[data-testid="stSidebar"] [role="radiogroup"] span,
            div[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
            div[data-testid="stSidebar"] [data-testid="stCheckbox"] span {{
                color: #111827 !important;
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: #dbe3ee;
            }}
            .mm-filter-card {{
                background: #f8fafc;
                border: 1px solid #dbe3ee;
                border-radius: 6px;
                padding: .46rem .5rem;
                margin: .28rem 0;
            }}
            .mm-filter-label {{
                color: #64748b;
                font-size: .56rem;
                font-weight: 850;
                letter-spacing: .07em;
                text-transform: uppercase;
                margin-bottom: .18rem;
            }}
            .mm-filter-value {{
                color: #111827;
                font-size: .72rem;
                font-weight: 850;
                line-height: 1.25;
                overflow-wrap: anywhere;
            }}
            div[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
                background: #f8fafc;
                border: 1px solid #dbe3ee;
                border-radius: 6px;
                padding: .55rem .7rem;
                margin: .18rem 0;
            }}
            div[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
                background: #eef2f7;
                border-color: #cbd5e1;
            }}
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: #ffffff !important;
                border: 1px solid #d9dee7 !important;
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18) !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: #0b0f14 !important;
                -webkit-text-fill-color: #0b0f14 !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"],
            div[data-baseweb="popover"] [role="option"]:hover {{
                background: #eef1f5 !important;
            }}
            .mm-hero {{
                background:
                    linear-gradient(135deg, rgba(11,17,24,0.98) 0%, rgba(17,24,39,0.98) 58%, rgba(56,12,18,0.98) 100%);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 6px;
                padding: 1.5rem 1.6rem;
                box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
                margin-bottom: 1rem;
                position: relative;
                overflow: hidden;
            }}
            .mm-hero::before {{
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 4px;
                background: linear-gradient(90deg, var(--mm-red) 0%, #ffffff 48%, var(--mm-blue) 100%);
            }}
            .mm-eyebrow {{
                color: rgba(255,255,255,0.72);
                font-size: .73rem;
                font-weight: 800;
                letter-spacing: .1em;
                text-transform: uppercase;
            }}
            .mm-title {{
                color: #ffffff;
                font-size: clamp(1.8rem, 2.8vw, 2.65rem);
                line-height: 1.02;
                font-weight: 900;
                margin: .24rem 0 .55rem 0;
            }}
            .mm-copy {{
                color: rgba(255,255,255,0.74);
                font-size: .98rem;
                line-height: 1.58;
                max-width: 980px;
                font-weight: 500;
            }}
            .mm-feature-strip {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: .55rem;
                margin: .15rem 0 1.05rem 0;
            }}
            .mm-feature-pill {{
                background: var(--mm-surface);
                border: 1px solid var(--mm-line);
                border-top: 3px solid #111827;
                border-radius: 6px;
                padding: .74rem .85rem;
                box-shadow: none;
            }}
            .mm-feature-value {{
                color: var(--mm-black);
                font-size: .98rem;
                font-weight: 850;
                line-height: 1.2;
            }}
            .mm-feature-label {{
                color: var(--mm-muted);
                font-size: .72rem;
                font-weight: 700;
                margin-top: .2rem;
                text-transform: uppercase;
                letter-spacing: .06em;
            }}
            .mm-section {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                border-bottom: 1px solid #cfd6e1;
                padding: 1.05rem 0 .55rem 0;
                margin: .55rem 0 .75rem 0;
            }}
            .mm-section-title {{
                color: var(--mm-black);
                font-size: 1rem;
                font-weight: 900;
                margin: 0;
                letter-spacing: 0;
            }}
            .mm-section-note {{
                color: var(--mm-muted);
                font-size: .82rem;
                font-weight: 600;
            }}
            .mm-nav-card {{
                background: var(--mm-surface);
                border: 1px solid var(--mm-line);
                border-radius: 6px;
                padding: 1.05rem;
                min-height: 170px;
                box-shadow: none;
                transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
                position: relative;
                overflow: hidden;
            }}
            .mm-nav-card::before {{
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 3px;
                background: #111827;
            }}
            .mm-nav-card:hover {{
                transform: translateY(-2px);
                border-color: rgba(17,24,39,0.28);
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.09);
            }}
            .mm-nav-title {{
                color: var(--mm-black);
                font-size: 1.08rem;
                font-weight: 850;
                margin-bottom: .45rem;
            }}
            .mm-card-kicker {{
                color: var(--mm-red-dark);
                font-size: .72rem;
                font-weight: 800;
                letter-spacing: .07em;
                text-transform: uppercase;
                margin-bottom: .45rem;
            }}
            .mm-nav-copy {{
                color: var(--mm-muted);
                line-height: 1.48;
                margin-bottom: .95rem;
                font-size: .9rem;
                font-weight: 500;
            }}
            .mm-tiny {{
                display: inline-flex;
                align-items: center;
                gap: .35rem;
                color: var(--mm-red-dark);
                background: rgba(193,18,31,0.08);
                border: 1px solid rgba(193,18,31,0.14);
                border-radius: 999px;
                padding: .26rem .55rem;
                font-size: .72rem;
                font-weight: 750;
                max-width: 100%;
                overflow-wrap: anywhere;
            }}
            .mm-insight-card {{
                background: var(--mm-surface);
                border: 1px solid var(--mm-line);
                border-radius: 6px;
                padding: .88rem 1rem .88rem 1.1rem;
                margin-bottom: .7rem;
                min-height: 82px;
                color: var(--mm-ink);
                line-height: 1.42;
                font-weight: 600;
                box-shadow: none;
                position: relative;
            }}
            .mm-insight-card::before {{
                content: "";
                position: absolute;
                left: 0;
                top: .85rem;
                bottom: .85rem;
                width: 3px;
                border-radius: 999px;
                background: var(--mm-red);
            }}
            div.stButton > button {{
                width: 100%;
                border-radius: 6px;
                border: 1px solid var(--mm-red);
                background: var(--mm-red);
                color: #ffffff !important;
                font-weight: 800;
                padding: .58rem .9rem;
                transition: none;
                box-shadow: none;
            }}
            div.stButton > button:hover {{
                border-color: var(--mm-red);
                background: var(--mm-red-dark);
                color: #ffffff !important;
                transform: none;
            }}
            .mm-landing-shell {{
                height: auto;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: .9rem;
                padding: 0;
                overflow: hidden;
                background: #ffffff;
            }}
            .mm-landing-shell div[data-testid="stImage"] {{
                background: transparent;
                border: 0;
                border-radius: 0;
                padding: 0;
                box-shadow: none;
                width: min(340px, 66vw);
            }}
            .mm-landing-shell div[data-testid="stImage"] img {{
                display: block;
                width: 100%;
                height: auto;
            }}
            .mm-landing-action {{
                width: min(260px, 68vw);
            }}
            .mm-landing-action div.stButton > button {{
                min-height: 2.9rem;
                border-radius: 6px;
                font-size: .95rem;
                letter-spacing: 0;
                box-shadow: 0 16px 34px rgba(193, 18, 31, 0.2);
            }}
            .mm-landing-wordmark {{
                font-size: clamp(3rem, 11vw, 8rem);
                line-height: .9;
                font-weight: 900;
                letter-spacing: 0;
            }}
            .mm-landing-wordmark span {{
                color: #20232b;
            }}
            .mm-landing-wordmark strong {{
                color: var(--mm-red);
            }}
            div[data-testid="stDownloadButton"] > button {{
                border-radius: 6px;
                background: var(--mm-red);
                border-color: var(--mm-red);
                color: #ffffff !important;
                font-weight: 800;
            }}
            div[data-testid="stMetric"] {{
                background: var(--mm-surface);
                border: 1px solid var(--mm-line);
                border-left: 3px solid #111827;
                border-radius: 6px;
                padding: .74rem .86rem;
                box-shadow: none;
            }}
            div[data-testid="stMetricLabel"] p {{
                color: var(--mm-muted);
                font-weight: 800;
                font-size: .72rem;
                text-transform: uppercase;
                letter-spacing: .04em;
            }}
            div[data-testid="stMetricValue"] {{
                color: var(--mm-black);
                font-weight: 900;
                font-size: 1.42rem;
            }}
            [data-testid="stDataFrameResizable"] {{
                border: 1px solid var(--mm-line);
                border-radius: 6px;
                overflow: hidden;
                box-shadow: none;
            }}
            div[data-testid="stTabs"] [role="tablist"] {{
                background: #ffffff;
                border: 1px solid rgba(193,18,31,0.28);
                border-radius: 8px;
                padding: .25rem;
                gap: .2rem;
                margin-bottom: .35rem;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                border-radius: 6px;
                font-weight: 750;
                min-height: 36px;
                padding: .35rem .85rem;
                background: var(--mm-red) !important;
                border: 1px solid var(--mm-red) !important;
                color: #ffffff !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: #0f172a !important;
                border-color: #0f172a !important;
                color: #ffffff !important;
                box-shadow: 0 0 0 2px rgba(255,255,255,0.38) inset;
            }}
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: var(--mm-surface);
                border: 1px solid var(--mm-line);
                border-radius: 6px;
                padding: .65rem;
                box-shadow: none;
            }}
            .mm-table-note {{
                color: var(--mm-muted);
                font-size: .8rem;
                font-weight: 600;
                margin: -.25rem 0 .55rem 0;
            }}
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                border-radius: 6px;
            }}
            div[data-testid="stTextInput"] input,
            div[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
            div[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
                min-height: 38px;
            }}
            .stSlider [data-testid="stTickBar"] {{
                opacity: .45;
            }}
            div[data-testid="stAlert"] {{
                border-radius: 6px;
                border: 1px solid var(--mm-line);
            }}
            .stCaptionContainer, .stCaptionContainer p {{
                color: var(--mm-muted);
                font-weight: 550;
            }}
            @media (max-width: 900px) {{
                .mm-feature-strip {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
                .mm-section {{
                    align-items: flex-start;
                    flex-direction: column;
                    gap: .25rem;
                }}
            }}
            @media (max-width: 560px) {{
                .mm-feature-strip {{
                    grid-template-columns: 1fr;
                }}
                .mm-hero {{
                    padding: 1.15rem;
                }}
            }}
            /* Scouting product layer */
            .stApp {{
                background:
                    radial-gradient(circle at 15% 0%, rgba(193,18,31,0.12), transparent 28rem),
                    linear-gradient(180deg, #091019 0%, #0d1722 11.5rem, #edf1f5 11.55rem, #f5f7fa 100%) !important;
            }}
            .block-container {{
                max-width: 1500px;
                padding-top: 1.05rem;
            }}
            .mm-hero {{
                background:
                    linear-gradient(135deg, rgba(5,10,16,0.98) 0%, rgba(11,17,24,0.96) 48%, rgba(83,18,27,0.92) 100%),
                    repeating-linear-gradient(90deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 42px);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
                padding: 1.45rem 1.55rem 1.35rem;
                box-shadow: 0 26px 70px rgba(2,6,23,0.24);
            }}
            .mm-hero::before {{
                height: 5px;
                background: linear-gradient(90deg, #c1121f 0%, #f8fafc 42%, #0ea5e9 72%, #16a34a 100%);
            }}
            .mm-eyebrow {{
                color: rgba(255,255,255,0.66) !important;
                font-size: .68rem;
                letter-spacing: .16em;
            }}
            .mm-title {{
                color: #ffffff !important;
                font-size: clamp(2rem, 3.2vw, 3.25rem);
                line-height: .98;
            }}
            .mm-copy {{
                color: rgba(226,232,240,0.82) !important;
                max-width: 1040px;
            }}
            .mm-feature-strip {{
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: .75rem;
                margin: .8rem 0 1.1rem 0;
            }}
            .mm-feature-pill,
            .mm-nav-card,
            .mm-insight-card,
            div[data-testid="stMetric"],
            [data-testid="stDataFrameResizable"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                border-radius: 10px;
                border: 1px solid rgba(15,23,42,0.12);
                box-shadow: 0 14px 36px rgba(15,23,42,0.07);
            }}
            .mm-feature-pill {{
                background: #ffffff;
                border-top: 0;
                border-left: 4px solid #0f172a;
                padding: .86rem .95rem;
            }}
            .mm-feature-value {{
                font-size: 1.02rem;
            }}
            .mm-feature-label,
            .mm-card-kicker,
            .mm-table-note,
            div[data-testid="stMetricLabel"] p {{
                letter-spacing: .08em;
            }}
            .mm-section {{
                border-bottom: 0;
                padding: .2rem 0 .4rem;
                margin: 1.15rem 0 .65rem;
            }}
            .mm-section-title {{
                display: inline-flex;
                align-items: center;
                gap: .55rem;
                color: #0b0f14;
                font-size: .92rem;
                text-transform: uppercase;
                letter-spacing: .1em;
            }}
            .mm-section-title::before {{
                content: "";
                width: .55rem;
                height: .55rem;
                border-radius: 999px;
                background: #c1121f;
                box-shadow: 0 0 0 4px rgba(193,18,31,0.12);
            }}
            .mm-section-note {{
                color: #64748b;
                font-size: .78rem;
                font-weight: 750;
            }}
            .mm-nav-card {{
                background:
                    linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
                min-height: 210px;
                padding: 1rem 1.05rem 1.1rem;
            }}
            .mm-nav-card::before {{
                inset: 0 0 auto 0;
                height: 4px;
                width: auto;
                background: linear-gradient(90deg, #0f172a, #c1121f);
            }}
            .mm-nav-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(193,18,31,0.32);
                box-shadow: 0 22px 46px rgba(15,23,42,0.13);
            }}
            .mm-nav-title {{
                font-size: 1.22rem;
                font-weight: 900;
            }}
            .mm-card-kicker {{
                color: #991b1b;
                font-size: .66rem;
            }}
            .mm-nav-copy {{
                color: #475569;
                font-size: .88rem;
            }}
            .mm-tiny {{
                border-radius: 6px;
                background: #f1f5f9;
                color: #334155;
                border-color: #dbe3ee;
            }}
            .mm-insight-card {{
                background: #ffffff;
                min-height: auto;
                border-left: 0;
                padding: .82rem .92rem .82rem 1rem;
            }}
            .mm-insight-card::before {{
                top: 0;
                bottom: 0;
                border-radius: 10px 0 0 10px;
                background: linear-gradient(180deg, #c1121f, #0f172a);
            }}
            div[data-testid="stMetric"] {{
                background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
                border-left: 0;
                padding: .82rem .92rem;
                position: relative;
                overflow: hidden;
            }}
            div[data-testid="stMetric"]::before {{
                content: "";
                position: absolute;
                inset: 0 0 auto 0;
                height: 3px;
                background: linear-gradient(90deg, #0f172a, #c1121f);
            }}
            div[data-testid="stMetricValue"] {{
                font-size: 1.58rem;
            }}
            div[data-testid="stTabs"] [role="tablist"] {{
                background: #ffffff;
                border: 1px solid rgba(193,18,31,0.28);
                border-radius: 10px;
                padding: .32rem;
                box-shadow: 0 14px 34px rgba(15,23,42,0.15);
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                background: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                color: #0f172a !important;
                border-radius: 8px;
                font-size: .86rem;
                text-transform: uppercase;
                letter-spacing: .06em;
                transition: none;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: #c1121f !important;
                border-color: #c1121f !important;
                color: #ffffff !important;
                box-shadow: none;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover,
            div[data-testid="stTabs"] button[role="tab"]:focus,
            div[data-testid="stTabs"] button[role="tab"]:active {{
                background: #f8fafc !important;
                border-color: #94a3b8 !important;
                color: #0f172a !important;
            }}
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: #ffffff;
                padding: .72rem;
            }}
            [data-testid="stDataFrameResizable"] {{
                background: #ffffff;
            }}
            div.stButton > button,
            div[data-testid="stDownloadButton"] > button {{
                min-height: 40px;
                border-radius: 8px;
                background: #c1121f;
                border-color: #c1121f;
                color: #ffffff !important;
                text-transform: uppercase;
                letter-spacing: .04em;
                font-size: .78rem;
                transition: none;
            }}
            div.stButton > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {{
                background: #991b1b;
                border-color: #991b1b;
                color: #ffffff !important;
                transform: none;
                box-shadow: none;
            }}
            div.stButton > button:focus,
            div.stButton > button:active,
            div[data-testid="stDownloadButton"] > button:focus,
            div[data-testid="stDownloadButton"] > button:active {{
                background: #c1121f !important;
                border-color: #c1121f !important;
                color: #ffffff !important;
                box-shadow: 0 0 0 3px rgba(193,18,31,0.18) !important;
            }}
            .mm-filter-summary {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: .85rem;
                background: #ffffff;
                border: 1px solid rgba(15,23,42,0.12);
                border-radius: 10px;
                padding: .8rem .9rem;
                margin: .8rem 0 1rem;
                box-shadow: 0 12px 30px rgba(15,23,42,0.06);
            }}
            .mm-filter-count {{
                color: #0f172a;
                font-size: .96rem;
                font-weight: 900;
                white-space: nowrap;
            }}
            .mm-filter-chips {{
                display: flex;
                flex-wrap: wrap;
                justify-content: flex-end;
                gap: .38rem;
            }}
            .mm-chip {{
                display: inline-flex;
                align-items: center;
                gap: .25rem;
                max-width: 21rem;
                color: #334155;
                background: #f1f5f9;
                border: 1px solid #dbe3ee;
                border-radius: 999px;
                padding: .28rem .55rem;
                font-size: .72rem;
                font-weight: 800;
                line-height: 1.15;
                overflow-wrap: anywhere;
            }}
            .mm-chip strong {{
                color: #0f172a;
            }}
            .mm-empty-state {{
                background: #ffffff;
                border: 1px solid rgba(193,18,31,0.18);
                border-left: 4px solid #c1121f;
                border-radius: 10px;
                padding: 1rem;
                margin: .8rem 0 1rem;
                color: #0f172a;
                box-shadow: 0 12px 30px rgba(15,23,42,0.06);
            }}
            .mm-empty-title {{
                font-weight: 900;
                margin-bottom: .25rem;
            }}
            .mm-empty-copy {{
                color: #475569;
                font-weight: 600;
                line-height: 1.45;
            }}
            .mm-command-center {{
                display: grid;
                grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr);
                gap: .85rem;
                margin: .8rem 0 1.1rem;
            }}
            .mm-panel {{
                background: #ffffff;
                border: 1px solid #e1e7ef;
                border-radius: 8px;
                padding: .95rem;
                box-shadow: 0 10px 28px rgba(15,23,42,0.055);
            }}
            .mm-panel-title {{
                color: #0b0f14;
                font-weight: 900;
                font-size: .95rem;
                margin-bottom: .2rem;
            }}
            .mm-panel-copy {{
                color: #64748b;
                font-weight: 600;
                font-size: .82rem;
                line-height: 1.42;
                margin-bottom: .75rem;
            }}
            .mm-stat-grid {{
                display: grid;
                grid-template-columns: repeat(6, minmax(0, 1fr));
                gap: .55rem;
                margin: .65rem 0 .85rem;
            }}
            .mm-kpi-deck {{
                display: grid;
                grid-template-columns: repeat(6, minmax(0, 1fr));
                gap: .58rem;
                margin: .8rem 0 .55rem;
            }}
            .mm-kpi-card {{
                background: #ffffff;
                border: 1px solid #e1e7ef;
                border-top: 3px solid #0b0f14;
                border-radius: 8px;
                padding: .78rem .82rem;
                box-shadow: 0 10px 28px rgba(15,23,42,0.055);
                min-height: 92px;
            }}
            .mm-kpi-card.is-red {{
                border-top-color: #c1121f;
            }}
            .mm-kpi-label {{
                color: #64748b;
                font-size: .66rem;
                font-weight: 900;
                letter-spacing: .08em;
                text-transform: uppercase;
                margin-bottom: .22rem;
            }}
            .mm-kpi-value {{
                color: #0b0f14;
                font-size: 1.35rem;
                font-weight: 950;
                line-height: 1.08;
            }}
            .mm-kpi-help {{
                color: #64748b;
                font-size: .72rem;
                font-weight: 650;
                line-height: 1.25;
                margin-top: .3rem;
            }}
            .mm-read-strip {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: .58rem;
                margin: .6rem 0 1rem;
            }}
            .mm-read-card {{
                background: #10151c;
                border: 1px solid rgba(255,255,255,0.10);
                border-left: 3px solid #c1121f;
                border-radius: 8px;
                padding: .78rem .85rem;
                box-shadow: 0 12px 30px rgba(15,23,42,0.12);
            }}
            .mm-read-title {{
                color: rgba(255,255,255,0.58);
                font-size: .66rem;
                font-weight: 900;
                letter-spacing: .1em;
                text-transform: uppercase;
                margin-bottom: .24rem;
            }}
            .mm-read-value {{
                color: #ffffff;
                font-size: .88rem;
                font-weight: 800;
                line-height: 1.34;
                overflow-wrap: anywhere;
            }}
            .mm-workflow-rail {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: .5rem;
                margin: .65rem 0 .8rem;
            }}
            .mm-rail-step {{
                background: #ffffff;
                border: 1px solid #e1e7ef;
                border-radius: 8px;
                padding: .62rem .7rem;
                box-shadow: 0 8px 22px rgba(15,23,42,0.045);
                position: relative;
            }}
            .mm-rail-step::before {{
                content: "";
                position: absolute;
                inset: 0 auto 0 0;
                width: 3px;
                background: #c1121f;
                border-radius: 8px 0 0 8px;
            }}
            .mm-rail-label {{
                color: #64748b;
                font-size: .62rem;
                font-weight: 900;
                letter-spacing: .1em;
                text-transform: uppercase;
                margin-bottom: .16rem;
            }}
            .mm-rail-title {{
                color: #0b0f14;
                font-size: .82rem;
                font-weight: 900;
            }}
            .mm-stat-card {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-top: 3px solid #0b0f14;
                border-radius: 8px;
                padding: .72rem .78rem;
            }}
            .mm-stat-card.is-red {{
                border-top-color: #c1121f;
            }}
            .mm-stat-label {{
                color: #64748b;
                font-size: .68rem;
                font-weight: 850;
                letter-spacing: .08em;
                text-transform: uppercase;
                margin-bottom: .18rem;
            }}
            .mm-stat-value {{
                color: #0b0f14;
                font-size: 1.25rem;
                line-height: 1.1;
                font-weight: 950;
            }}
            .mm-profile-strip {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: .55rem;
                margin: .65rem 0;
            }}
            .mm-profile-card {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-left: 3px solid #c1121f;
                border-radius: 8px;
                padding: .72rem .78rem;
            }}
            .mm-profile-title {{
                color: #0b0f14;
                font-weight: 900;
                font-size: .86rem;
                margin-bottom: .18rem;
            }}
            .mm-profile-copy {{
                color: #64748b;
                font-weight: 650;
                font-size: .78rem;
                line-height: 1.36;
                overflow-wrap: anywhere;
            }}
            .mm-scout-shell {{
                display: grid;
                grid-template-columns: minmax(0, 1.28fr) minmax(310px, .72fr);
                gap: .9rem;
                margin: .8rem 0 1rem;
            }}
            .mm-command-panel {{
                background: #0f172a;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
                padding: 1rem;
                min-height: 100%;
                box-shadow: 0 22px 50px rgba(15,23,42,0.18);
            }}
            .mm-command-panel * {{
                color: inherit;
            }}
            .mm-command-title {{
                color: #ffffff;
                font-size: 1rem;
                font-weight: 900;
                letter-spacing: .08em;
                text-transform: uppercase;
                margin-bottom: .75rem;
            }}
            .mm-command-row {{
                display: grid;
                grid-template-columns: 7.2rem minmax(0, 1fr);
                gap: .75rem;
                padding: .64rem 0;
                border-top: 1px solid rgba(255,255,255,0.1);
            }}
            .mm-command-label {{
                color: rgba(226,232,240,0.62);
                font-size: .68rem;
                font-weight: 850;
                text-transform: uppercase;
                letter-spacing: .08em;
            }}
            .mm-command-value {{
                color: #f8fafc;
                font-size: .88rem;
                line-height: 1.35;
                font-weight: 650;
            }}
            .mm-workflow-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: .7rem;
                margin: .75rem 0 1rem;
            }}
            .mm-workflow-card {{
                background: #ffffff;
                border: 1px solid #dbe3ee;
                border-radius: 10px;
                padding: .9rem;
            }}
            .mm-workflow-step {{
                color: #c1121f;
                font-size: .68rem;
                font-weight: 900;
                letter-spacing: .12em;
                text-transform: uppercase;
                margin-bottom: .32rem;
            }}
            .mm-workflow-title {{
                color: #0f172a;
                font-weight: 900;
                margin-bottom: .28rem;
            }}
            .mm-workflow-copy {{
                color: #64748b;
                font-size: .84rem;
                line-height: 1.42;
                font-weight: 550;
            }}
            div[data-testid="stSidebar"] {{
                background: #ffffff !important;
            }}
            @media (max-width: 980px) {{
                .mm-scout-shell,
                .mm-workflow-grid,
                .mm-command-center,
                .mm-stat-grid,
                .mm-profile-strip,
                .mm-kpi-deck,
                .mm-read-strip,
                .mm-workflow-rail {{
                    grid-template-columns: 1fr;
                    align-items: flex-start;
                }}
                .mm-filter-summary {{
                    flex-direction: column;
                }}
                .mm-filter-chips {{
                    justify-content: flex-start;
                }}
            }}

            /* Modern single-file product layer */
            .stApp {{
                background:
                    linear-gradient(180deg, #0b0f14 0, #0b0f14 7.25rem, #f4f6f8 7.25rem, #f4f6f8 100%) !important;
                color: #0b0f14;
            }}
            .block-container {{
                max-width: 1480px;
                padding: 1rem 1.4rem 3rem;
            }}
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] {{
                width: 17rem !important;
                min-width: 17rem !important;
                max-width: 17rem !important;
            }}
            div[data-testid="stSidebar"] {{
                background: #ffffff !important;
                border-right: 1px solid #e2e8f0;
                box-shadow: 12px 0 36px rgba(15,23,42,0.05);
            }}
            div[data-testid="stSidebar"] h3 {{
                font-size: .74rem;
                letter-spacing: .12em;
                text-transform: uppercase;
                color: #64748b !important;
                margin: .2rem 0 .45rem;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] {{
                display: grid;
                gap: .26rem;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: .55rem .65rem;
                min-height: 38px;
                transition: background .15s ease, border-color .15s ease, box-shadow .15s ease;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
                background: #f1f5f9;
                border-color: #cbd5e1;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
                background: #0b0f14;
                border-color: #0b0f14;
                box-shadow: inset 4px 0 0 #c1121f;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span,
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) div {{
                color: #ffffff !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div,
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: #ffffff !important;
                border: 1px solid #d8dee8 !important;
                border-radius: 8px !important;
                box-shadow: 0 1px 0 rgba(15,23,42,0.03);
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div:focus-within,
            [data-baseweb="select"] > div:focus-within,
            [data-baseweb="input"] > div:focus-within,
            textarea:focus {{
                border-color: #c1121f !important;
                box-shadow: 0 0 0 3px rgba(193,18,31,0.12) !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] {{
                background: #111827 !important;
                border-radius: 999px !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="tag"] span {{
                color: #ffffff !important;
            }}
            .mm-hero {{
                background: #0b0f14 !important;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 8px;
                box-shadow: 0 20px 60px rgba(2,6,23,0.20);
                padding: 1.35rem 1.45rem;
            }}
            .mm-hero::before {{
                height: 3px;
                background: #c1121f;
            }}
            .mm-eyebrow {{
                color: rgba(255,255,255,0.58) !important;
                letter-spacing: .14em;
            }}
            .mm-title {{
                font-size: clamp(1.9rem, 2.7vw, 2.9rem);
                letter-spacing: 0;
            }}
            .mm-copy {{
                color: rgba(248,250,252,0.78) !important;
                max-width: 920px;
            }}
            .mm-feature-pill,
            .mm-nav-card,
            .mm-insight-card,
            .mm-panel,
            .mm-stat-card,
            .mm-profile-card,
            .mm-kpi-card,
            .mm-read-card,
            .mm-rail-step,
            .mm-filter-summary,
            .mm-command-panel,
            .mm-workflow-card,
            .mm-empty-state,
            div[data-testid="stMetric"],
            [data-testid="stDataFrameResizable"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                border-radius: 8px !important;
                border: 1px solid #e1e7ef;
                box-shadow: 0 10px 28px rgba(15,23,42,0.055);
            }}
            .mm-feature-pill,
            .mm-nav-card,
            .mm-insight-card,
            .mm-panel,
            .mm-profile-card,
            .mm-workflow-card,
            .mm-filter-summary,
            div[data-testid="stMetric"],
            [data-testid="stDataFrameResizable"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stImage"],
            div[data-testid="stPyplot"] {{
                background: #ffffff !important;
            }}
            .mm-feature-pill {{
                border-left: 0;
                border-top: 3px solid #0b0f14;
            }}
            .mm-nav-card {{
                min-height: 188px;
                padding: 1rem;
            }}
            .mm-nav-card::before {{
                height: 3px;
                background: #c1121f;
            }}
            .mm-nav-card:hover {{
                transform: translateY(-2px);
                border-color: rgba(193,18,31,0.35);
                box-shadow: 0 16px 38px rgba(15,23,42,0.10);
            }}
            .mm-command-panel {{
                background: #10151c !important;
                border-color: rgba(255,255,255,0.10);
            }}
            .mm-section {{
                margin: 1.25rem 0 .65rem;
                padding: 0;
            }}
            .mm-section-title {{
                font-size: .86rem;
                letter-spacing: .11em;
            }}
            .mm-section-title::before {{
                width: .45rem;
                height: .45rem;
                box-shadow: none;
            }}
            .mm-filter-summary {{
                align-items: flex-start;
                padding: .78rem .9rem;
            }}
            .mm-filter-count {{
                font-size: .92rem;
            }}
            .mm-chip,
            .mm-tiny {{
                background: #f8fafc;
                border-color: #e2e8f0;
                border-radius: 999px;
            }}
            div[data-testid="stMetric"] {{
                border-top: 3px solid #0b0f14;
            }}
            div[data-testid="stMetric"]::before {{
                display: none;
            }}
            div[data-testid="stMetricValue"] {{
                font-size: 1.42rem;
            }}
            div[data-testid="stTabs"] [role="tablist"] {{
                border: 1px solid #e2e8f0;
                box-shadow: none;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                border: 0 !important;
                min-height: 34px;
                text-transform: none;
                letter-spacing: 0;
                font-size: .84rem;
                font-weight: 800;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: #0b0f14 !important;
                color: #ffffff !important;
                box-shadow: inset 0 -3px 0 #c1121f;
            }}
            div.stButton > button,
            div[data-testid="stDownloadButton"] > button {{
                border-radius: 8px;
                min-height: 38px;
                letter-spacing: 0;
                text-transform: none;
                font-size: .84rem;
                font-weight: 850;
                background: #c1121f;
                border-color: #c1121f;
            }}
            div.stButton > button[kind="secondary"],
            div[data-testid="stDownloadButton"] > button[kind="secondary"] {{
                background: #ffffff;
                color: #0b0f14 !important;
                border-color: #d8dee8;
            }}
            div.stButton > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {{
                background: #991b1b;
                border-color: #991b1b;
            }}
            .mm-table-note {{
                color: #64748b;
                font-size: .78rem;
                letter-spacing: 0;
                text-transform: none;
            }}
            @media (max-width: 760px) {{
                .block-container {{
                    padding: .75rem .85rem 2.2rem;
                }}
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div,
                div[data-testid="stSidebar"] {{
                    width: 100% !important;
                    min-width: 100% !important;
                    max-width: 100% !important;
                }}
                .mm-title {{
                    font-size: 1.85rem;
                }}
            }}
            @media (min-width: 761px) and (max-width: 1180px) {{
                .mm-stat-grid,
                .mm-kpi-deck {{
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }}
                .mm-read-strip,
                .mm-profile-strip,
                .mm-workflow-rail {{
                    grid-template-columns: 1fr;
                }}
            }}

            /* ── Final product skin ─────────────────────────────── */
            :root {{
                --sp-bg: #f2f4f7;
                --sp-surface: #ffffff;
                --sp-sidebar: #0f172a;
                --sp-sidebar-border: rgba(148,163,184,0.18);
                --sp-ink: #0b0f14;
                --sp-muted: #64748b;
                --sp-line: #e2e8f0;
                --sp-red: #c1121f;
                --sp-red-d: #991b1b;
                --sp-accent: #c1121f;
            }}

            /* Body & chrome */
            .stApp {{
                background: var(--sp-bg) !important;
                color: var(--sp-ink) !important;
            }}
            h1, h2, h3, h4, h5, h6, p, label, span {{
                color: var(--sp-ink);
            }}
            .block-container {{
                max-width: 1520px !important;
                padding: 1rem 1.55rem 3rem !important;
            }}
            header[data-testid="stHeader"] {{
                background: transparent !important;
            }}

            /* Sidebar — dark panel */
            section[data-testid="stSidebar"],
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] {{
                background: var(--sp-sidebar) !important;
                border-right: 1px solid rgba(255,255,255,0.06) !important;
                box-shadow: 4px 0 24px rgba(0,0,0,0.18) !important;
                width: 17rem !important;
                min-width: 17rem !important;
                max-width: 17rem !important;
                color-scheme: dark !important;
            }}
            div[data-testid="stSidebar"] *,
            div[data-testid="stSidebar"] span,
            div[data-testid="stSidebar"] div,
            div[data-testid="stSidebar"] button,
            div[data-testid="stSidebar"] a,
            div[data-testid="stSidebar"] p,
            div[data-testid="stSidebar"] label {{
                color: #e2e8f0 !important;
            }}
            div[data-testid="stSidebar"] h3 {{
                color: #94a3b8 !important;
                font-size: .68rem;
                letter-spacing: .16em;
                text-transform: uppercase;
                margin: .8rem 0 .4rem;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] {{
                display: grid;
                gap: .2rem;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label {{
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid rgba(255,255,255,0.07) !important;
                border-radius: 6px !important;
                padding: .5rem .65rem !important;
                min-height: 36px !important;
                transition: background .1s ease !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
                background: rgba(255,255,255,0.08) !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
                background: rgba(193,18,31,0.22) !important;
                border-color: rgba(193,18,31,0.50) !important;
                box-shadow: inset 3px 0 0 #c1121f !important;
            }}
            div[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) span {{
                color: #ffffff !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] > div,
            div[data-testid="stSidebar"] [data-baseweb="input"] > div {{
                background: rgba(255,255,255,0.07) !important;
                border: 1px solid rgba(148,163,184,0.25) !important;
                border-radius: 6px !important;
                box-shadow: none !important;
            }}
            div[data-testid="stSidebar"] [data-baseweb="select"] span,
            div[data-testid="stSidebar"] [data-baseweb="select"] input,
            div[data-testid="stSidebar"] [data-baseweb="input"] input {{
                color: #e2e8f0 !important;
                -webkit-text-fill-color: #e2e8f0 !important;
            }}
            div[data-testid="stSidebar"] button {{
                background: rgba(193,18,31,0.85) !important;
                border-color: rgba(193,18,31,0.50) !important;
                color: #ffffff !important;
            }}
            div[data-testid="stSidebar"] button:hover {{
                background: #991b1b !important;
            }}
            div[data-testid="stSidebar"] hr {{
                border-color: rgba(148,163,184,0.18) !important;
            }}

            /* Dropdowns (main area) */
            [data-baseweb="select"] > div,
            [data-baseweb="input"] > div,
            textarea {{
                background: #ffffff !important;
                border: 1px solid #d8dee8 !important;
                border-radius: 7px !important;
                box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
            }}
            [data-baseweb="select"] > div:focus-within,
            [data-baseweb="input"] > div:focus-within,
            textarea:focus {{
                border-color: #c1121f !important;
                box-shadow: 0 0 0 3px rgba(193,18,31,0.10) !important;
            }}
            div[data-baseweb="popover"] ul,
            div[data-baseweb="popover"] [role="listbox"] {{
                background: #ffffff !important;
                border: 1px solid #dde3ec !important;
                box-shadow: 0 16px 48px rgba(15,23,42,0.14) !important;
                border-radius: 8px !important;
            }}
            div[data-baseweb="popover"] [role="option"],
            div[data-baseweb="popover"] [role="option"] *,
            div[data-baseweb="popover"] li,
            div[data-baseweb="popover"] li * {{
                color: #0b0f14 !important;
                -webkit-text-fill-color: #0b0f14 !important;
            }}
            div[data-baseweb="popover"] [aria-selected="true"],
            div[data-baseweb="popover"] [role="option"]:hover {{
                background: #f1f5f9 !important;
            }}

            /* Hero block */
            .mm-hero {{
                background: #0f172a !important;
                border: 0 !important;
                border-radius: 10px !important;
                padding: 1.4rem 1.6rem 1.5rem !important;
                box-shadow: 0 4px 24px rgba(15,23,42,0.18) !important;
                position: relative;
                overflow: hidden;
            }}
            .mm-hero::before {{
                content: "" !important;
                display: block !important;
                position: absolute !important;
                inset: 0 0 auto 0 !important;
                height: 3px !important;
                background: var(--sp-red) !important;
                border-radius: 10px 10px 0 0 !important;
            }}
            .mm-eyebrow {{
                color: rgba(148,163,184,0.9) !important;
                font-size: .68rem !important;
                letter-spacing: .18em !important;
                text-transform: uppercase !important;
            }}
            .mm-title {{
                color: #ffffff !important;
                font-size: clamp(1.85rem, 2.8vw, 3rem) !important;
                font-weight: 900 !important;
                letter-spacing: -.01em !important;
                line-height: 1.02 !important;
                text-transform: none !important;
            }}
            .mm-copy {{
                color: rgba(203,213,225,0.90) !important;
                font-size: .96rem !important;
                font-weight: 500 !important;
                max-width: 900px;
            }}

            /* Section divider */
            .mm-section {{
                border-bottom: 1px solid var(--sp-line) !important;
                background: none !important;
                border-radius: 0 !important;
                padding: 0 0 .4rem !important;
                margin: 1.4rem 0 .8rem !important;
            }}
            .mm-section-title {{
                color: #0b0f14 !important;
                font-size: .78rem !important;
                font-weight: 900 !important;
                text-transform: uppercase !important;
                letter-spacing: .12em !important;
            }}
            .mm-section-title::before {{
                background: var(--sp-red) !important;
                box-shadow: none !important;
                width: .38rem !important;
                height: .38rem !important;
            }}
            .mm-section-note {{
                color: var(--sp-muted) !important;
                font-size: .78rem !important;
            }}

            /* Cards, surfaces */
            .mm-feature-pill,
            .mm-nav-card,
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
                background: #ffffff !important;
                border: 1px solid var(--sp-line) !important;
                border-radius: 8px !important;
                box-shadow: 0 1px 4px rgba(15,23,42,0.06) !important;
            }}
            .mm-command-panel,
            .mm-read-card {{
                background: #0f172a !important;
                border: 1px solid rgba(255,255,255,0.10) !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 18px rgba(0,0,0,0.22) !important;
            }}
            .mm-command-title,
            .mm-read-value {{
                color: #f8fafc !important;
            }}
            .mm-command-label,
            .mm-read-title {{
                color: #94a3b8 !important;
            }}
            .mm-command-row {{
                border-top-color: rgba(148,163,184,0.18) !important;
            }}
            .mm-nav-card {{
                min-height: 175px !important;
                padding: .95rem 1rem !important;
            }}
            .mm-nav-card::before {{
                height: 3px !important;
                width: auto !important;
                inset: 0 0 auto 0 !important;
                background: var(--sp-red) !important;
                border-radius: 8px 8px 0 0 !important;
            }}
            .mm-nav-card:hover {{
                transform: translateY(-2px) !important;
                border-color: rgba(193,18,31,0.30) !important;
                box-shadow: 0 8px 28px rgba(15,23,42,0.10) !important;
            }}
            .mm-nav-title,
            .mm-panel-title,
            .mm-profile-title,
            .mm-workflow-title,
            .mm-stat-value,
            .mm-kpi-value,
            div[data-testid="stMetricValue"],
            .mm-feature-value,
            .mm-filter-count {{
                color: var(--sp-ink) !important;
            }}
            .mm-nav-copy,
            .mm-panel-copy,
            .mm-profile-copy,
            .mm-workflow-copy,
            .mm-stat-label,
            .mm-kpi-label,
            .mm-kpi-help,
            div[data-testid="stMetricLabel"] p,
            .mm-empty-copy,
            .mm-table-note {{
                color: var(--sp-muted) !important;
            }}
            .mm-card-kicker,
            .mm-workflow-step {{
                color: var(--sp-red) !important;
            }}
            .mm-feature-pill {{
                border-top: 0 !important;
                border-left: 3px solid var(--sp-red) !important;
            }}
            .mm-kpi-card,
            .mm-stat-card,
            div[data-testid="stMetric"] {{
                border-top: 3px solid var(--sp-ink) !important;
            }}
            .mm-kpi-card.is-red,
            .mm-stat-card.is-red {{
                border-top-color: var(--sp-red) !important;
            }}
            div[data-testid="stMetric"]::before {{
                display: none !important;
            }}
            div[data-testid="stMetricValue"] {{
                font-size: 1.45rem !important;
            }}

            /* Insight card */
            .mm-insight-card {{
                padding: .82rem .95rem .82rem 1.05rem !important;
                min-height: auto !important;
            }}
            .mm-insight-card::before {{
                background: var(--sp-red) !important;
                top: 0 !important;
                bottom: 0 !important;
                border-radius: 8px 0 0 8px !important;
            }}

            /* Chips & tags */
            .mm-tiny,
            .mm-chip {{
                background: #f1f5f9 !important;
                border: 1px solid #dde3ec !important;
                color: #334155 !important;
                border-radius: 6px !important;
            }}
            .mm-chip strong {{
                color: var(--sp-ink) !important;
            }}

            /* Filter summary */
            .mm-filter-card {{
                background: #f8fafc !important;
                border: 1px solid var(--sp-line) !important;
                border-radius: 6px !important;
            }}
            .mm-filter-label {{
                color: var(--sp-muted) !important;
            }}
            .mm-filter-value {{
                color: var(--sp-ink) !important;
            }}

            /* Tabs — pill style */
            div[data-testid="stTabs"] [role="tablist"] {{
                background: #ffffff !important;
                border: 1px solid var(--sp-line) !important;
                border-radius: 8px !important;
                padding: .3rem !important;
                box-shadow: none !important;
                gap: .2rem !important;
                margin-bottom: .5rem !important;
            }}
            div[data-testid="stTabs"] button[role="tab"] {{
                background: transparent !important;
                border: 0 !important;
                border-radius: 6px !important;
                color: var(--sp-muted) !important;
                font-size: .82rem !important;
                font-weight: 700 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 34px !important;
                padding: .3rem .85rem !important;
                transition: background .1s ease, color .1s ease !important;
            }}
            div[data-testid="stTabs"] button[role="tab"]:hover {{
                background: #f1f5f9 !important;
                color: var(--sp-ink) !important;
            }}
            div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
                background: var(--sp-red) !important;
                color: #ffffff !important;
                box-shadow: none !important;
            }}

            /* Buttons */
            div.stButton > button,
            div[data-testid="stDownloadButton"] > button {{
                background: var(--sp-red) !important;
                border: 0 !important;
                border-radius: 7px !important;
                color: #ffffff !important;
                font-size: .82rem !important;
                font-weight: 800 !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                min-height: 38px !important;
                box-shadow: none !important;
            }}
            div.stButton > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {{
                background: var(--sp-red-d) !important;
            }}

            /* Misc */
            div[data-testid="stCaptionContainer"] p,
            .stCaptionContainer p {{
                color: var(--sp-muted) !important;
            }}
            div[data-testid="stAlert"] {{
                background: #ffffff !important;
                border: 1px solid var(--sp-line) !important;
                border-radius: 8px !important;
            }}
            div[data-testid="stDataFrameResizable"] {{
                background: #ffffff !important;
            }}
            .mm-table-note {{
                color: var(--sp-muted) !important;
                font-size: .78rem !important;
            }}
            @media (max-width: 760px) {{
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div,
                div[data-testid="stSidebar"] {{
                    width: 100% !important;
                    min-width: 100% !important;
                    max-width: 100% !important;
                }}
                .mm-title {{
                    font-size: 1.8rem !important;
                }}
                .block-container {{
                    padding: .75rem .85rem 2rem !important;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
