"""Throw-ins section — dedicated render function, no is_freekick flag."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    hero_block,
    section_header,
    kpi_row,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    generate_set_piece_insights,
    polish_plotly_figure,
    throwin_sequence_summary,
    throwin_zone_summary,
    throwin_taker_summary,
    throwin_shooter_summary,
    throwin_delivery_map_figure,
    throwin_outcome_zone_figure,
    shotmap_figure,
    starting_location_map_figure,
)

from sections._shared import (
    _safe_sorted,
    _league_filter_options,
    _league_selectbox,
    _set_piece_team_options,
    _apply_team_perspective,
    _with_match_names,
    bar_chart,
    render_plotly_visual,
    render_mpl_visual,
)


def render_throwins() -> None:
    label = "Throw-ins"
    df = _with_match_names(load_prepared_sp_data("Throw ins", DATA_VERSION))
    hero_block("Set pieces", label, "Choose a team or league and read the full dashboard on one page.")
    if df.empty:
        st.warning("No throw-in rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    teams = _set_piece_team_options(df)
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shooters = _safe_sorted(df["Shooter"]) if "Shooter" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    league = _league_selectbox("League", leagues, key="throwins_league")
    team = st.sidebar.selectbox("Team", teams, key="throwins_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key="throwins_perspective")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key="throwins_sample")

    minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min()) if "minute" in df.columns else 0
    minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max())) if "minute" in df.columns else 95

    period = "All"
    minute_range = (minute_min, minute_max)
    taker_filter: list[str] = []
    shooter_filter: list[str] = []
    height_filter: list[str] = []
    outcome_filter: list[str] = []

    with st.sidebar.expander("More filters", expanded=False):
        period = st.selectbox("Game period", periods, key="throwins_period")
        minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key="throwins_minutes")
        taker_filter = st.multiselect("Thrower", takers, key="throwins_taker")
        shooter_filter = st.multiselect("Shooter", shooters, key="throwins_shooter")
        height_filter = st.multiselect("Height", heights, key="throwins_height")
        outcome_filter = st.multiselect("Shot outcome", outcomes, key="throwins_outcome")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if period != "All" and "game_period" in filtered.columns:
        filtered = filtered[filtered["game_period"].eq(period)].copy()
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10].copy()
    if "minute" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["minute"], errors="coerce").between(minute_range[0], minute_range[1])].copy()
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()
    if shooter_filter and "Shooter" in filtered.columns:
        filtered = filtered[filtered["Shooter"].isin(shooter_filter)].copy()
    if height_filter and "Delivery height" in filtered.columns:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)].copy()
    if outcome_filter and "Shot outcome" in filtered.columns:
        filtered = filtered[filtered["Shot outcome"].isin(outcome_filter)].copy()

    sequences = throwin_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Period", period), ("Sample", sample),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Thrower", taker_filter), ("Shooter", shooter_filter),
        ("Height", height_filter), ("Shot outcome", outcome_filter),
    ]

    render_export_controls(filtered, "throwins", label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()

    kpi_row(filtered)

    seq_count = int(len(sequences))
    box_entry_rate = float(sequences["Box entry"].mean() * 100) if not sequences.empty and "Box entry" in sequences.columns else 0.0
    attack_zone_rate = float((sequences["Zone"].eq("Attacking channel")).mean() * 100) if not sequences.empty else 0.0
    shots_total = int(sequences["Shots"].sum()) if not sequences.empty else 0
    best_seq_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sequences", seq_count)
    c2.metric("Box entry %", f"{box_entry_rate:.1f}%")
    c3.metric("Attacking third", f"{attack_zone_rate:.1f}%")
    c4.metric("Shots", shots_total)
    st.metric("Best sequence xG", f"{best_seq_xg:.3f}")

    scope = team if team != "All" else league if league != "All" else "All teams"
    insights = generate_set_piece_insights(filtered, label)
    if not sequences.empty:
        top_zone = sequences["Zone"].value_counts().head(1)
        if not top_zone.empty:
            insights.insert(0, f"Most common zone is {top_zone.index[0].lower()} ({top_zone.iloc[0]} sequences).")

    section_header(f"{scope} Dashboard")
    dash_left, dash_right = st.columns([0.9, 1.3])
    with dash_left:
        for insight in insights[:5]:
            st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)
    with dash_right:
        render_analyst_table(throwin_zone_summary(filtered).head(12), height=330)

    section_header("Priority Sequences")
    base_cols = ["Match", "Team", "Minute", "Zone", "Side", "Initial taker", "Initial height",
                 "Box entry", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
    priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
    render_analyst_table(priority.head(30), height=360)

    section_header("Charts")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_mpl_visual(throwin_delivery_map_figure(filtered), "Throw-in deliveries", "throwins_delivery_map_png")
    with chart_right:
        if not sequences.empty:
            side_mix = (sequences.groupby("Side", dropna=False)
                        .agg(Sequences=("Side", "size"), Box_entries=("Box entry", "sum"))
                        .reset_index())
            side_mix["Box entry %"] = (side_mix["Box_entries"] / side_mix["Sequences"] * 100).round(1)
            fig = bar_chart(side_mix, x="Side", y="Box entry %", color="Side")
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            from mm_setpieces_1.utils import polish_plotly_figure
            render_plotly_visual(polish_plotly_figure(fig), "Box entry % by side", "throwins_side_box_png")

    section_header("Pitch")
    render_mpl_visual(throwin_outcome_zone_figure(filtered), "Throw-in outcome zones", "throwins_outcome_zones_png")
    pitch_left, pitch_right = st.columns(2)
    with pitch_left:
        render_plotly_visual(polish_plotly_figure(starting_location_map_figure(filtered, f"{label} start locations")), f"{label} start locations", "throwins_start_locations_png")
    with pitch_right:
        render_plotly_visual(polish_plotly_figure(shotmap_figure(filtered, f"{label} shot map")), f"{label} shot map", "throwins_shot_map_png")

    section_header("Roles")
    role_left, role_right = st.columns(2)
    with role_left:
        render_analyst_table(throwin_taker_summary(filtered).head(25), height=420)
    with role_right:
        render_analyst_table(throwin_shooter_summary(filtered).head(25), height=420)

    with st.expander("Rows", expanded=False):
        render_analyst_table(sequences, height=430)
        display_cols = [c for c in [
            "Match", "Team", "Taker", "Shooter", "minute", "second", "pass_x", "pass_y",
            "Delivery height", "Shot outcome", "xg", "Occupation_Rating", "Proximity_Rating",
            "Duel_Win_Prob", "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=520)
