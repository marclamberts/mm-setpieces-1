
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Michael Mackin Set Piece",
    page_icon="⚽",
    layout="wide",
)

st.markdown(
    '''
    <style>
        .stApp {background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);}
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        .hero-card {
            background: rgba(255,255,255,0.98);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 28px;
            padding: 2rem 2rem 1.8rem 2rem;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.1rem;
        }
        .eyebrow {font-size: .82rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: #64748b;}
        .hero-title {font-size: 2.7rem; font-weight: 900; color: #0f172a; margin-top: .35rem; margin-bottom: .5rem;}
        .hero-copy {font-size: 1rem; color: #475569; max-width: 850px; line-height: 1.7;}
        .nav-card {
            background: rgba(255,255,255,0.98);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 24px;
            padding: 1.3rem 1.2rem 1.15rem 1.2rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
            min-height: 210px;
        }
        .nav-title {font-size: 1.2rem; font-weight: 800; color: #0f172a; margin-bottom: .3rem;}
        .nav-copy {color: #64748b; line-height: 1.6; margin-bottom: 1rem;}
        .tiny {font-size: .85rem; color: #94a3b8;}
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            border: 1px solid #cbd5e1;
            background: white;
            color: #0f172a;
            font-weight: 700;
            padding: .7rem 1rem;
        }
    </style>
    ''',
    unsafe_allow_html=True,
)

st.markdown(
    '''
    <div class="hero-card">
        <div class="eyebrow">Michael Mackin · Set Piece Analysis</div>
        <div class="hero-title">Professional set-piece dashboard</div>
        <div class="hero-copy">
            Explore corners, freekicks, and throw-ins with delivery maps, shot maps, match filters,
            player filters, and event-level detail. The dashboard is built for fast opposition review
            and set-piece pattern analysis in a clean light-theme environment.
        </div>
    </div>
    ''',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        '''
        <div class="nav-card">
            <div class="nav-title">Corners</div>
            <div class="nav-copy">Half-pitch vertical shot map and delivery map using StatsBomb 120×80 coordinates, with richer filter controls.</div>
            <div class="tiny">Attacking-half view · Team, side, taker, technique, minute, outcomes</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    if st.button("Open Corners"):
        st.switch_page("pages/1_Corners.py")

with c2:
    st.markdown(
        '''
        <div class="nav-card">
            <div class="nav-title">Freekicks</div>
            <div class="nav-copy">Shared page framework ready for freekick datasets, including summary tables and plotting components.</div>
            <div class="tiny">Generic template · Plug in data when ready</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    if st.button("Open Freekicks"):
        st.switch_page("pages/2_Freekicks.py")

with c3:
    st.markdown(
        '''
        <div class="nav-card">
            <div class="nav-title">Throw ins</div>
            <div class="nav-copy">Shared page framework ready for throw-in workflows, with filters, KPIs, and event table layout.</div>
            <div class="tiny">Generic template · Plug in data when ready</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    if st.button("Open Throw ins"):
        st.switch_page("pages/3_Throw_ins.py")

st.caption("Corners are wired to the bundled Allsvenskan 2025 corners workbook. Freekicks and Throw ins pages remain template-ready until their datasets are added.")
