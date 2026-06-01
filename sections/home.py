"""Home section — logo hero, module navigation, team snapshot."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    section_header,
)
from mm_setpieces_1.utils import load_prepared_freekick_brief_data

from sections._shared import (
    _fmt_num,
    _with_match_names,
    _set_piece_team_options,
    _safe_sorted,
    load_hops_data,
    team_snapshot_table,
    selected_team_staff_read,
    search_people,
    set_section,
)
import pandas as pd

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "setplaypro-logo.jpg"

MODULE_CARDS = [
    ("Corners",          "home_open_corners",          "⚽", "Corner kick delivery zones, shot maps, taker profiles and phase breakdowns."),
    ("Freekicks",        "home_open_freekicks",         "🎯", "Indirect free kick zones, cross maps and phase analysis."),
    ("Throw-ins",        "home_open_throwins",          "↗",  "Throw-in patterns, distances and possession outcomes."),
    ("HOPS",             "home_open_hops",              "🏃", "Player heading and duel ratings across all positions."),
    ("League Comparison","home_open_league_comparison", "📊", "Benchmark set piece stats across competitions."),
    ("Match Prep",       "home_open_match_prep",        "📋", "Opponent-specific set piece intelligence for upcoming fixtures."),
    ("Delay Analysis",   "home_open_delay",             "⏱",  "Corner delivery timing and delay patterns over time."),
]


@st.cache_data(show_spinner=False)
def _home_data(_data_version: str = DATA_VERSION):
    corners  = _with_match_names(load_prepared_sp_data("Corners", _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_data_version))
    throwins  = _with_match_names(load_prepared_sp_data("Throw ins", _data_version))
    hops      = load_hops_data(_data_version)
    return corners, freekicks, throwins, hops


def _team_options(corners, freekicks, throwins, hops) -> list[str]:
    sets = [
        set(_set_piece_team_options(df)[1:])
        for df in [corners, freekicks, throwins]
        if not df.empty
    ]
    return sorted(set.intersection(*sets)) if sets else []


def render_home() -> None:
    corners, freekicks, throwins, hops = _home_data(DATA_VERSION)
    teams = _team_options(corners, freekicks, throwins, hops)

    # ── Logo + headline ──────────────────────────────────────────────
    logo_col, text_col = st.columns([1, 3], gap="large")
    with logo_col:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
    with text_col:
        st.markdown(
            """
            <div style="padding:.6rem 0 .4rem">
                <div style="color:#374151;font-size:.65rem;font-weight:700;
                            letter-spacing:.2em;text-transform:uppercase;
                            margin-bottom:.45rem">
                    Football Intelligence
                </div>
                <div style="color:#f1f5f9;font-size:clamp(1.6rem,2.4vw,2.5rem);
                            font-weight:800;letter-spacing:-.02em;line-height:1.05;
                            margin-bottom:.5rem">
                    Set Piece Analytics
                </div>
                <div style="color:#6b7280;font-size:.94rem;line-height:1.58;
                            max-width:560px">
                    Match-prep intelligence for corners, free kicks, throw-ins,
                    player duel profiles, league benchmarks and timing analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Module navigation cards ──────────────────────────────────────
    section_header("Modules")
    for row_start in range(0, len(MODULE_CARDS), 4):
        row_items = MODULE_CARDS[row_start:row_start + 4]
        cols = st.columns(len(row_items), gap="small")
        for col, (title, key, icon, desc) in zip(cols, row_items):
            with col:
                st.markdown(
                    f"""<div class="mm-nav-card">
                        <div class="mm-card-kicker">{icon}&nbsp; Module</div>
                        <div class="mm-nav-title">{title}</div>
                        <div class="mm-nav-copy">{desc}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="mm-nav-card-action">', unsafe_allow_html=True)
                if st.button(f"Open →", key=key, use_container_width=True):
                    set_section(title)
                st.markdown("</div>", unsafe_allow_html=True)

    # ── Team Snapshot ────────────────────────────────────────────────
    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
    section_header("Team Snapshot")

    if not teams:
        st.info("No team names found in the bundled data.")
        return

    snap_col, persp_col = st.columns([3, 1], gap="small")
    with snap_col:
        selected_team = st.selectbox("Team", teams, key="home_team_snapshot", label_visibility="collapsed")
    with persp_col:
        snapshot_perspective = st.radio("View", ["For", "Against"], horizontal=True, key="home_snapshot_perspective", label_visibility="collapsed")

    snapshot = team_snapshot_table(selected_team, corners, freekicks, throwins, snapshot_perspective)

    total_set_pieces = int(snapshot["Set pieces"].sum())
    total_shots      = int(snapshot["Shots"].sum())
    total_goals      = int(snapshot["Goals"].sum())
    total_xg         = float(snapshot["xG"].sum())
    shot_rate        = (total_shots / total_set_pieces * 100) if total_set_pieces else 0
    phase_read, role_read, _ = selected_team_staff_read(selected_team, snapshot, hops)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Set pieces", f"{total_set_pieces:,}")
    c2.metric("Shots",      f"{total_shots:,}")
    c3.metric("Goals",      f"{total_goals:,}")
    c4.metric("xG",         _fmt_num(total_xg, 2))
    c5.metric("Shot rate",  f"{_fmt_num(shot_rate, 1)}%")

    ins_left, ins_right = st.columns(2)
    with ins_left:
        st.markdown(
            f"<div class='mm-insight-card'><strong style='color:#f1f5f9'>Main read:</strong>&nbsp;{phase_read}</div>",
            unsafe_allow_html=True,
        )
    with ins_right:
        st.markdown(
            f"<div class='mm-insight-card'><strong style='color:#f1f5f9'>Role read:</strong>&nbsp;{role_read}</div>",
            unsafe_allow_html=True,
        )

    render_analyst_table(snapshot, height=190)

    # ── Player search ────────────────────────────────────────────────
    search_query = st.text_input(
        "Search player",
        key="home_people_search",
        placeholder="Search by player name, taker, shooter or HOPS profile…",
        label_visibility="collapsed",
    )
    search_results = search_people(search_query, corners, freekicks, throwins, hops)
    if not search_results.empty:
        section_header("Search Results", "Across restarts and HOPS")
        render_analyst_table(search_results, height=260)
