"""Home section — database stats, module navigation, team snapshot."""
from __future__ import annotations

from pathlib import Path

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    section_header,
    load_prepared_freekick_brief_data,
)

from sections._shared import (
    _fmt_num,
    _with_match_names,
    _set_piece_team_options,
    load_hops_data,
    team_snapshot_table,
    selected_team_staff_read,
    search_people,
    set_section,
    FILTER_PREFIXES,
)

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "setplaypro-logo.jpg"

MODULE_CARDS = [
    ("Corners",          "home_open_corners",          "⚽", "Corner Kicks",
     "Delivery zones, shot maps, taker profiles, phase breakdowns."),
    ("Freekicks",        "home_open_freekicks",         "🎯", "Free Kicks",
     "Indirect FK zones, cross maps, phase and sequence analysis."),
    ("Throw-ins",        "home_open_throwins",          "↗",  "Throw-ins",
     "Throw-in patterns, distances and possession outcomes."),
    ("HOPS",             "home_open_hops",              "🏃", "HOPS",
     "Player heading and aerial duel ratings across all positions."),
    ("League Comparison","home_open_league_comparison", "📊", "League Comparison",
     "Benchmark set piece output across competitions."),
    ("Match Prep",       "home_open_match_prep",        "📋", "Match Prep",
     "Opponent-specific set piece intelligence for upcoming fixtures."),
    ("Delay Analysis",   "home_open_delay",             "⏱",  "Delay Analysis",
     "Corner delivery timing and delay patterns over time."),
]


