from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Michael Mackin Set Piece | HOPS", page_icon="⚽", layout="wide")

st.markdown(
    '''
    <style>
        .stApp {background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);}
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        .page-card {
            background: rgba(255,255,255,0.97);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 24px;
            padding: 1.4rem 1.45rem 1.15rem 1.45rem;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }
        .mini-title {font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b;}
        .main-title {font-size: 2.25rem; font-weight: 800; color: #0f172a; margin: 0.2rem 0 0.35rem 0;}
        .copy {color: #475569; line-height: 1.65;}
    </style>
    ''',
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def load_hops_data() -> pd.DataFrame:
    df = pd.read_excel("duel_hops_rating_summary.xlsx")
    df["Player"] = df["Player"].fillna("Unknown")
    df["Team"] = df["Team"].fillna("Unknown")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).copy()
    return df.sort_values("Rating", ascending=False)

df = load_hops_data()

st.markdown(
    '''
    <div class="page-card">
        <div class="mini-title">Duel rating analysis</div>
        <div class="main-title">HOPS</div>
        <div class="copy">
            Explore player duel HOPS ratings with team filters, ranking tables, and a distribution overview.
        </div>
    </div>
    ''',
    unsafe_allow_html=True,
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
    st.markdown("### Top players")
    st.dataframe(top_players, width="stretch", hide_index=True)
with right:
    st.markdown("### Bottom players")
    st.dataframe(bottom_players, width="stretch", hide_index=True)

chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown("### Top rating chart")
    chart_df = filtered.nlargest(min(15, len(filtered)), "Rating").sort_values("Rating")
    fig = px.bar(
        chart_df,
        x="Rating",
        y="Player",
        color="Team",
        orientation="h",
    )
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")

with chart_right:
    st.markdown("### Rating distribution")
    hist = px.histogram(filtered, x="Rating", nbins=20)
    hist.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
    )
    st.plotly_chart(hist, width="stretch")

st.markdown("### Full HOPS table")
st.dataframe(
    filtered.sort_values("Rating", ascending=False)[["Player", "Team", "Rating"]],
    width="stretch",
    hide_index=True,
)
