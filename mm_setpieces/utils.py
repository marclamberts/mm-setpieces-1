
from __future__ import annotations

from pathlib import Path
from io import BytesIO
from html import escape
import os
import tempfile
import textwrap
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PITCH_LENGTH = 120
PITCH_WIDTH = 80
HALF_START = 60
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"

BLACK = "#0b0f14"
RED = "#c1121f"
RED_DARK = "#780000"
INK = "#111827"
MUTED = "#475569"
BORDER = "rgba(17,24,39,0.12)"

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mm-setpieces-mpl"))


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
                height: calc(100vh - 2.6rem);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 1.15rem;
                padding: 0 1rem 1.4rem;
                overflow: hidden;
            }}
            .mm-landing-shell div[data-testid="stImage"] {{
                background: transparent;
                border: 0;
                border-radius: 0;
                padding: 0;
                box-shadow: none;
                width: min(460px, 76vw);
            }}
            .mm-landing-shell div[data-testid="stImage"] img {{
                display: block;
                width: 100%;
                height: auto;
            }}
            .mm-landing-action {{
                width: min(300px, 76vw);
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_menu(active: str = "Home", filters: list[tuple[str, str]] | None = None) -> None:
    st.sidebar.markdown("### Desk")
    st.sidebar.caption("Use the single app selector in app.py to switch views.")
    st.sidebar.markdown(f"### {active} filters")
    if filters:
        for label, value in filters:
            st.sidebar.markdown(
                f"""
                <div class="mm-filter-card">
                    <div class="mm-filter-label">{escape(str(label))}</div>
                    <div class="mm-filter-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _format_filter_value(value: object) -> str:
    if value is None:
        return "All"
    if isinstance(value, (list, tuple, set)):
        cleaned = [str(v) for v in value if str(v).strip()]
        if not cleaned:
            return "All"
        if len(cleaned) <= 2:
            return ", ".join(cleaned)
        return f"{', '.join(cleaned[:2])} +{len(cleaned) - 2}"
    text = str(value).strip()
    return text or "All"


def render_filter_summary(
    label: str,
    source_rows: int,
    filtered_rows: int,
    filters: list[tuple[str, object]],
) -> None:
    active = [
        (name, _format_filter_value(value))
        for name, value in filters
        if _format_filter_value(value) not in {"All", "Total", "0-95"}
    ]
    chips = "".join(
        f"<span class='mm-chip'><strong>{escape(str(name))}:</strong>{escape(str(value))}</span>"
        for name, value in active[:8]
    )
    if len(active) > 8:
        chips += f"<span class='mm-chip'><strong>More</strong>{len(active) - 8} filters</span>"
    if not chips:
        chips = "<span class='mm-chip'><strong>Filters</strong>Full sample</span>"

    st.markdown(
        f"""
        <div class="mm-filter-summary">
            <div class="mm-filter-count">{escape(label)} · {filtered_rows:,} of {source_rows:,} rows</div>
            <div class="mm-filter-chips">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_filter_state() -> None:
    st.markdown(
        """
        <div class="mm-empty-state">
            <div class="mm-empty-title">No rows match these filters.</div>
            <div class="mm-empty-copy">Widen the team, minute, player, or outcome filters in the sidebar to bring events back into the view.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_rail() -> None:
    steps = [
        ("1", "Filter opponent"),
        ("2", "Read KPIs"),
        ("3", "Check evidence"),
        ("4", "Export brief"),
    ]
    html = "<div class='mm-workflow-rail'>"
    for number, title in steps:
        html += (
            "<div class='mm-rail-step'>"
            f"<div class='mm-rail-label'>Step {escape(number)}</div>"
            f"<div class='mm-rail-title'>{escape(title)}</div>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def hero_block(eyebrow: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="mm-hero">
            <div class="mm-eyebrow">{eyebrow}</div>
            <div class="mm-title">{title}</div>
            <div class="mm-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, note: str = "") -> None:
    note_html = f'<div class="mm-section-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="mm-section">
            <div class="mm-section-title">{title}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def polish_plotly_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font=dict(color=BLACK, family="Arial, sans-serif"),
        title_font=dict(color=BLACK, size=18),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        colorway=[RED, BLACK, "#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#64748b"],
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(15,23,42,0.08)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(15,23,42,0.08)", zeroline=False)
    return fig


@st.cache_data(show_spinner=False)
def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


def render_export_controls(df: pd.DataFrame, slug: str, sheet_name: str = "Data") -> None:
    st.markdown('<div class="mm-table-note">Exports are prepared only when needed to keep page reruns fast.</div>', unsafe_allow_html=True)
    if not st.checkbox("Prepare export files", key=f"{slug}_prepare_exports"):
        return

    csv_col, excel_col = st.columns(2)
    safe_slug = slug.lower().replace(" ", "_").replace("/", "-")
    with csv_col:
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{safe_slug}_filtered.csv",
            mime="text/csv",
            width="stretch",
        )
    with excel_col:
        st.download_button(
            "Download Excel",
            data=dataframe_to_excel_bytes(df, sheet_name=sheet_name[:31] or "Data"),
            file_name=f"{safe_slug}_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )


def categorical_breakdown_figure(
    df: pd.DataFrame,
    column: str,
    title: str,
    *,
    top_n: int = 8,
    color: str = RED,
) -> go.Figure:
    fig = go.Figure()
    if df.empty or column not in df.columns:
        fig.add_annotation(text="No data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    counts = (
        df[column]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .head(top_n)
        .sort_values(ascending=True)
    )

    fig.add_trace(
        go.Bar(
            x=counts.values,
            y=counts.index.tolist(),
            orientation="h",
            marker=dict(color=color),
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=340, margin=dict(l=10, r=10, t=45, b=10), showlegend=False)
    return polish_plotly_figure(fig)


def minute_distribution_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty or "minute" not in df.columns:
        fig.add_annotation(text="No minute data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    minutes = pd.to_numeric(df["minute"], errors="coerce").dropna()
    if minutes.empty:
        fig.add_annotation(text="No minute data available", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
        return polish_plotly_figure(fig)

    bins = list(range(0, int(max(95, minutes.max())) + 6, 5))
    bucket = pd.cut(minutes, bins=bins, right=False, include_lowest=True)
    counts = bucket.value_counts().sort_index()
    labels = [f"{int(interval.left)}-{int(interval.right - 1)}" for interval in counts.index]
    fig.add_trace(
        go.Bar(
            x=labels,
            y=counts.values,
            marker=dict(color=BLACK),
            hovertemplate="Minute window %{x}: %{y}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=340, margin=dict(l=10, r=10, t=45, b=10), showlegend=False)
    return polish_plotly_figure(fig)

def _candidate_paths(filename: str) -> list[Path]:
    return [DATA_DIR / filename, BASE_DIR.parent / filename, BASE_DIR / filename, Path(filename)]

@st.cache_data(show_spinner=False)
def _read_excel_if_exists(filename: str, sheet_name=0) -> pd.DataFrame:
    for path in _candidate_paths(filename):
        if path.exists():
            return pd.read_excel(path, sheet_name=sheet_name)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def _read_csv_if_exists(filename: str) -> pd.DataFrame:
    for path in _candidate_paths(filename):
        if path.exists():
            return pd.read_csv(path)
    return pd.DataFrame()

def _with_league(df: pd.DataFrame, league: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "League" not in df.columns:
        df["League"] = league
    else:
        df["League"] = df["League"].fillna(league)
    return df

def _canonical_sp_type(value: object) -> str:
    text = str(value).strip()
    lowered = text.lower()
    if "free kick" in lowered or "freekick" in lowered:
        return "From Free Kick"
    if "throw in" in lowered or "throw-in" in lowered or "throwin" in lowered:
        return "From Throw In"
    if "corner" in lowered:
        return "From Corner"
    return text

def _canonical_sp_type_series(series: pd.Series) -> pd.Series:
    return series.map(_canonical_sp_type)

@st.cache_data(show_spinner=False)
def _load_czech_sp_data() -> pd.DataFrame:
    cz = _read_excel_if_exists("Czech SP.xlsx")
    if cz.empty:
        return cz
    cz = cz.copy()
    if "SP_Type" not in cz.columns and "play_pattern.name" in cz.columns:
        cz["SP_Type"] = cz["play_pattern.name"]
    if "SP_Type" in cz.columns:
        cz["SP_Type"] = _canonical_sp_type_series(cz["SP_Type"])
    return cz

def _fill_from_candidates(df: pd.DataFrame, target: str, candidates: list[str], default=np.nan) -> None:
    if target not in df.columns:
        df[target] = pd.Series(np.nan, index=df.index, dtype="object")
    else:
        df[target] = df[target].astype("object")
    for cand in candidates:
        if cand == target or cand not in df.columns:
            continue
        missing = df[target].isna()
        if missing.any():
            df.loc[missing, target] = df.loc[missing, cand]
    df[target] = df[target].fillna(default)

@st.cache_data(show_spinner=False)
def _cz_taker_team_map() -> dict[str, str]:
    cz_sp = _load_czech_sp_data()
    if cz_sp.empty or "team.name" not in cz_sp.columns:
        return {}
    player_col = "player.name" if "player.name" in cz_sp.columns else "Taker" if "Taker" in cz_sp.columns else None
    if player_col is None:
        return {}
    taker_team = (
        cz_sp[[player_col, "team.name"]]
        .dropna()
        .astype(str)
        .groupby(player_col)["team.name"]
        .agg(lambda s: s.value_counts().idxmax())
    )
    return taker_team.to_dict()

@st.cache_data(show_spinner=False)
def load_corner_data() -> pd.DataFrame:
    cz_corners = _read_csv_if_exists("CZ - Corners 2025-2026.csv")
    if not cz_corners.empty:
        cz_corners = cz_corners.copy()
        if "Team" not in cz_corners.columns and "Taker" in cz_corners.columns:
            cz_corners["Team"] = cz_corners["Taker"].astype(str).map(_cz_taker_team_map())
    sources = [
        _with_league(_read_excel_if_exists("Allsvenskan - Corners 2025.xlsx"), "Allsvenskan"),
        _with_league(cz_corners, "Czech First League"),
    ]
    sources = [df for df in sources if not df.empty]
    return pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_swe_sp_data() -> pd.DataFrame:
    swe = _with_league(_read_excel_if_exists("SWE SP.xlsx"), "Allsvenskan")
    if not swe.empty and "SP_Type" in swe.columns:
        swe = swe.copy()
        swe["SP_Type"] = _canonical_sp_type_series(swe["SP_Type"])
    cz = _with_league(_load_czech_sp_data(), "Czech First League")
    sources = [df for df in [swe, cz] if not df.empty]
    return pd.concat(sources, ignore_index=True, sort=False) if sources else pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_sp_data(label: str) -> pd.DataFrame:
    if label == "Corners":
        return load_corner_data().copy()

    raw = load_swe_sp_data().copy()
    if raw.empty or "SP_Type" not in raw.columns:
        return pd.DataFrame()

    mapping = {
        "Freekicks": "From Free Kick",
        "Throw ins": "From Throw In",
    }
    sp_type = mapping.get(label)
    if sp_type:
        sp = _canonical_sp_type_series(raw["SP_Type"])
        return raw[sp.eq(sp_type)].copy()
    return pd.DataFrame()


def filter_by_sp_type(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "SP_Type" not in df.columns:
        return df
    mapping = {
        "Freekicks": "From Free Kick",
        "Throw ins": "From Throw In",
    }
    wanted = mapping.get(label)
    if not wanted:
        return df
    sp = _canonical_sp_type_series(df["SP_Type"])
    return df[sp.eq(wanted)].copy()

def _ensure_column(df: pd.DataFrame, target: str, candidates: list[str], default=np.nan):
    _fill_from_candidates(df, target, candidates, default)

def prepare_sp_dataframe(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    if label == "Corners":
        _ensure_column(df, "Team", ["Team", "pass_team_name", "shot_team_name"], "Unknown")
        _ensure_column(df, "Match", ["Match"], "Unknown")
        _ensure_column(df, "minute", ["minute", "Minute"], 0)
        _ensure_column(df, "second", ["second", "Second"], 0)
        _ensure_column(df, "Technique", ["Technique", "pass.technique.name", "pass_technique"], "Unknown")
        _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name", "pass_height"], "Unknown")
        _ensure_column(df, "Delivery outcome", ["SP_outcome", "Delivery outcome", "pass.outcome.name", "pass_outcome"], "Unknown")
        _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name", "shot_outcome"], "No shot")
        _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
        _ensure_column(df, "Taker", ["Taker"], "Unknown")
        _ensure_column(df, "League", ["League"], "Allsvenskan")
        _ensure_column(df, "shot_x", ["shot_x", "shot_location_x"], np.nan)
        _ensure_column(df, "shot_y", ["shot_y", "shot_location_y"], np.nan)
        _ensure_column(df, "delivery_end_x", ["delivery_end_x", "pass_end_location_x", "end_x"], np.nan)
        _ensure_column(df, "delivery_end_y", ["delivery_end_y", "pass_end_location_y", "end_y"], np.nan)
        _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg", "shot_statsbomb_xg"], 0.0)

        for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Shooter", "Taker", "League"]:
            fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
            df[col] = df[col].fillna(fill)

        for col in ["minute", "second", "match_id", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "side" not in df.columns:
            if "pass_location_y" in df.columns:
                py = pd.to_numeric(df["pass_location_y"], errors="coerce")
                df["side"] = np.where(py <= 40, "Left", "Right")
            else:
                df["side"] = "Unknown"

        if "is_shot" not in df.columns:
            df["is_shot"] = df[["shot_x", "shot_y"]].notna().all(axis=1)
        if "is_goal" not in df.columns:
            df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

        if "game_period" not in df.columns:
            minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
            bins = [-1, 15, 30, 45, 60, 75, 200]
            labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
            df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

        if "match_rank" not in df.columns:
            if "match_id" in df.columns:
                match_order = (
                    df[["match_id"]]
                    .dropna()
                    .drop_duplicates()
                    .sort_values("match_id", ascending=False)
                    .reset_index(drop=True)
                )
                match_order["match_rank"] = range(1, len(match_order) + 1)
                df = df.merge(match_order, on="match_id", how="left")
            else:
                df["match_rank"] = 999
        return df

    _ensure_column(df, "Team", ["Team", "team.name"], "Unknown")
    _ensure_column(df, "Match", ["Match"], "Unknown")
    _ensure_column(df, "Technique", ["Technique", "type.name", "pass.technique.name"], "Unknown")
    _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name"], "Unknown")
    _ensure_column(df, "Delivery outcome", ["Delivery outcome", "Metrics", "pass.outcome.name"], "Unknown")
    _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name"], "No shot")
    _ensure_column(df, "Taker", ["Taker"], "Unknown")
    _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
    _ensure_column(df, "League", ["League"], "Allsvenskan")
    _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg"], 0.0)

    if "Match" in df.columns and (df["Match"].isna().all() or df["Match"].astype(str).eq("Unknown").all()) and "match_id" in df.columns:
        df["Match"] = "Match " + df["match_id"].astype(str)

    for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Taker", "Shooter", "League"]:
        fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
        df[col] = df[col].fillna(fill)

    if "location.pass" in df.columns:
        pass_xy = df["location.pass"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if pass_xy.shape[1] >= 2:
            df["pass_x"] = pd.to_numeric(pass_xy[0].str.strip(), errors="coerce")
            df["pass_y"] = pd.to_numeric(pass_xy[1].str.strip(), errors="coerce")

    if "side" not in df.columns:
        if "pass_y" in df.columns:
            df["side"] = np.where(df["pass_y"] <= 40, "Left", "Right")
        else:
            df["side"] = "Unknown"

    if "location.shot" in df.columns:
        shot_xy = df["location.shot"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if shot_xy.shape[1] >= 2:
            df["shot_x"] = pd.to_numeric(shot_xy[0].str.strip(), errors="coerce")
            df["shot_y"] = pd.to_numeric(shot_xy[1].str.strip(), errors="coerce")

    _ensure_column(df, "shot_x", ["shot_x"], np.nan)
    _ensure_column(df, "shot_y", ["shot_y"], np.nan)
    _ensure_column(df, "delivery_end_x", ["delivery_end_x", "shot_x"], np.nan)
    _ensure_column(df, "delivery_end_y", ["delivery_end_y", "shot_y"], np.nan)

    if "minute" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            if parts.shape[1] >= 2:
                hours = pd.to_numeric(parts[0], errors="coerce").fillna(0)
                minutes = pd.to_numeric(parts[1], errors="coerce").fillna(0)
                df["minute"] = hours * 60 + minutes
            else:
                df["minute"] = pd.to_numeric(parts[0], errors="coerce").fillna(0) if parts.shape[1] >= 1 else 0
        else:
            df["minute"] = 0

    if "second" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            df["second"] = pd.to_numeric(parts[2], errors="coerce").fillna(0) if parts.shape[1] >= 3 else 0
        else:
            df["second"] = 0

    for col in ["minute", "second", "match_id", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_shot" not in df.columns:
        df["is_shot"] = df["shot_x"].notna() & df["shot_y"].notna()
    if "is_goal" not in df.columns:
        df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

    if "game_period" not in df.columns:
        minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
        bins = [-1, 15, 30, 45, 60, 75, 200]
        labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
        df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

    if "match_rank" not in df.columns:
        if "match_id" in df.columns:
            order = (
                df[["match_id"]]
                .dropna()
                .drop_duplicates()
                .sort_values("match_id", ascending=False)
                .reset_index(drop=True)
            )
            order["match_rank"] = range(1, len(order) + 1)
            df = df.merge(order, on="match_id", how="left")
        else:
            df["match_rank"] = 999
    return df


@st.cache_data(show_spinner=False)
def load_prepared_sp_data(label: str) -> pd.DataFrame:
    raw = load_sp_data(label)
    return filter_by_sp_type(prepare_sp_dataframe(raw, label=label), label)


def _is_swe_sp_df(df: pd.DataFrame) -> bool:
    return "SP_Type" in df.columns

def unique_shot_events(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "shot_x" not in df.columns or "shot_y" not in df.columns:
        return df.iloc[0:0].copy()
    shots = df[df["shot_x"].notna() & df["shot_y"].notna()].copy()
    if shots.empty:
        return shots
    if _is_swe_sp_df(shots):
        keys = [c for c in ["match_id", "possession", "Team", "shot_x", "shot_y", "Shot outcome", "xg"] if c in shots.columns]
        if keys:
            shots = shots.drop_duplicates(subset=keys)
    return shots

def unique_start_events(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if _is_swe_sp_df(df):
        keys = [c for c in ["match_id", "possession", "Team", "pass_x", "pass_y", "Taker", "timestamp"] if c in df.columns]
        if keys:
            return df.drop_duplicates(subset=keys)
    return df

def vertical_coords_from_statsbomb(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")

def restart_origin_xy(side: str) -> tuple[float, float]:
    return (0.0, 120.0) if str(side).lower() == "left" else (80.0, 120.0)

def add_half_vertical_pitch_layout(fig: go.Figure, title: str, pitch_color: str = "white", height: int = 620) -> go.Figure:
    fig.update_xaxes(range=[0, PITCH_WIDTH], visible=False)
    fig.update_yaxes(range=[HALF_START, PITCH_LENGTH], visible=False, scaleanchor="x", scaleratio=1)

    penalty_left = (PITCH_WIDTH / 2) - 22
    penalty_right = (PITCH_WIDTH / 2) + 22
    six_left = (PITCH_WIDTH / 2) - 10
    six_right = (PITCH_WIDTH / 2) + 10

    zone_shapes = [
        dict(type="rect", x0=30, y0=114, x1=36.67, y1=120, line=dict(width=0.8, color="rgba(37,99,235,0.55)"), fillcolor="rgba(37,99,235,0.10)", layer="below"),
        dict(type="rect", x0=36.67, y0=114, x1=43.33, y1=120, line=dict(width=0.8, color="rgba(22,163,74,0.55)"), fillcolor="rgba(22,163,74,0.10)", layer="below"),
        dict(type="rect", x0=43.33, y0=114, x1=50, y1=120, line=dict(width=0.8, color="rgba(245,158,11,0.55)"), fillcolor="rgba(245,158,11,0.10)", layer="below"),
        dict(type="rect", x0=28, y0=108, x1=52, y1=114, line=dict(width=0.8, color="rgba(124,58,237,0.55)"), fillcolor="rgba(124,58,237,0.08)", layer="below"),
        dict(type="rect", x0=18, y0=102, x1=62, y1=108, line=dict(width=0.8, color="rgba(100,116,139,0.45)"), fillcolor="rgba(100,116,139,0.06)", layer="below"),
    ]

    pitch_shapes = [
        dict(type="rect", x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=PITCH_LENGTH, line=dict(width=2, color="#1e293b")),
        dict(type="line", x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=HALF_START, line=dict(width=2, color="#94a3b8")),
        dict(type="rect", x0=penalty_left, y0=102, x1=penalty_right, y1=120, line=dict(width=1.6, color="#1e293b")),
        dict(type="rect", x0=six_left, y0=114, x1=six_right, y1=120, line=dict(width=1.6, color="#1e293b")),
        dict(type="line", x0=36, y0=120, x1=44, y1=120, line=dict(width=3, color="#1e293b")),
    ]

    annotations = [
        dict(x=33.3, y=116.5, text="Near post", showarrow=False, font=dict(size=10, color="#1e3a8a")),
        dict(x=40.0, y=116.5, text="Central 6", showarrow=False, font=dict(size=10, color="#166534")),
        dict(x=46.7, y=116.5, text="Far post", showarrow=False, font=dict(size=10, color="#b45309")),
        dict(x=40.0, y=111.0, text="Penalty spot", showarrow=False, font=dict(size=10, color="#6d28d9")),
        dict(x=40.0, y=105.0, text="Edge box", showarrow=False, font=dict(size=10, color="#475569")),
    ]

    fig.update_layout(
        title=title,
        shapes=zone_shapes + pitch_shapes,
        annotations=annotations,
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        plot_bgcolor=pitch_color,
        paper_bgcolor=pitch_color,
        legend_title_text="",
    )
    return fig

def shotmap_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    shots = unique_shot_events(df)
    shots = shots[pd.to_numeric(shots["shot_x"], errors="coerce") >= HALF_START]

    if shots.empty:
        fig.add_annotation(text="No shots for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    shots["vx"], shots["vy"] = vertical_coords_from_statsbomb(shots["shot_x"], shots["shot_y"])
    shots["Result"] = np.where(shots["is_goal"], "Goal", "Shot")
    color_map = {"Shot": "#2563eb", "Goal": "#16a34a"}

    for result in ["Shot", "Goal"]:
        part = shots[shots["Result"] == result]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part["vx"],
                y=part["vy"],
                mode="markers",
                name=result,
                marker=dict(
                    size=np.clip(part["xg"].fillna(0) * 95 + 10, 10, 38),
                    color=color_map[result],
                    opacity=0.78,
                    line=dict(width=1, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Shooter"].fillna("Unknown"),
                        part["Shot outcome"].fillna("Unknown"),
                        part["xg"].fillna(0).round(3),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    return add_half_vertical_pitch_layout(fig, title)

def delivery_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    deliveries = df.copy()

    # Explicit SP_Type filtering for SWE SP pages.
    if "SP_Type" in deliveries.columns:
        sp_values = deliveries["SP_Type"].astype(str).str.strip()
        if sp_values.eq("From Free Kick").any() and not sp_values.eq("From Throw In").any():
            deliveries = deliveries[sp_values.eq("From Free Kick")]
        elif sp_values.eq("From Throw In").any() and not sp_values.eq("From Free Kick").any():
            deliveries = deliveries[sp_values.eq("From Throw In")]

    deliveries = deliveries[deliveries["delivery_end_x"].notna() & deliveries["delivery_end_y"].notna()].copy()

    # Corners use the dedicated half-pitch cutoff; SWE SP freekicks/throw-ins should show all deliveries.
    if "SP_Type" not in deliveries.columns:
        deliveries = deliveries[pd.to_numeric(deliveries["delivery_end_x"], errors="coerce") >= HALF_START]

    if deliveries.empty:
        fig.add_annotation(text="No deliveries with end locations for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    sample = deliveries.copy()
    if len(sample) > 250:
        sample = sample.sample(250, random_state=7)

    sample["vx_end"], sample["vy_end"] = vertical_coords_from_statsbomb(sample["delivery_end_x"], sample["delivery_end_y"])

    color_map = {
        "Inswinging": "#2563eb",
        "Outswinging": "#f59e0b",
        "Straight": "#7c3aed",
        "Unknown": "#94a3b8",
    }

    for tech, part in sample.groupby("Technique", dropna=False):
        color = color_map.get(str(tech), "#7c3aed")
        for _, row in part.iterrows():
            start_x, start_y = restart_origin_xy(row.get("side", "Left"))
            fig.add_trace(
                go.Scatter(
                    x=[start_x, row["vx_end"]],
                    y=[start_y, row["vy_end"]],
                    mode="lines",
                    line=dict(color=color, width=1.3),
                    opacity=0.28,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=part["vx_end"],
                y=part["vy_end"],
                mode="markers",
                name=str(tech),
                marker=dict(size=10, color=color, opacity=0.84, line=dict(width=0.8, color="white")),
                text=part["Delivery outcome"].fillna("Unknown"),
                textposition="top center",
                textfont=dict(size=9),
                customdata=np.stack(
                    [
                        part["Taker"].fillna("Unknown"),
                        part["Delivery height"].fillna("Unknown"),
                        part["Delivery outcome"].fillna("Unknown"),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Height: %{customdata[1]}<br>SP outcome: %{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[0, 80],
            y=[120, 120],
            mode="markers",
            name="Restart spot",
            marker=dict(size=11, color="#0f172a", symbol="circle-open", line=dict(width=2, color="#0f172a")),
            hoverinfo="skip",
        )
    )

    return add_half_vertical_pitch_layout(fig, title)


def starting_location_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    starts = df.copy()

    # Use pass start locations from SWE SP
    if "pass_x" not in starts.columns or "pass_y" not in starts.columns:
        if "location.pass" in starts.columns:
            pass_xy = starts["location.pass"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
            if pass_xy.shape[1] >= 2:
                starts["pass_x"] = pd.to_numeric(pass_xy[0].str.strip(), errors="coerce")
                starts["pass_y"] = pd.to_numeric(pass_xy[1].str.strip(), errors="coerce")

    starts = starts[starts["pass_x"].notna() & starts["pass_y"].notna()].copy()
    starts = unique_start_events(starts)

    if starts.empty:
        fig.add_annotation(text="No start locations for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    starts["vx"], starts["vy"] = vertical_coords_from_statsbomb(starts["pass_x"], starts["pass_y"])

    color_map = {
        "From Free Kick": "#2563eb",
        "From Throw In": "#f59e0b",
    }

    if "SP_Type" in starts.columns:
        groups = starts.groupby("SP_Type", dropna=False)
    else:
        starts["SP_Type"] = "Start location"
        groups = starts.groupby("SP_Type", dropna=False)

    for sp_type, part in groups:
        color = color_map.get(str(sp_type), "#7c3aed")
        fig.add_trace(
            go.Scatter(
                x=part["vx"],
                y=part["vy"],
                mode="markers",
                name=str(sp_type),
                marker=dict(
                    size=10,
                    color=color,
                    opacity=0.82,
                    line=dict(width=0.8, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Team"].fillna("Unknown") if "Team" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["Taker"].fillna("Unknown") if "Taker" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["Match"].fillna("Unknown") if "Match" in part.columns else pd.Series(["Unknown"] * len(part)),
                        part["minute"].fillna(0) if "minute" in part.columns else pd.Series([0] * len(part)),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Taker: %{customdata[1]}<br>%{customdata[2]}<br>Minute: %{customdata[3]}<extra></extra>",
            )
        )

    return add_half_vertical_pitch_layout(fig, title)


def build_summary_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Sequence-based summaries for SWE SP pages; corners still work because possession may be absent.
    if "possession" in df.columns:
        rows = []
        for team, part in df.groupby("Team", dropna=False):
            sequences = int(part["possession"].nunique())
            matches = int(part["match_id"].nunique()) if "match_id" in part.columns else (int(part["Match"].nunique()) if "Match" in part.columns else 0)

            shot_part = part[part["is_shot"]] if "is_shot" in part.columns else part.iloc[0:0]
            goal_part = part[part["is_goal"]] if "is_goal" in part.columns else part.iloc[0:0]

            shots = int(shot_part["possession"].nunique()) if not shot_part.empty else 0
            goals = int(goal_part["possession"].nunique()) if not goal_part.empty else 0

            if set(["possession", "shot_x", "shot_y", "xg"]).issubset(part.columns):
                xg_df = part[part["shot_x"].notna()][["possession", "shot_x", "shot_y", "xg"]].drop_duplicates()
                total_xg = float(xg_df["xg"].sum()) if not xg_df.empty else 0.0
                avg_xg = float(xg_df["xg"].mean()) if not xg_df.empty else 0.0
            else:
                total_xg = 0.0
                avg_xg = 0.0

            rows.append({
                "Team": team,
                "Matches": matches,
                "Set_Pieces": sequences,
                "Shots": shots,
                "Goals": goals,
                "Total_xG": total_xg,
                "Avg_xG": avg_xg,
            })

        summary = pd.DataFrame(rows).sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
    else:
        summary = (
            df.groupby("Team", dropna=False)
            .agg(
                Matches=("match_id", "nunique") if "match_id" in df.columns else ("Match", "nunique") if "Match" in df.columns else ("Team", "size"),
                Set_Pieces=("Team", "size"),
                Shots=("is_shot", "sum"),
                Goals=("is_goal", "sum"),
                Total_xG=("xg", "sum"),
                Avg_xG=("xg", "mean"),
            )
            .reset_index()
            .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
        )

    summary["Shot conversion %"] = np.where(summary["Shots"] > 0, (summary["Goals"] / summary["Shots"] * 100).round(1), 0)
    summary["Avg_xG"] = summary["Avg_xG"].fillna(0).round(3)
    summary["Total_xG"] = summary["Total_xG"].fillna(0).round(2)

    technique_mix = (
        df.groupby(["Technique", "Delivery height"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Technique", "Delivery height"]).issubset(df.columns) else pd.DataFrame()

    outcome_mix = (
        df.groupby(["Delivery outcome", "Shot outcome"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Delivery outcome", "Shot outcome"]).issubset(df.columns) else pd.DataFrame()

    return summary, technique_mix, outcome_mix


def _rate(numerator: float, denominator: float) -> float:
    return round((numerator / denominator * 100), 1) if denominator else 0.0


def set_piece_kpi_values(df: pd.DataFrame) -> dict[str, object]:
    if df.empty:
        return {
            "matches": 0,
            "restarts": 0,
            "shots": 0,
            "goals": 0,
            "total_xg": 0.0,
            "shot_rate": 0.0,
            "goal_conversion": 0.0,
            "xg_per_restart": 0.0,
            "xg_per_100": 0.0,
            "xg_per_shot": 0.0,
            "top_taker": "Unknown",
            "top_shooter": "Unknown",
            "top_delivery": "Unknown",
            "top_outcome": "Unknown",
        }

    starts = unique_start_events(df)
    shots_df = unique_shot_events(df)
    restarts = int(len(starts)) if not starts.empty else int(len(df))
    shots = int(len(shots_df))
    goals = int(shots_df["is_goal"].sum()) if "is_goal" in shots_df.columns and not shots_df.empty else 0
    total_xg = float(shots_df["xg"].fillna(0).sum()) if "xg" in shots_df.columns and not shots_df.empty else 0.0
    matches = int(df["match_id"].nunique()) if "match_id" in df.columns else int(df["Match"].nunique()) if "Match" in df.columns else 0

    def top_value(source: pd.DataFrame, column: str) -> str:
        if column not in source.columns or source.empty:
            return "Unknown"
        values = source[column].dropna().astype(str)
        values = values[values.str.strip().ne("") & values.str.lower().ne("unknown")]
        return values.value_counts().index[0] if not values.empty else "Unknown"

    return {
        "matches": matches,
        "restarts": restarts,
        "shots": shots,
        "goals": goals,
        "total_xg": total_xg,
        "shot_rate": _rate(shots, restarts),
        "goal_conversion": _rate(goals, shots),
        "xg_per_restart": round(total_xg / restarts, 3) if restarts else 0.0,
        "xg_per_100": round(total_xg / restarts * 100, 2) if restarts else 0.0,
        "xg_per_shot": round(total_xg / shots, 3) if shots else 0.0,
        "top_taker": top_value(starts, "Taker"),
        "top_shooter": top_value(shots_df, "Shooter"),
        "top_delivery": top_value(starts, "Delivery height"),
        "top_outcome": top_value(starts, "Delivery outcome"),
    }


def render_set_piece_kpi_deck(df: pd.DataFrame, label: str = "Set pieces") -> None:
    kpi = set_piece_kpi_values(df)
    cards = [
        ("Restarts", f"{kpi['restarts']:,}", f"{kpi['matches']:,} matches", False),
        ("Shot creation", f"{kpi['shot_rate']:.1f}%", f"{kpi['shots']:,} shots", True),
        ("xG / 100", f"{kpi['xg_per_100']:.2f}", "Threat per 100 restarts", False),
        ("xG / shot", f"{kpi['xg_per_shot']:.3f}", "Shot quality", True),
        ("Goals", f"{kpi['goals']:,}", f"{kpi['goal_conversion']:.1f}% conversion", False),
        ("Total xG", f"{kpi['total_xg']:.2f}", label, True),
    ]
    html = "<div class='mm-kpi-deck'>"
    for title, value, note, is_red in cards:
        cls = "mm-kpi-card is-red" if is_red else "mm-kpi-card"
        html += (
            f"<div class='{cls}'>"
            f"<div class='mm-kpi-label'>{escape(str(title))}</div>"
            f"<div class='mm-kpi-value'>{escape(str(value))}</div>"
            f"<div class='mm-kpi-help'>{escape(str(note))}</div>"
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    reads = [
        ("Primary taker", kpi["top_taker"]),
        ("Main delivery", kpi["top_delivery"]),
        ("Best shooter", kpi["top_shooter"]),
    ]
    read_html = "<div class='mm-read-strip'>"
    for title, value in reads:
        read_html += (
            "<div class='mm-read-card'>"
            f"<div class='mm-read-title'>{escape(str(title))}</div>"
            f"<div class='mm-read-value'>{escape(str(value))}</div>"
            "</div>"
        )
    read_html += "</div>"
    st.markdown(read_html, unsafe_allow_html=True)


def build_team_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for team, part in base.groupby("Team", dropna=False):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        matches = int(part["match_id"].nunique()) if "match_id" in part.columns else int(part["Match"].nunique()) if "Match" in part.columns else 0
        takers = int(part["Taker"].nunique()) if "Taker" in part.columns else 0
        rows.append(
            {
                "Team": team,
                "Matches": matches,
                "Events": events,
                "Takers": takers,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Goals / shot %": _rate(goals, shots),
                "Total xG": round(total_xg, 2),
                "xG / event": round(total_xg / events, 3) if events else 0,
                "xG / 100": round(total_xg / events * 100, 2) if events else 0,
                "xG / shot": round(total_xg / shots, 3) if shots else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["xG / 100", "Shot rate %", "Events"], ascending=False)


def build_taker_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    roles = build_role_archetypes(df)
    if roles.empty:
        return roles
    cols = [
        "Taker", "Team", "Role", "Archetype", "Events", "Shots", "Goals",
        "Shot rate", "xG / event", "xG / 100", "Top technique", "Top zone",
    ]
    return roles[[c for c in cols if c in roles.columns]]


def build_shooter_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()

    rows = []
    for shooter, part in shots.groupby("Shooter", dropna=False):
        attempts = int(len(part))
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        team = part["Team"].fillna("Unknown").mode().iloc[0] if "Team" in part.columns and not part["Team"].dropna().empty else "Unknown"
        rows.append(
            {
                "Shooter": shooter,
                "Team": team,
                "Shots": attempts,
                "Goals": goals,
                "Total xG": round(total_xg, 2),
                "xG / shot": round(total_xg / attempts, 3) if attempts else 0,
                "Conversion %": _rate(goals, attempts),
            }
        )
    return pd.DataFrame(rows).sort_values(["Total xG", "Shots", "Goals"], ascending=False)


def build_pattern_library(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    group_cols = [c for c in ["Team", "side", "Technique", "Delivery height", "Delivery zone", "Delivery outcome"] if c in base.columns]
    if not group_cols:
        return pd.DataFrame()

    rows = []
    for keys, part in base.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        record.update(
            {
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Total xG": round(xg, 2),
                "xG / event": round(xg / events, 3) if events else 0,
                "xG / 100": round(xg / events * 100, 2) if events else 0,
                "xG / shot": round(xg / shots, 3) if shots else 0,
            }
        )
        rows.append(record)

    return (
        pd.DataFrame(rows)
        .sort_values(["Events", "xG / event", "Shot rate %"], ascending=False)
        .head(40)
    )


def build_match_log(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    group_cols = [c for c in ["Match", "Team"] if c in base.columns]
    if not group_cols:
        return pd.DataFrame()

    rows = []
    for keys, part in base.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        record.update(
            {
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate %": _rate(shots, events),
                "Total xG": round(xg, 2),
            }
        )
        rows.append(record)

    return pd.DataFrame(rows).sort_values(["Match", "Total xG"], ascending=[True, False])


def render_analyst_table(df: pd.DataFrame, *, height: int = 360, max_rows: int = 2500) -> None:
    if df.empty:
        st.info("No rows available for this view.")
        return
    display_df = df
    if len(df) > max_rows:
        display_df = df.head(max_rows)
        st.caption(f"Showing the first {max_rows:,} of {len(df):,} rows for faster rendering. Use exports for the full table.")
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=height,
    )


def freekick_zone(x: object, y: object) -> str:
    px = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    py = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pd.isna(px) or pd.isna(py):
        return "Unknown"
    if px >= 96 and 24 <= py <= 56:
        return "Direct threat"
    if px >= 82 and (py < 24 or py > 56):
        return "Wide delivery"
    if px >= 82:
        return "Advanced central"
    if px >= 60:
        return "Middle third"
    return "Deep restart"


def freekick_channel(y: object) -> str:
    py = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pd.isna(py):
        return "Unknown"
    if py < 18:
        return "Left wide"
    if py < 32:
        return "Left half-space"
    if py <= 48:
        return "Central"
    if py <= 62:
        return "Right half-space"
    return "Right wide"


def freekick_sequence_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()
    if "pass_x" not in base.columns or "pass_y" not in base.columns:
        return pd.DataFrame()

    group_cols = [c for c in ["match_id", "possession", "Team"] if c in base.columns]
    if len(group_cols) < 2:
        return pd.DataFrame()

    rows = []
    for keys, part in base.sort_values(["minute", "second"] if {"minute", "second"}.issubset(base.columns) else group_cols).groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        first = part.iloc[0]
        shots = unique_shot_events(part)
        total_xg = float(shots["xg"].fillna(0).sum()) if "xg" in shots.columns and not shots.empty else 0.0
        goals = int(shots["is_goal"].sum()) if "is_goal" in shots.columns and not shots.empty else 0
        record.update(
            {
                "Match": first.get("Match", record.get("match_id", "Unknown")),
                "Minute": int(first.get("minute", 0)) if pd.notna(first.get("minute", np.nan)) else 0,
                "Origin x": round(float(first.get("pass_x", np.nan)), 1) if pd.notna(first.get("pass_x", np.nan)) else np.nan,
                "Origin y": round(float(first.get("pass_y", np.nan)), 1) if pd.notna(first.get("pass_y", np.nan)) else np.nan,
                "Zone": freekick_zone(first.get("pass_x", np.nan), first.get("pass_y", np.nan)),
                "Channel": freekick_channel(first.get("pass_y", np.nan)),
                "Initial taker": first.get("Taker", "Unknown"),
                "Initial height": first.get("Delivery height", "Unknown"),
                "Actions": int(len(part)),
                "Shots": int(len(shots)),
                "Goals": goals,
                "Total xG": round(total_xg, 3),
                "Best shooter": shots.sort_values("xg", ascending=False).iloc[0].get("Shooter", "Unknown") if not shots.empty and "xg" in shots.columns else "Unknown",
                "Best shot xG": round(float(shots["xg"].max()), 3) if not shots.empty and "xg" in shots.columns else 0.0,
                "Shot outcome": shots.iloc[0].get("Shot outcome", "No shot") if not shots.empty else "No shot",
            }
        )
        rows.append(record)

    return pd.DataFrame(rows).sort_values(["Total xG", "Shots", "Minute"], ascending=[False, False, True])


def freekick_zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = freekick_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby(["Zone", "Channel"], dropna=False)
        .agg(
            Sequences=("Zone", "size"),
            Shots=("Shots", "sum"),
            Shot_Sequences=("Shots", lambda s: int((s > 0).sum())),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Avg_Actions=("Actions", "mean"),
        )
        .reset_index()
    )
    summary["Shot sequence %"] = summary.apply(lambda r: _rate(r["Shot_Sequences"], r["Sequences"]), axis=1)
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary["Avg_Actions"] = summary["Avg_Actions"].round(1)
    summary = summary.sort_values(["Total_xG", "Shots / seq", "Sequences"], ascending=False)
    return summary.drop(columns=[c for c in ["Shot_Sequences", "Shot sequence %"] if c in summary.columns])


def freekick_taker_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = freekick_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby("Initial taker", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Sequences=("Initial taker", "size"),
            Shots=("Shots", "sum"),
            Shot_Sequences=("Shots", lambda s: int((s > 0).sum())),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Main_zone=("Zone", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_channel=("Channel", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_height=("Initial height", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
        )
        .reset_index()
        .rename(columns={"Initial taker": "Taker"})
    )
    summary["Shot sequence %"] = summary.apply(lambda r: _rate(r["Shot_Sequences"], r["Sequences"]), axis=1)
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary = summary.sort_values(["Total_xG", "Sequences", "Avg_xG"], ascending=False)
    return summary.drop(columns=[c for c in ["Shot_Sequences", "Shot sequence %"] if c in summary.columns])


def freekick_shooter_summary(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()
    summary = (
        shots.groupby("Shooter", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Shots=("Shooter", "size"),
            Goals=("is_goal", "sum") if "is_goal" in shots.columns else ("Shooter", "size"),
            Total_xG=("xg", "sum") if "xg" in shots.columns else ("Shooter", "size"),
            Avg_xG=("xg", "mean") if "xg" in shots.columns else ("Shooter", "size"),
            Best_xG=("xg", "max") if "xg" in shots.columns else ("Shooter", "size"),
        )
        .reset_index()
    )
    summary["Conversion %"] = summary.apply(lambda r: _rate(r["Goals"], r["Shots"]), axis=1)
    for col in ["Total_xG", "Avg_xG", "Best_xG"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).round(3)
    return summary.sort_values(["Total_xG", "Shots", "Goals"], ascending=False)


def freekick_origin_map_figure(df: pd.DataFrame, title: str = "Freekick origins") -> go.Figure:
    fig = go.Figure()
    seq = freekick_sequence_summary(df)
    if seq.empty:
        fig.add_annotation(text="No freekick origins available", x=60, y=40, showarrow=False, font=dict(size=16, color=MUTED))
        return fig

    colors = {
        "Direct threat": RED,
        "Wide delivery": "#1d4ed8",
        "Advanced central": "#15803d",
        "Middle third": "#b45309",
        "Deep restart": "#64748b",
        "Unknown": "#94a3b8",
    }
    for zone, part in seq.groupby("Zone", dropna=False):
        fig.add_trace(
            go.Scatter(
                x=part["Origin x"],
                y=part["Origin y"],
                mode="markers",
                name=str(zone),
                marker=dict(
                    size=np.clip(part["Total xG"].fillna(0) * 180 + 8, 8, 38),
                    color=colors.get(str(zone), "#64748b"),
                    opacity=0.78,
                    line=dict(width=0.8, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Team"].fillna("Unknown"),
                        part["Initial taker"].fillna("Unknown"),
                        part["Total xG"].fillna(0).round(3),
                        part["Shot outcome"].fillna("Unknown"),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Taker: %{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<br>%{customdata[4]}<extra></extra>",
            )
        )

    fig.update_xaxes(range=[0, 120], visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(range=[0, 80], visible=False)
    fig.update_layout(
        title=title,
        height=560,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        shapes=[
            dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color=BLACK, width=1.4)),
            dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="#94a3b8", width=1)),
            dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color=BLACK, width=1.2)),
            dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color=BLACK, width=1.2)),
            dict(type="circle", x0=108, y0=34, x1=112, y1=46, line=dict(color="#94a3b8", width=1)),
        ],
        legend_title_text="Origin zone",
    )
    return fig


def throwin_zone(x: object) -> str:
    px = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    if pd.isna(px):
        return "Unknown"
    if px >= 102:
        return "Final-third pressure"
    if px >= 84:
        return "Attacking channel"
    if px >= 60:
        return "Middle-third platform"
    if px >= 36:
        return "Build-up restart"
    return "Defensive throw"


def throwin_side(y: object) -> str:
    py = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pd.isna(py):
        return "Unknown"
    return "Left touchline" if py <= 40 else "Right touchline"


def throwin_sequence_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()
    if "pass_x" not in base.columns or "pass_y" not in base.columns:
        return pd.DataFrame()

    group_cols = [c for c in ["match_id", "possession", "Team"] if c in base.columns]
    if len(group_cols) < 2:
        return pd.DataFrame()

    sort_cols = ["minute", "second"] if {"minute", "second"}.issubset(base.columns) else group_cols
    rows = []
    for keys, part in base.sort_values(sort_cols).groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(group_cols, keys))
        first = part.iloc[0]
        shots = unique_shot_events(part)
        total_xg = float(shots["xg"].fillna(0).sum()) if "xg" in shots.columns and not shots.empty else 0.0
        goals = int(shots["is_goal"].sum()) if "is_goal" in shots.columns and not shots.empty else 0
        best = shots.sort_values("xg", ascending=False).iloc[0] if not shots.empty and "xg" in shots.columns else None
        initial_height = first.get("Delivery height", "Unknown")
        origin_x = first.get("pass_x", np.nan)
        origin_y = first.get("pass_y", np.nan)
        zone = throwin_zone(origin_x)
        side = throwin_side(origin_y)
        if zone == "Final-third pressure" and str(initial_height).lower().startswith("high"):
            profile = "Long throw threat"
        elif zone in ["Final-third pressure", "Attacking channel"]:
            profile = "High press restart"
        elif str(initial_height).lower().startswith("ground"):
            profile = "Retain and combine"
        else:
            profile = "Territory reset"

        record.update(
            {
                "Match": first.get("Match", record.get("match_id", "Unknown")),
                "Minute": int(first.get("minute", 0)) if pd.notna(first.get("minute", np.nan)) else 0,
                "Origin x": round(float(origin_x), 1) if pd.notna(origin_x) else np.nan,
                "Origin y": round(float(origin_y), 1) if pd.notna(origin_y) else np.nan,
                "Zone": zone,
                "Side": side,
                "Profile": profile,
                "Initial taker": first.get("Taker", "Unknown"),
                "Initial height": initial_height,
                "Actions": int(len(part)),
                "Shots": int(len(shots)),
                "Goals": goals,
                "Total xG": round(total_xg, 3),
                "Best shooter": best.get("Shooter", "Unknown") if best is not None else "Unknown",
                "Best shot xG": round(float(best.get("xg", 0)), 3) if best is not None else 0.0,
                "Shot outcome": best.get("Shot outcome", "No shot") if best is not None else "No shot",
            }
        )
        rows.append(record)

    return pd.DataFrame(rows).sort_values(["Total xG", "Shots", "Minute"], ascending=[False, False, True])


def throwin_zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = throwin_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby(["Zone", "Side", "Profile"], dropna=False)
        .agg(
            Sequences=("Zone", "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Avg_Actions=("Actions", "mean"),
        )
        .reset_index()
    )
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    summary["Avg_Actions"] = summary["Avg_Actions"].round(1)
    return summary.sort_values(["Total_xG", "Shots / seq", "Sequences"], ascending=False)


def throwin_taker_summary(df: pd.DataFrame) -> pd.DataFrame:
    seq = throwin_sequence_summary(df)
    if seq.empty:
        return pd.DataFrame()
    summary = (
        seq.groupby("Initial taker", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Sequences=("Initial taker", "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
            Main_zone=("Zone", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_side=("Side", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_profile=("Profile", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Main_height=("Initial height", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
        )
        .reset_index()
        .rename(columns={"Initial taker": "Taker"})
    )
    summary["Shots / seq"] = (summary["Shots"] / summary["Sequences"]).replace([np.inf, -np.inf], 0).fillna(0).round(2)
    summary["Total_xG"] = summary["Total_xG"].round(2)
    summary["Avg_xG"] = summary["Avg_xG"].round(3)
    return summary.sort_values(["Total_xG", "Sequences", "Avg_xG"], ascending=False)


def throwin_shooter_summary(df: pd.DataFrame) -> pd.DataFrame:
    shots = unique_shot_events(df)
    if shots.empty or "Shooter" not in shots.columns:
        return pd.DataFrame()
    summary = (
        shots.groupby("Shooter", dropna=False)
        .agg(
            Team=("Team", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            Shots=("Shooter", "size"),
            Goals=("is_goal", "sum") if "is_goal" in shots.columns else ("Shooter", "size"),
            Total_xG=("xg", "sum") if "xg" in shots.columns else ("Shooter", "size"),
            Avg_xG=("xg", "mean") if "xg" in shots.columns else ("Shooter", "size"),
            Best_xG=("xg", "max") if "xg" in shots.columns else ("Shooter", "size"),
        )
        .reset_index()
    )
    summary["Conversion %"] = summary.apply(lambda r: _rate(r["Goals"], r["Shots"]), axis=1)
    for col in ["Total_xG", "Avg_xG", "Best_xG"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).round(3)
    return summary.sort_values(["Total_xG", "Shots", "Goals"], ascending=False)


def throwin_origin_map_figure(df: pd.DataFrame, title: str = "Throw-in origins") -> go.Figure:
    fig = go.Figure()
    seq = throwin_sequence_summary(df)
    if seq.empty:
        fig.add_annotation(text="No throw-in origins available", x=60, y=40, showarrow=False, font=dict(size=16, color=MUTED))
        return fig

    colors = {
        "Final-third pressure": RED,
        "Attacking channel": "#1d4ed8",
        "Middle-third platform": "#15803d",
        "Build-up restart": "#b45309",
        "Defensive throw": "#64748b",
        "Unknown": "#94a3b8",
    }
    for zone, part in seq.groupby("Zone", dropna=False):
        fig.add_trace(
            go.Scatter(
                x=part["Origin x"],
                y=part["Origin y"],
                mode="markers",
                name=str(zone),
                marker=dict(
                    size=np.clip(part["Total xG"].fillna(0) * 180 + 8, 8, 40),
                    color=colors.get(str(zone), "#64748b"),
                    opacity=0.78,
                    line=dict(width=0.8, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Team"].fillna("Unknown"),
                        part["Initial taker"].fillna("Unknown"),
                        part["Profile"].fillna("Unknown"),
                        part["Total xG"].fillna(0).round(3),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>Taker: %{customdata[1]}<br>%{customdata[2]}<br>xG: %{customdata[3]}<br>%{customdata[4]}<extra></extra>",
            )
        )

    fig.update_xaxes(range=[0, 120], visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(range=[0, 80], visible=False)
    fig.update_layout(
        title=title,
        height=560,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        shapes=[
            dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color=BLACK, width=1.4)),
            dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="#94a3b8", width=1)),
            dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color=BLACK, width=1.2)),
            dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color=BLACK, width=1.2)),
        ],
        legend_title_text="Origin zone",
    )
    return fig

def kpi_row(df: pd.DataFrame) -> None:
    render_set_piece_kpi_deck(df)

def info_panel(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No rows match the current filters.")
        return
    notes = []
    base = unique_start_events(df)
    if "Technique" in base.columns:
        vc = base["Technique"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top technique: {vc.index[0]} ({int(vc.iloc[0])})")
    if "Taker" in base.columns:
        vc = base["Taker"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top taker: {vc.index[0]} ({int(vc.iloc[0])})")
    if notes:
        st.caption(" · ".join(notes))


def delivery_zone_label(x: object, y: object) -> str:
    end_x = pd.to_numeric(pd.Series([x]), errors="coerce").iloc[0]
    end_y = pd.to_numeric(pd.Series([y]), errors="coerce").iloc[0]
    if pd.isna(end_x) or pd.isna(end_y):
        return "Unknown"
    if end_x >= 114 and 30 <= end_y <= 50:
        return "Six-yard corridor"
    if end_x >= 114:
        return "Near/far post lane"
    if end_x >= 108 and 28 <= end_y <= 52:
        return "Penalty spot"
    if end_x >= 102 and 18 <= end_y <= 62:
        return "Edge of box"
    if end_x < 90:
        return "Short / recycle"
    return "Second ball zone"


def add_delivery_zones(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    if {"delivery_end_x", "delivery_end_y"}.issubset(enriched.columns):
        enriched["Delivery zone"] = [
            delivery_zone_label(x, y)
            for x, y in zip(enriched["delivery_end_x"], enriched["delivery_end_y"])
        ]
    elif "Delivery zone" not in enriched.columns:
        enriched["Delivery zone"] = "Unknown"
    return enriched


def build_role_archetypes(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    if df.empty or "Taker" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for taker, part in base.groupby("Taker", dropna=False):
        taker_name = str(taker) if str(taker).strip() else "Unknown"
        events = int(len(part))
        if events == 0:
            continue
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        shot_rate = shots / events if events else 0.0
        xg_per_event = total_xg / events if events else 0.0

        top_technique = part["Technique"].fillna("Unknown").mode().iloc[0] if "Technique" in part.columns and not part["Technique"].dropna().empty else "Unknown"
        top_height = part["Delivery height"].fillna("Unknown").mode().iloc[0] if "Delivery height" in part.columns and not part["Delivery height"].dropna().empty else "Unknown"
        top_zone = part["Delivery zone"].fillna("Unknown").mode().iloc[0] if "Delivery zone" in part.columns and not part["Delivery zone"].dropna().empty else "Unknown"
        team = part["Team"].fillna("Unknown").mode().iloc[0] if "Team" in part.columns and not part["Team"].dropna().empty else "Unknown"

        if events >= max(8, base.groupby("Taker").size().quantile(0.75)):
            role = "Primary taker"
        elif shot_rate >= 0.35 or xg_per_event >= 0.04:
            role = "Chance creator"
        elif top_zone == "Short / recycle":
            role = "Short option"
        else:
            role = "Rotation taker"

        technique_l = str(top_technique).lower()
        if "inswing" in technique_l:
            archetype = f"Inswing {top_zone.lower()}"
        elif "outswing" in technique_l:
            archetype = f"Outswing {top_zone.lower()}"
        elif top_zone == "Short / recycle":
            archetype = "Short-play connector"
        elif label == "Freekicks":
            archetype = f"Dead-ball {top_height.lower()}"
        else:
            archetype = f"Mixed {top_zone.lower()}"

        rows.append(
            {
                "Taker": taker_name,
                "Team": team,
                "Role": role,
                "Archetype": archetype,
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate": round(shot_rate * 100, 1),
                "xG / event": round(xg_per_event, 3),
                "xG / 100": round(xg_per_event * 100, 2),
                "Top technique": top_technique,
                "Top zone": top_zone,
            }
        )

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["xG / 100", "Shot rate", "Events"], ascending=False)


def build_team_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()

    base = add_delivery_zones(unique_start_events(df))
    rows = []
    for team, part in base.groupby("Team", dropna=False):
        events = int(len(part))
        if events == 0:
            continue
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        zone = part["Delivery zone"].fillna("Unknown").mode().iloc[0] if "Delivery zone" in part.columns and not part["Delivery zone"].dropna().empty else "Unknown"
        height = part["Delivery height"].fillna("Unknown").mode().iloc[0] if "Delivery height" in part.columns and not part["Delivery height"].dropna().empty else "Unknown"
        technique = part["Technique"].fillna("Unknown").mode().iloc[0] if "Technique" in part.columns and not part["Technique"].dropna().empty else "Unknown"

        if shots / events >= 0.35:
            profile = "Direct shot hunters"
        elif zone == "Short / recycle":
            profile = "Short and second-phase"
        elif "High" in str(height):
            profile = "Aerial box load"
        else:
            profile = "Mixed delivery side"

        rows.append(
            {
                "Team": team,
                "Archetype": profile,
                "Events": events,
                "Shots": shots,
                "Goals": goals,
                "Shot rate": round(shots / events * 100, 1),
                "xG / event": round(total_xg / events, 3),
                "Primary delivery": f"{technique} · {zone}",
            }
        )
    return pd.DataFrame(rows).sort_values(["xG / event", "Shot rate", "Events"], ascending=False)


def generate_set_piece_insights(df: pd.DataFrame, label: str = "") -> list[str]:
    if df.empty:
        return ["No rows match the current filter, so the report cannot generate a reliable read."]

    base = add_delivery_zones(unique_start_events(df))
    insights: list[str] = []
    events = len(base)
    shots = int(base["is_shot"].sum()) if "is_shot" in base.columns else 0
    goals = int(base["is_goal"].sum()) if "is_goal" in base.columns else 0
    total_xg = float(base["xg"].fillna(0).sum()) if "xg" in base.columns else 0.0
    shot_rate = shots / events * 100 if events else 0
    insights.append(f"{label or 'Set pieces'} produced {shots} shots from {events} events ({shot_rate:.1f}% shot rate), worth {total_xg:.2f} xG and {goals} goals.")

    roles = build_role_archetypes(base, label)
    if not roles.empty:
        lead = roles.iloc[0]
        insights.append(f"Main taker profile: {lead['Taker']} is a {str(lead['Role']).lower()} for {lead['Team']}, most often showing as {lead['Archetype']}.")
        creator = roles.sort_values(["xG / event", "Shot rate", "Events"], ascending=False).iloc[0]
        insights.append(f"Best creation signal: {creator['Taker']} leads the filtered takers on xG/event ({creator['xG / event']:.3f}) with a {creator['Shot rate']:.1f}% shot rate.")

    teams = build_team_archetypes(base)
    if not teams.empty:
        top_team = teams.iloc[0]
        insights.append(f"Team archetype to prepare for: {top_team['Team']} profile as {str(top_team['Archetype']).lower()}, built around {top_team['Primary delivery']}.")

    if "Delivery zone" in base.columns:
        zone_counts = base["Delivery zone"].value_counts()
        if not zone_counts.empty:
            zone = zone_counts.index[0]
            share = zone_counts.iloc[0] / len(base) * 100
            insights.append(f"Dominant target area is {zone.lower()} ({share:.1f}% of deliveries with a classified end zone).")

    if "side" in base.columns:
        side_counts = base["side"].value_counts()
        if len(side_counts) > 0:
            insights.append(f"Restart side bias: {side_counts.index[0]} side accounts for {side_counts.iloc[0] / len(base) * 100:.1f}% of the sample.")

    return insights[:6]


def mplsoccer_delivery_figure(df: pd.DataFrame, label: str = ""):
    import matplotlib.pyplot as plt
    from mplsoccer import Pitch

    base = add_delivery_zones(unique_start_events(df))
    fig, ax = plt.subplots(figsize=(8, 5.8), dpi=140)
    pitch = Pitch(pitch_type="statsbomb", half=True, pitch_color="#fbfdff", line_color=BLACK, linewidth=1.2)
    pitch.draw(ax=ax)
    ax.set_title(f"{label} delivery map", fontsize=14, fontweight="bold", color=BLACK, pad=10)

    if base.empty or not {"delivery_end_x", "delivery_end_y"}.issubset(base.columns):
        ax.text(90, 40, "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    plot_df = base.dropna(subset=["delivery_end_x", "delivery_end_y"]).copy()
    if plot_df.empty:
        ax.text(90, 40, "No delivery end locations", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    if len(plot_df) > 320:
        plot_df = plot_df.sample(320, random_state=11)

    colors = {
        "Six-yard corridor": RED,
        "Near/far post lane": "#2563eb",
        "Penalty spot": "#16a34a",
        "Edge of box": "#f59e0b",
        "Short / recycle": "#7c3aed",
        "Second ball zone": "#64748b",
        "Unknown": "#94a3b8",
    }

    for zone, part in plot_df.groupby("Delivery zone", dropna=False):
        color = colors.get(str(zone), "#64748b")
        pitch.scatter(
            part["delivery_end_x"],
            part["delivery_end_y"],
            s=np.clip(part["xg"].fillna(0).to_numpy() * 550 + 28 if "xg" in part.columns else 36, 28, 120),
            color=color,
            edgecolors="white",
            linewidth=0.7,
            alpha=0.82,
            label=str(zone),
            ax=ax,
        )

    ax.legend(loc="lower left", bbox_to_anchor=(0.01, 0.01), fontsize=7, frameon=True)
    fig.tight_layout()
    return fig


def mplsoccer_shot_figure(df: pd.DataFrame, label: str = ""):
    import matplotlib.pyplot as plt
    from mplsoccer import Pitch

    shots = unique_shot_events(df)
    fig, ax = plt.subplots(figsize=(8, 5.8), dpi=140)
    pitch = Pitch(pitch_type="statsbomb", half=True, pitch_color="#fbfdff", line_color=BLACK, linewidth=1.2)
    pitch.draw(ax=ax)
    ax.set_title(f"{label} shot quality", fontsize=14, fontweight="bold", color=BLACK, pad=10)

    if shots.empty or not {"shot_x", "shot_y"}.issubset(shots.columns):
        ax.text(90, 40, "No shots in current filter", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    shots = shots.dropna(subset=["shot_x", "shot_y"]).copy()
    shots = shots[pd.to_numeric(shots["shot_x"], errors="coerce") >= HALF_START]
    if shots.empty:
        ax.text(90, 40, "No shots in current filter", ha="center", va="center", color=MUTED, fontsize=12)
        return fig

    goals = shots["is_goal"] if "is_goal" in shots.columns else pd.Series(False, index=shots.index)
    sizes = np.clip(shots["xg"].fillna(0).to_numpy() * 700 + 34 if "xg" in shots.columns else 42, 34, 145)
    pitch.scatter(shots.loc[~goals, "shot_x"], shots.loc[~goals, "shot_y"], s=sizes[~goals], color="#2563eb", edgecolors="white", linewidth=0.8, alpha=0.78, label="Shot", ax=ax)
    if goals.any():
        pitch.scatter(shots.loc[goals, "shot_x"], shots.loc[goals, "shot_y"], s=sizes[goals], color="#16a34a", edgecolors=BLACK, linewidth=0.8, alpha=0.92, label="Goal", ax=ax)
    ax.legend(loc="lower left", bbox_to_anchor=(0.01, 0.01), fontsize=8, frameon=True)
    fig.tight_layout()
    return fig


def prematch_report_pdf_bytes(df: pd.DataFrame, label: str = "", opponent: str = "") -> bytes:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    buffer = BytesIO()
    insights = generate_set_piece_insights(df, label)
    roles = build_role_archetypes(df, label).head(8)
    teams = build_team_archetypes(df).head(8)

    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        title = f"{label} pre-match report"
        if opponent:
            title = f"{title}: {opponent}"
        ax.text(0.07, 0.94, title, fontsize=22, fontweight="bold", color=BLACK)
        ax.text(0.07, 0.905, "Roles, archetypes, delivery tendencies, and preparation notes", fontsize=10, color=MUTED)

        y = 0.84
        ax.text(0.07, y, "Key insights", fontsize=13, fontweight="bold", color=RED_DARK)
        y -= 0.035
        for insight in insights:
            wrapped = textwrap.wrap(insight, width=92)
            for i, line in enumerate(wrapped):
                prefix = "- " if i == 0 else "  "
                ax.text(0.08, y, prefix + line, fontsize=9.4, color=INK)
                y -= 0.022
            y -= 0.006

        if not roles.empty:
            y -= 0.02
            ax.text(0.07, y, "Taker roles", fontsize=13, fontweight="bold", color=RED_DARK)
            y -= 0.035
            for _, row in roles.iterrows():
                line = f"{row['Taker']} ({row['Team']}): {row['Role']} · {row['Archetype']} · {row['Events']} events · {row['xG / event']:.3f} xG/event"
                ax.text(0.08, y, line[:118], fontsize=8.8, color=INK)
                y -= 0.024

        if not teams.empty and y > 0.18:
            y -= 0.02
            ax.text(0.07, y, "Team archetypes", fontsize=13, fontweight="bold", color=RED_DARK)
            y -= 0.035
            for _, row in teams.iterrows():
                line = f"{row['Team']}: {row['Archetype']} · {row['Primary delivery']} · {row['Shot rate']:.1f}% shot rate"
                ax.text(0.08, y, line[:118], fontsize=8.8, color=INK)
                y -= 0.024
                if y < 0.08:
                    break
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = mplsoccer_delivery_figure(df, label)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = mplsoccer_shot_figure(df, label)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    buffer.seek(0)
    return buffer.getvalue()