@st.cache_data(show_spinner=False)
def _home_data(_data_version: str = DATA_VERSION):
    corners   = _with_match_names(load_prepared_sp_data("Corners",    _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(   _data_version))
    throwins  = _with_match_names(load_prepared_sp_data("Throw ins",  _data_version))
    hops      = load_hops_data(_data_version)
    return corners, freekicks, throwins, hops


def _db_stats(corners, freekicks, throwins, hops) -> list[tuple[str, str, str]]:
    """Return (label, value, sublabel) tuples for the database stats bar."""
    total_corners   = len(corners)   if not corners.empty   else 0
    total_fks       = len(freekicks) if not freekicks.empty else 0
    total_throwins  = len(throwins)  if not throwins.empty  else 0

    teams: set = set()
    for df in [corners, freekicks, throwins]:
        if not df.empty and "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    teams.discard("Unknown")

    leagues: set = set()
    for df in [corners, freekicks, throwins]:
        if not df.empty and "League" in df.columns:
            leagues.update(df["League"].dropna().astype(str).unique())
    leagues.discard("Unknown")

    matches: set = set()
    for df in [corners, freekicks, throwins]:
        if not df.empty and "Match" in df.columns:
            matches.update(df["Match"].dropna().astype(str).unique())

    players = 0
    if not hops.empty and "Player" in hops.columns:
        players = int(hops["Player"].nunique())

    def _fmt(n: int) -> str:
        return f"{n:,}"

    return [
        ("⚽", _fmt(total_corners),  "corners"),
        ("🎯", _fmt(total_fks),      "free kicks"),
        ("↗",  _fmt(total_throwins), "throw-ins"),
        ("🏟", _fmt(len(matches)),   "matches"),
        ("🛡", _fmt(len(teams)),     "teams"),
        ("🏆", _fmt(len(leagues)),   "leagues"),
        ("🏃", _fmt(players),        "HOPS players"),
    ]


def _render_highlights(corners, freekicks, throwins, hops) -> None:
    items: list[tuple[str, str, str]] = []

    # Best HOPS player
    if not hops.empty and "Player" in hops.columns and "Rating" in hops.columns:
        top = hops.nlargest(1, "Rating").iloc[0]
        items.append((
            "Top aerial player",
            str(top["Player"]),
            f"Rating {top['Rating']:.3f} · {top.get('Team', '')}",
        ))

    # Team with most corner shots
    shot_col = next((c for c in ["is_shot", "Shot", "shot"] if c in corners.columns), None)
    if not corners.empty and "Team" in corners.columns and shot_col:
        shot_col = shot_col
        shot_df = corners[corners[shot_col].astype(str).str.lower().isin(["true", "1", "yes", "shot"])]
        if shot_df.empty:
            shot_df = corners
        team_shots = shot_df.groupby("Team").size().sort_values(ascending=False)
        if not team_shots.empty:
            best_team = team_shots.index[0]
            items.append((
                "Most corner shots",
                str(best_team),
                f"{team_shots.iloc[0]:,} shots from corners",
            ))
    if len(items) < 2 and not corners.empty and "Team" in corners.columns:
        team_counts = corners.groupby("Team").size().sort_values(ascending=False)
        if not team_counts.empty:
            items.append((
                "Most active corner team",
                str(team_counts.index[0]),
                f"{team_counts.iloc[0]:,} corners taken",
            ))

    # League with most events
    all_events = pd.concat(
        [df[["League"]] for df in [corners, freekicks, throwins]
         if not df.empty and "League" in df.columns],
        ignore_index=True,
    )
    if not all_events.empty:
        league_counts = all_events.groupby("League").size().sort_values(ascending=False)
        if not league_counts.empty:
            items.append((
                "Most data",
                str(league_counts.index[0]),
                f"{league_counts.iloc[0]:,} events indexed",
            ))

    # Top freekick team by event count
    if not freekicks.empty and "Team" in freekicks.columns:
        fk_counts = freekicks.groupby("Team").size().sort_values(ascending=False)
        if not fk_counts.empty:
            items.append((
                "Most active FK team",
                str(fk_counts.index[0]),
                f"{fk_counts.iloc[0]:,} free kicks",
            ))

    # Render up to 4 highlights
    items = items[:4]
    if not items:
        return
    cols = st.columns(len(items), gap="small")
    for col, (label, value, sub) in zip(cols, items):
        col.markdown(
            f"""<div class="mm-kpi-card" style="background:#161922;border:1px solid rgba(255,255,255,0.08);
                border-top:2px solid #22c55e;border-radius:6px;padding:.75rem .9rem .6rem">
                <div class="mm-kpi-label">{label}</div>
                <div class="mm-kpi-value" style="font-size:1rem;letter-spacing:-.01em;line-height:1.2">{value}</div>
                <div class="mm-kpi-help">{sub}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_home() -> None:
    corners, freekicks, throwins, hops = _home_data(DATA_VERSION)

    # ── Database stats bar ───────────────────────────────────────────
    stats = _db_stats(corners, freekicks, throwins, hops)
    stat_items = "".join(
        f"""<div class="mm-dbstat">
               <span class="mm-dbstat-icon">{icon}</span>
               <span class="mm-dbstat-val">{val}</span>
               <span class="mm-dbstat-lbl">{lbl}</span>
            </div>"""
        for icon, val, lbl in stats
    )
    st.markdown(
        f'<div class="mm-dbstats-bar">{stat_items}</div>',
        unsafe_allow_html=True,
    )

    # ── Highlights strip ─────────────────────────────────────────────
    section_header("Season highlights")
    _render_highlights(corners, freekicks, throwins, hops)

    # ── Module cards ─────────────────────────────────────────────────
    section_header("Analysis Modules")
    # 4-col first row, 3-col second row
    rows = [MODULE_CARDS[:4], MODULE_CARDS[4:]]
    for row in rows:
        if not row:
            continue
        cols = st.columns(len(row), gap="small")
        for col, (section, key, icon, short, desc) in zip(cols, row):
            with col:
                # Invisible overlay button fills the card; visible card is pure HTML
                st.markdown(
                    f"""<div class="mm-mod-card" id="mc-{key}">
                        <div class="mm-mod-icon">{icon}</div>
                        <div class="mm-mod-title">{short}</div>
                        <div class="mm-mod-desc">{desc}</div>
                        <div class="mm-mod-cta">Open →</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button("", key=key, use_container_width=True, help=f"Open {short}"):
                    set_section(section)

    # ── Team Snapshot ────────────────────────────────────────────────
    st.markdown("<div style='height:.2rem'></div>", unsafe_allow_html=True)
    section_header("Team Snapshot")

    teams_for = sorted({
        t for df in [corners, freekicks, throwins]
        if not df.empty and "Team" in df.columns
        for t in df["Team"].dropna().astype(str).unique()
        if t and t != "Unknown"
    })

    if not teams_for:
        st.info("No team names found in the bundled data.")
        return

    sc1, sc2, sc3 = st.columns([3, 1, 1], gap="small")
    with sc1:
        selected_team = st.selectbox("Team", teams_for, key="home_team_snapshot",
                                     label_visibility="collapsed")
    with sc2:
        snapshot_perspective = st.radio("View", ["For", "Against"], horizontal=True,
                                        key="home_snapshot_perspective",
                                        label_visibility="collapsed")
    with sc3:
        st.markdown("<div style='height:.35rem'></div>", unsafe_allow_html=True)

    snapshot = team_snapshot_table(selected_team, corners, freekicks, throwins, snapshot_perspective)

    total_sp    = int(snapshot["Set pieces"].sum())
    total_shots = int(snapshot["Shots"].sum())
    total_goals = int(snapshot["Goals"].sum())
    total_xg    = float(snapshot["xG"].sum())
    shot_rate   = (total_shots / total_sp * 100) if total_sp else 0
    xg_per_100  = (total_xg / total_sp * 100) if total_sp else 0
    phase_read, role_read, hops_read = selected_team_staff_read(selected_team, snapshot, hops)

    # KPI row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Set pieces",  f"{total_sp:,}")
    k2.metric("Shots",       f"{total_shots:,}")
    k3.metric("Goals",       f"{total_goals:,}")
    k4.metric("xG",          _fmt_num(total_xg, 2))
    k5.metric("Shot rate",   f"{_fmt_num(shot_rate, 1)}%")
    k6.metric("xG / 100",    _fmt_num(xg_per_100, 2))

    # Insight cards
    ins_l, ins_r = st.columns(2)
    with ins_l:
        st.markdown(
            f"<div class='mm-insight-card'>"
            f"<strong>Threat read</strong>&ensp;{phase_read}</div>",
            unsafe_allow_html=True,
        )
    with ins_r:
        st.markdown(
            f"<div class='mm-insight-card'>"
            f"<strong>Personnel</strong>&ensp;{role_read}</div>",
            unsafe_allow_html=True,
        )

    render_analyst_table(snapshot, height=190)

    jc1, jc2, jc3, jc4 = st.columns(4)
    if jc1.button(f"⚽ {selected_team} Corners", key="home_jump_corners"):
        set_section("Corners", team=selected_team)
    if jc2.button(f"🎯 {selected_team} Freekicks", key="home_jump_fk"):
        set_section("Freekicks", team=selected_team)
    if jc3.button(f"↗ {selected_team} Throw-ins", key="home_jump_ti"):
        set_section("Throw-ins", team=selected_team)
    if jc4.button(f"🏃 {selected_team} HOPS", key="home_jump_hops"):
        set_section("HOPS", team=selected_team)

    # ── Global player search ─────────────────────────────────────────
    st.markdown("<div style='height:.15rem'></div>", unsafe_allow_html=True)
    section_header("Player Search")
    search_query = st.text_input(
        "Search",
        key="home_people_search",
        placeholder="Search by player name across corners, free kicks, throw-ins and HOPS…",
        label_visibility="collapsed",
    )
    if search_query:
        search_results = search_people(search_query, corners, freekicks, throwins, hops)
        if not search_results.empty:
            render_analyst_table(search_results, height=280)
        else:
            st.caption("No results found.")
