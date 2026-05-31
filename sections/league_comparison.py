"""League Comparison section."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    load_prepared_freekick_brief_data,
    render_analyst_table,
    hero_block,
    section_header,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    polish_plotly_figure,
)

from sections._shared import (
    _safe_sorted,
    _league_selectbox,
    _with_match_names,
    load_hops_data,
    _league_comparison_source,
    _league_summary_table,
    _league_phase_summary_table,
    _league_set_piece_difference_table,
    bar_chart,
    render_plotly_visual,
    simple_view_radio,
)


@st.cache_data(show_spinner=False)
def _lc_datasets(_data_version: str = DATA_VERSION):
    corners = _with_match_names(load_prepared_sp_data("Corners", _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_data_version))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _data_version))
    return corners, freekicks, throwins


def render_league_comparison() -> None:
    corners, freekicks, throwins = _lc_datasets(DATA_VERSION)
    df = _league_comparison_source(corners, freekicks, throwins)
    hero_block("League comparison", "League Comparison", "Benchmark restart volume, shot creation, and shot quality across competitions.")
    if df.empty:
        st.warning("No restart rows were found for league comparison.")
        return

    phases = ["All"] + _safe_sorted(df["Phase"]) if "Phase" in df.columns else ["All"]
    leagues = _safe_sorted(df["League"]) if "League" in df.columns else []
    phase = st.sidebar.selectbox("Phase", phases, key="league_comparison_phase")
    if any(league not in leagues for league in st.session_state.get("league_comparison_leagues", [])):
        st.session_state["league_comparison_leagues"] = leagues
    selected_leagues = leagues
    min_set_pieces = 10
    top_n = min(10, max(3, len(leagues)))
    with st.sidebar.expander("More filters", expanded=False):
        selected_leagues = st.multiselect("Leagues", leagues, default=leagues, key="league_comparison_leagues")
        min_set_pieces = st.slider("Minimum set pieces", min_value=1, max_value=100, value=10, key="league_comparison_min_sp")
        top_n = st.slider("Rows", min_value=3, max_value=20, value=top_n, key="league_comparison_top_n")

    filtered = df.copy()
    if phase != "All" and "Phase" in filtered.columns:
        filtered = filtered[filtered["Phase"].eq(phase)].copy()
    if selected_leagues and "League" in filtered.columns:
        filtered = filtered[filtered["League"].isin(selected_leagues)].copy()

    summary = _league_summary_table(filtered)
    if not summary.empty:
        summary = summary[summary["Set pieces"] >= min_set_pieces].copy()
    phase_summary = _league_phase_summary_table(filtered)
    if not phase_summary.empty and not summary.empty:
        phase_summary = phase_summary[phase_summary["League"].isin(summary["League"])].copy()
    set_piece_differences = _league_set_piece_difference_table(phase_summary)

    render_export_controls(filtered, "league_comparison", "League Comparison")
    render_filter_summary(
        "League Comparison", len(df), len(filtered),
        [("Phase", phase), ("Leagues", selected_leagues), ("Minimum set pieces", min_set_pieces)],
    )
    if filtered.empty or summary.empty:
        render_empty_filter_state()
        return

    league_count = int(summary["League"].nunique())
    set_pieces = int(summary["Set pieces"].sum())
    shots = int(summary["Shots"].sum())
    total_xg = float(summary["xG"].sum())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Leagues", league_count)
    c2.metric("Set pieces", f"{set_pieces:,}")
    c3.metric("Shots", f"{shots:,}")
    c4.metric("Shot rate", f"{(shots / set_pieces * 100) if set_pieces else 0:.1f}%")
    c5.metric("xG / 100", f"{(total_xg / set_pieces * 100) if set_pieces else 0:.2f}")

    view = simple_view_radio("league_comparison_view", ["Summary", "Charts", "Rows"])
    if view == "Summary":
        left, right = st.columns([1.2, 1])
        with left:
            section_header("League Threat Board", "Restart output by competition")
            render_analyst_table(summary.head(top_n), height=430)
        with right:
            section_header("Phase Split", "How each league creates threat by restart type")
            render_analyst_table(phase_summary.sort_values(["xG / 100", "Set pieces"], ascending=False).head(top_n * 3), height=430)
        section_header("Set Piece Differences", "Goals and xG per restart by phase")
        render_analyst_table(set_piece_differences.head(top_n), height=430)

    elif view == "Charts":
        chart_left, chart_right = st.columns(2)
        chart_df = summary.head(top_n).sort_values("xG / 100")
        with chart_left:
            section_header("xG / 100", "Shot value generated per 100 restarts")
            fig = bar_chart(chart_df, x="xG / 100", y="League", color=None, orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "League comparison xG per 100", "league_comparison_xg_per_100_png")
        with chart_right:
            section_header("Shot Rate", "Share of restarts ending in a shot")
            shot_df = summary.head(top_n).sort_values("Shot rate %")
            fig = bar_chart(shot_df, x="Shot rate %", y="League", color=None, orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "League comparison shot rate", "league_comparison_shot_rate_png")

        if not phase_summary.empty:
            section_header("Phase Threat Mix", "xG / 100 by league and restart phase")
            phase_chart = phase_summary[phase_summary["League"].isin(summary.head(top_n)["League"])].copy()
            fig = bar_chart(phase_chart, x="League", y="xG / 100", color="Phase", barmode="group")
            fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "League comparison phase threat", "league_comparison_phase_threat_png")

        if not set_piece_differences.empty:
            section_header("Set Piece Difference Evidence", "Where corners, indirect free kicks, and throw-ins separate")
            diff_cols = ["League", "Corner xG edge vs indirect FK", "Corner xG edge vs throw-in", "Indirect FK xG edge vs throw-in"]
            diff_chart = set_piece_differences[diff_cols].head(top_n).melt("League", var_name="Difference", value_name="xG edge")
            fig = bar_chart(diff_chart, x="League", y="xG edge", color="Difference", barmode="group")
            fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "League comparison set piece differences", "league_comparison_set_piece_differences_png")

    elif view == "Rows":
        section_header("Rows", f"{len(filtered):,} restart rows in the active filter")
        display_cols = [c for c in [
            "League", "Phase", "Match", "Team", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=620)
