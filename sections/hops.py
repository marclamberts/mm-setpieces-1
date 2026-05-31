"""HOPS (player duel profiles) section."""
from __future__ import annotations

import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    render_analyst_table,
    hero_block,
    section_header,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    polish_plotly_figure,
)

from sections._shared import (
    _league_filter_options,
    _league_selectbox,
    load_hops_data,
    bar_chart,
    histogram_chart,
    simple_view_radio,
    render_plotly_visual,
)


def render_hops() -> None:
    df = load_hops_data(DATA_VERSION)
    hero_block("Players", "HOPS", "Simple duel profile rankings.")
    if df.empty:
        st.warning("No HOPS rows were found in Data/HOPS.")
        return

    leagues = _league_filter_options(df, "HOPS")
    teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
    league = _league_selectbox("League", leagues, key="hops_league")
    team = st.sidebar.selectbox("Team", teams, key="hops_team")
    with st.sidebar.expander("More filters", expanded=False):
        top_n = st.slider("Rows", min_value=5, max_value=30, value=10, key="hops_top_n")

    filtered = df.copy()
    if league != "All":
        filtered = filtered[filtered["League"] == league].copy()
    if team != "All":
        filtered = filtered[filtered["Team"] == team].copy()

    render_export_controls(filtered, "hops", "HOPS")
    render_filter_summary("HOPS", len(df), len(filtered), [("League", league), ("Team", team), ("Rows", f"Top/bottom {top_n}")])
    if filtered.empty:
        render_empty_filter_state()

    import pandas as pd
    player_count = int(filtered["Player"].nunique())
    team_count = int(filtered["Team"].nunique())
    avg_rating = float(filtered["Rating"].mean()) if not filtered.empty else 0.0
    best_rating = float(filtered["Rating"].max()) if not filtered.empty else 0.0
    elite_count = int((filtered["Tier"] == "Elite").sum()) if "Tier" in filtered.columns else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Players", player_count)
    c2.metric("Teams", team_count)
    c3.metric("Average rating", f"{avg_rating:.3f}")
    c4.metric("Best rating", f"{best_rating:.3f}")
    c5.metric("Elite profiles", elite_count)

    team_summary = (
        filtered.groupby(["League", "Team"], dropna=False)
        .agg(
            Players=("Player", "nunique"),
            Avg_Rating=("Rating", "mean"),
            Median_Rating=("Rating", "median"),
            Best_Rating=("Rating", "max"),
            Elite=("Tier", lambda s: int((s == "Elite").sum())),
            Strong_Plus=("Tier", lambda s: int(s.isin(["Strong", "Elite"]).sum())),
        )
        .reset_index()
    )
    for col in ["Avg_Rating", "Median_Rating", "Best_Rating"]:
        team_summary[col] = team_summary[col].round(3)
    team_summary = team_summary.sort_values(["Avg_Rating", "Elite", "Strong_Plus"], ascending=False)

    top_players = filtered.nlargest(top_n, "Rating")[["Player", "Team", "League", "Rating", "Percentile", "Tier"]].copy()
    bottom_players = filtered.nsmallest(top_n, "Rating")[["Player", "Team", "League", "Rating", "Percentile", "Tier"]].copy()

    view = simple_view_radio("hops_view", ["Summary", "Charts", "Rows"])
    if view == "Summary":
        left, right = st.columns([1.15, 1])
        with left:
            section_header("Team Duel Board", "Average rating and high-end profiles by squad")
            render_analyst_table(team_summary, height=410)
        with right:
            section_header("Priority Profiles", f"Best {len(top_players)} in filter")
            render_analyst_table(top_players, height=410)
        section_header("Lowest Ratings", "Bottom of the filter")
        render_analyst_table(bottom_players, height=330)

    elif view == "Charts":
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Top Rating Evidence")
            chart_df = filtered.nlargest(min(15, len(filtered)), "Rating").sort_values("Rating")
            fig = bar_chart(chart_df, x="Rating", y="Player", color="Team", orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "HOPS top rating evidence", "hops_top_rating_evidence_png")
        with chart_right:
            section_header("Rating Distribution")
            hist = histogram_chart(filtered, "Rating", color="Tier", nbins=20)
            hist.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(hist), "HOPS rating distribution", "hops_rating_distribution_png")

    elif view == "Rows":
        section_header("Rows", f"{len(filtered):,} players")
        render_analyst_table(
            filtered.sort_values("Rating", ascending=False)[["Player", "Team", "League", "Rating", "Percentile", "Tier"]],
            height=620,
        )
