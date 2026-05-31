"""Home section — team snapshot, player search, module navigation."""
from __future__ import annotations

import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    hero_block,
    section_header,
)
from mm_setpieces_1.utils import load_prepared_freekick_brief_data

from sections._shared import (
    _fmt_num,
    _with_match_names,
    _set_piece_team_options,
    _match_team_parts,
    _safe_sorted,
    load_hops_data,
    team_snapshot_table,
    selected_team_staff_read,
    search_people,
    set_section,
    _league_comparison_source,
    _league_summary_table,
    _league_phase_summary_table,
    _league_set_piece_difference_table,
)
import pandas as pd


# ---------------------------------------------------------------------------
# Cached data — loaded only when Home section is active
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _home_data(_data_version: str = DATA_VERSION):
    corners = _with_match_names(load_prepared_sp_data("Corners", _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_data_version))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _data_version))
    hops = load_hops_data(_data_version)
    return corners, freekicks, throwins, hops


def _team_options(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, hops: pd.DataFrame) -> list[str]:
    restart_team_sets = [
        set(_set_piece_team_options(df)[1:])
        for df in [corners, freekicks, throwins]
        if not df.empty
    ]
    if not restart_team_sets:
        return []
    return sorted(set.intersection(*restart_team_sets))


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_home() -> None:
    corners, freekicks, throwins, hops = _home_data(DATA_VERSION)
    teams = _team_options(corners, freekicks, throwins, hops)

    hero_block(
        "Football Intelligence",
        "Pick a team. Open a module.",
        "Simple match-prep views for set pieces, player roles, duel profiles, league benchmarks, and timing checks.",
    )

    section_header("Team Snapshot")
    if teams:
        selected_team = st.selectbox("Team", teams, key="home_team_snapshot")
        snapshot_perspective = st.radio("View", ["For", "Against"], horizontal=True, key="home_snapshot_perspective")
        snapshot = team_snapshot_table(selected_team, corners, freekicks, throwins, snapshot_perspective)

        total_set_pieces = int(snapshot["Set pieces"].sum())
        total_shots = int(snapshot["Shots"].sum())
        total_goals = int(snapshot["Goals"].sum())
        total_xg = float(snapshot["xG"].sum())
        shot_rate = (total_shots / total_set_pieces * 100) if total_set_pieces else 0
        phase_read, role_read, _ = selected_team_staff_read(selected_team, snapshot, hops)

        # Safe Streamlit-native layout instead of raw HTML f-strings
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Set pieces", f"{total_set_pieces:,}")
        c2.metric("Shots", f"{total_shots:,}")
        c3.metric("Goals", f"{total_goals:,}")
        c4.metric("xG", _fmt_num(total_xg, 2))
        c5.metric("Shot rate", f"{_fmt_num(shot_rate, 1)}%")

        ins_left, ins_right = st.columns(2)
        with ins_left:
            st.markdown(f"<div class='mm-insight-card'><strong>Main read:</strong> {phase_read}</div>", unsafe_allow_html=True)
        with ins_right:
            st.markdown(f"<div class='mm-insight-card'><strong>Role read:</strong> {role_read}</div>", unsafe_allow_html=True)

        render_analyst_table(snapshot, height=190)

        search_query = st.text_input(
            "Search player, taker, shooter, or HOPS profile",
            key="home_people_search",
            placeholder="Type at least 2 characters",
        )
        search_results = search_people(search_query, corners, freekicks, throwins, hops)
        if not search_results.empty:
            section_header("Search Results", "Across restarts and HOPS")
            render_analyst_table(search_results, height=260)
    else:
        st.info("No team names were found in the bundled data.")

    section_header("Open A Module")
    module_cols = st.columns(3)
    modules = [
        ("Corners", "home_open_corners"),
        ("Freekicks", "home_open_freekicks"),
        ("Throw-ins", "home_open_throwins"),
        ("HOPS", "home_open_hops"),
        ("League Comparison", "home_open_league_comparison"),
        ("Match Prep", "home_open_match_prep"),
        ("Delay Analysis", "home_open_delay"),
    ]
    for idx, (title, key) in enumerate(modules):
        with module_cols[idx % 3]:
            if st.button(title, key=key, use_container_width=True):
                set_section(title)
