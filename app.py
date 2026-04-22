from __future__ import annotations

import streamlit as st

from utils import hero_block, inject_app_style, section_header

st.set_page_config(page_title="Michael Mackin Set Piece", page_icon="⚽", layout="wide")
inject_app_style()

hero_block(
    "Michael Mackin · Set-Piece Intelligence",
    "Match-prep analysis workspace",
    "A focused analyst tool for corners, free kicks, throw-ins, duel profiles, timing audits, and report-ready tactical evidence.",
)

st.markdown(
    """
    <div class="mm-feature-strip">
        <div class="mm-feature-pill">
            <div class="mm-feature-value">5 workbooks</div>
            <div class="mm-feature-label">Connected data</div>
        </div>
        <div class="mm-feature-pill">
            <div class="mm-feature-value">Roles + archetypes</div>
            <div class="mm-feature-label">Player profiling</div>
        </div>
        <div class="mm-feature-pill">
            <div class="mm-feature-value">mplsoccer maps</div>
            <div class="mm-feature-label">Report visuals</div>
        </div>
        <div class="mm-feature-pill">
            <div class="mm-feature-value">PDF reports</div>
            <div class="mm-feature-label">Pre-match output</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_header("Core Workbooks", "Primary event analysis")
cards = [
    (
        "Corners",
        "Delivery + shot value",
        "Corner output by team, taker, target zone, shot map, sequence value, and pre-match report export.",
        "Allsvenskan - Corners 2025.xlsx",
        "pages/1_Corners.py",
        "Open Corners",
    ),
    (
        "Freekicks",
        "Origin + taker profiles",
        "Specialist free-kick view with origin zones, taker rankings, shooter value, and possession-level outcomes.",
        "SWE SP.xlsx · From Free Kick",
        "pages/2_Freekicks.py",
        "Open Freekicks",
    ),
    (
        "Throw ins",
        "Touchline pressure",
        "Throw-in territory, side bias, pressure profile, thrower output, and shot creation from possession sequences.",
        "SWE SP.xlsx · From Throw In",
        "pages/3_Throw_ins.py",
        "Open Throw ins",
    ),
]

for col, (title, kicker, copy, source, page, button) in zip(st.columns(3), cards):
    with col:
        st.markdown(
            f"""
            <div class="mm-nav-card">
                <div class="mm-card-kicker">{kicker}</div>
                <div class="mm-nav-title">{title}</div>
                <div class="mm-nav-copy">{copy}</div>
                <div class="mm-tiny">{source}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(button):
            st.switch_page(page)

section_header("Specialist Analysis", "Player rating model and timing audit")
s1, s2 = st.columns(2)

with s1:
    st.markdown(
        """
        <div class="mm-nav-card">
            <div class="mm-card-kicker">Duel model</div>
            <div class="mm-nav-title">HOPS</div>
            <div class="mm-nav-copy">Duel strength by player and team, with percentiles, tiers, elite profiles, and risk checks.</div>
            <div class="mm-tiny">duel_hops_rating_summary.xlsx</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open HOPS"):
        st.switch_page("pages/4_HOPS.py")

with s2:
    st.markdown(
        """
        <div class="mm-nav-card">
            <div class="mm-card-kicker">Timing model</div>
            <div class="mm-nav-title">Delay Analysis</div>
            <div class="mm-nav-copy">Corner timing audit with delay bands, exit events, slowest match profiles, and extraction diagnostics.</div>
            <div class="mm-tiny">corner_delays (1).xlsx</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Delay Analysis"):
        st.switch_page("pages/5_Delay.py")

st.caption("Data routing: Corners use Allsvenskan - Corners 2025.xlsx. Freekicks and Throw ins use SWE SP.xlsx filtered by SP_Type.")
