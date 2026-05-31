"""Freekicks section — dedicated render function, no is_freekick flag."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_freekick_brief_data,
    render_analyst_table,
    hero_block,
    section_header,
    kpi_row,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    generate_set_piece_insights,
    polish_plotly_figure,
    freekick_sequence_summary,
    freekick_zone_summary,
    freekick_taker_summary,
    freekick_shooter_summary,
    freekick_origin_map_figure,
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
    simple_view_radio,
)


def render_freekicks() -> None:
    label = "Freekicks"
    df = _with_match_names(load_prepared_freekick_brief_data(DATA_VERSION))
    hero_block("Set pieces", label, "Choose a team or league and read the full dashboard on one page.")
    if df.empty:
        st.warning("No freekick rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    teams = _set_piece_team_options(df)
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []

    league = _league_selectbox("League", leagues, key="freekicks_league")
    team = st.sidebar.selectbox("Team", teams, key="freekicks_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key="freekicks_perspective")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key="freekicks_sample")
    taker_filter: list[str] = []
    with st.sidebar.expander("More filters", expanded=False):
        taker_filter = st.multiselect("Taker", takers, key="freekicks_taker")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10].copy()
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()

    sequences = freekick_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Sample", sample), ("Taker", taker_filter),
    ]

    render_export_controls(filtered, "freekicks", label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()

    kpi_row(filtered)

    seq_count = int(len(sequences))
    avg_actions = float(sequences["Actions"].mean()) if not sequences.empty else 0.0
    direct_threat = float((sequences["Zone"].eq("Direct threat")).mean() * 100) if not sequences.empty else 0.0
    wide_delivery = float((sequences["Zone"].eq("Wide delivery")).mean() * 100) if not sequences.empty else 0.0
    best_seq_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sequences", seq_count)
    c2.metric("Avg actions", f"{avg_actions:.1f}")
    c3.metric("Direct threat", f"{direct_threat:.1f}%")
    c4.metric("Wide delivery", f"{wide_delivery:.1f}%")
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
        render_analyst_table(freekick_zone_summary(filtered).head(12), height=330)

    section_header("Priority Sequences")
    base_cols = ["Match", "Team", "Minute", "Zone", "Channel", "Initial taker", "Initial height",
                 "Actions", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
    priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
    render_analyst_table(priority.head(30), height=360)

    section_header("Charts")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        render_mpl_visual(freekick_origin_map_figure(filtered), f"{label} origin map", "freekicks_origin_map_png")
    with chart_right:
        if not sequences.empty:
            mix = sequences.groupby("Channel", dropna=False).size().reset_index(name="Sequences")
            if not mix.empty:
                fig = bar_chart(mix.sort_values("Sequences", ascending=False), x="Channel", y="Sequences", color="Channel")
                fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                render_plotly_visual(polish_plotly_figure(fig), f"{label} mix", "freekicks_mix_png")

    section_header("Pitch")
    pitch_left, pitch_right = st.columns(2)
    with pitch_left:
        render_plotly_visual(polish_plotly_figure(starting_location_map_figure(filtered, f"{label} start locations")), f"{label} start locations", "freekicks_start_locations_png")
    with pitch_right:
        render_plotly_visual(polish_plotly_figure(shotmap_figure(filtered, f"{label} shot map")), f"{label} shot map", "freekicks_shot_map_png")

    section_header("Roles")
    role_left, role_right = st.columns(2)
    with role_left:
        render_analyst_table(freekick_taker_summary(filtered).head(25), height=420)
    with role_right:
        render_analyst_table(freekick_shooter_summary(filtered).head(25), height=420)

    with st.expander("Rows", expanded=False):
        render_analyst_table(sequences, height=430)
        display_cols = [c for c in [
            "Match", "Team", "Taker", "Shooter", "minute", "second", "pass_x", "pass_y",
            "Delivery height", "Shot outcome", "xg", "Occupation_Rating", "Proximity_Rating",
            "Duel_Win_Prob", "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=520)
