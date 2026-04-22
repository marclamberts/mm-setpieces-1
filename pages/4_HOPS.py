from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import hero_block, inject_app_style, polish_plotly_figure, section_header

st.set_page_config(page_title="Michael Mackin Set Piece | HOPS", page_icon="⚽", layout="wide")
inject_app_style()

@st.cache_data(show_spinner=False)
def load_hops_data() -> pd.DataFrame:
    df = pd.read_excel("duel_hops_rating_summary.xlsx")
    df["Player"] = df["Player"].fillna("Unknown")
    df["Team"] = df["Team"].fillna("Unknown")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).copy()
    return df.sort_values("Rating", ascending=False)

df = load_hops_data()

hero_block(
    "Duel rating analysis",
    "HOPS",
    "Explore player duel HOPS ratings with team filters, leader tables, low-end risk checks, and a distribution overview.",
)

st.sidebar.header("HOPS filters")
teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
team = st.sidebar.selectbox("Team", teams)
top_n = st.sidebar.slider("Show top / bottom players", min_value=5, max_value=30, value=10)

filtered = df.copy()
if team != "All":
    filtered = filtered[filtered["Team"] == team].copy()

player_count = int(filtered["Player"].nunique())
team_count = int(filtered["Team"].nunique())
avg_rating = float(filtered["Rating"].mean()) if not filtered.empty else 0.0
best_rating = float(filtered["Rating"].max()) if not filtered.empty else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", player_count)
c2.metric("Teams", team_count)
c3.metric("Average rating", f"{avg_rating:.3f}")
c4.metric("Best rating", f"{best_rating:.3f}")

top_players = filtered.nlargest(top_n, "Rating")[["Player", "Team", "Rating"]].copy()
bottom_players = filtered.nsmallest(top_n, "Rating")[["Player", "Team", "Rating"]].copy()

left, right = st.columns(2)
with left:
    section_header("Top Players", f"Best {len(top_players)} in filter")
    st.dataframe(top_players, width="stretch", hide_index=True)
with right:
    section_header("Bottom Players", f"Lowest {len(bottom_players)} in filter")
    st.dataframe(bottom_players, width="stretch", hide_index=True)

chart_left, chart_right = st.columns(2)

with chart_left:
    section_header("Top Rating Chart")
    chart_df = filtered.nlargest(min(15, len(filtered)), "Rating").sort_values("Rating")
    fig = px.bar(
        chart_df,
        x="Rating",
        y="Player",
        color="Team",
        orientation="h",
        color_discrete_sequence=["#c1121f", "#0b0f14", "#2563eb", "#16a34a", "#f59e0b"],
    )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    st.plotly_chart(polish_plotly_figure(fig), width="stretch")

with chart_right:
    section_header("Rating Distribution")
    hist = px.histogram(filtered, x="Rating", nbins=20, color_discrete_sequence=["#c1121f"])
    hist.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
    )
    st.plotly_chart(polish_plotly_figure(hist), width="stretch")

section_header("Full HOPS Table", f"{len(filtered):,} players")
st.dataframe(
    filtered.sort_values("Rating", ascending=False)[["Player", "Team", "Rating"]],
    width="stretch",
    hide_index=True,
)
