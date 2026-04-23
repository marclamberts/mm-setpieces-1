from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import hero_block, inject_app_style, polish_plotly_figure, render_analyst_table, section_header

st.set_page_config(page_title="Michael Mackin Set Piece | HOPS", page_icon="⚽", layout="wide")
inject_app_style()

@st.cache_data(show_spinner=False)
def load_hops_data() -> pd.DataFrame:
    df = pd.read_excel("duel_hops_rating_summary.xlsx")
    df["Player"] = df["Player"].fillna("Unknown")
    df["Team"] = df["Team"].fillna("Unknown")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).copy()
    df["Percentile"] = (df["Rating"].rank(pct=True) * 100).round(1)
    df["Tier"] = pd.cut(
        df["Percentile"],
        bins=[-0.1, 50, 75, 90, 100],
        labels=["Depth", "Rotation", "Strong", "Elite"],
    ).astype(str)
    return df.sort_values("Rating", ascending=False)

df = load_hops_data()

hero_block(
    "Duel intelligence",
    "HOPS",
    "Player and team duel profiles from the HOPS workbook, ranked by rating, percentile, and squad-level depth.",
)

st.sidebar.header("HOPS filters")
teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
with st.sidebar.expander("Scope", expanded=True):
    team = st.selectbox("Team", teams)
with st.sidebar.expander("Board settings", expanded=True):
    top_n = st.slider("Show top / bottom players", min_value=5, max_value=30, value=10)

filtered = df.copy()
if team != "All":
    filtered = filtered[filtered["Team"] == team].copy()

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
    filtered.groupby("Team", dropna=False)
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
team_summary["Avg_Rating"] = team_summary["Avg_Rating"].round(3)
team_summary["Median_Rating"] = team_summary["Median_Rating"].round(3)
team_summary["Best_Rating"] = team_summary["Best_Rating"].round(3)
team_summary = team_summary.sort_values(["Avg_Rating", "Elite", "Strong_Plus"], ascending=False)

top_players = filtered.nlargest(top_n, "Rating")[["Player", "Team", "Rating", "Percentile", "Tier"]].copy()
bottom_players = filtered.nsmallest(top_n, "Rating")[["Player", "Team", "Rating", "Percentile", "Tier"]].copy()

overview_tab, charts_tab, data_tab = st.tabs(["Briefing", "Duel Evidence", "Player Log"])

with overview_tab:
    left, right = st.columns([1.15, 1])
    with left:
        section_header("Team Duel Board", "Average rating and high-end profiles by squad")
        render_analyst_table(team_summary, height=410)
    with right:
        section_header("Priority Profiles", f"Best {len(top_players)} in filter")
        render_analyst_table(top_players, height=410)

    section_header("Risk Check", "Lowest ratings in the active filter")
    render_analyst_table(bottom_players, height=330)

with charts_tab:
    chart_left, chart_right = st.columns(2)

    with chart_left:
        section_header("Top Rating Evidence")
        chart_df = filtered.nlargest(min(15, len(filtered)), "Rating").sort_values("Rating")
        fig = px.bar(
            chart_df,
            x="Rating",
            y="Player",
            color="Team",
            orientation="h",
            color_discrete_sequence=["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309"],
        )
        fig.update_layout(
            height=520,
            margin=dict(l=10, r=10, t=30, b=10),
            legend_title_text="",
        )
        st.plotly_chart(polish_plotly_figure(fig), use_container_width=True)

    with chart_right:
        section_header("Rating Distribution")
        hist = px.histogram(filtered, x="Rating", color="Tier", nbins=20, color_discrete_sequence=["#94a3b8", "#64748b", "#1d4ed8", "#c1121f"])
        hist.update_layout(
            height=520,
            margin=dict(l=10, r=10, t=30, b=10),
            legend_title_text="",
        )
        st.plotly_chart(polish_plotly_figure(hist), use_container_width=True)

with data_tab:
    section_header("Player Log", f"{len(filtered):,} players")
    render_analyst_table(
        filtered.sort_values("Rating", ascending=False)[["Player", "Team", "Rating", "Percentile", "Tier"]],
        height=620,
    )
