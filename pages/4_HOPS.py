from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

_PAGE_FILE = Path(__file__).resolve()
_UTILS_FILE = _PAGE_FILE.parents[1] / "mm_setpieces" / "utils.py"
_PAGE_GLOBALS = globals()
_PAGE_GLOBALS["__file__"] = str(_UTILS_FILE)
exec(_UTILS_FILE.read_text(), _PAGE_GLOBALS)
_PAGE_GLOBALS["__file__"] = str(_PAGE_FILE)

st.set_page_config(
    page_title="Michael Mackin Set Piece | HOPS",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_app_style()
render_sidebar_menu("HOPS")

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

teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
team = st.sidebar.selectbox("Team", teams)
top_n = st.sidebar.slider("Show top / bottom players", min_value=5, max_value=30, value=10)

filtered = df.copy()
if team != "All":
    filtered = filtered[filtered["Team"] == team].copy()

nav_left, nav_mid, nav_right = st.columns([0.9, 1.1, 1.1])
with nav_left:
    if st.button("Back to Home", use_container_width=True):
        st.switch_page("app.py")
with nav_mid:
    st.download_button(
        "Export filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="hops_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )
with nav_right:
    st.download_button(
        "Export filtered Excel",
        data=dataframe_to_excel_bytes(filtered, sheet_name="HOPS"),
        file_name="hops_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

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

    section_header("Quick Reads", "Fast profile summaries")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.plotly_chart(
            categorical_breakdown_figure(filtered, "Tier", "Tier split", top_n=4, color="#c1121f"),
            use_container_width=True,
            key="hops_quick_tier_split",
        )
    with q2:
        st.plotly_chart(
            categorical_breakdown_figure(filtered, "Team", "Team depth", top_n=8, color="#111827"),
            use_container_width=True,
            key="hops_quick_team_depth",
        )
    with q3:
        percentile_band = filtered.copy()
        percentile_band["Percentile band"] = pd.cut(
            percentile_band["Percentile"],
            bins=[-0.1, 25, 50, 75, 90, 100],
            labels=["0-25", "26-50", "51-75", "76-90", "91-100"],
        ).astype(str)
        st.plotly_chart(
            categorical_breakdown_figure(percentile_band, "Percentile band", "Percentile spread", top_n=5, color="#1d4ed8"),
            use_container_width=True,
            key="hops_quick_percentile_spread",
        )

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
        st.plotly_chart(polish_plotly_figure(fig), use_container_width=True, key="hops_top_rating_evidence")

    with chart_right:
        section_header("Rating Distribution")
        hist = px.histogram(filtered, x="Rating", color="Tier", nbins=20, color_discrete_sequence=["#94a3b8", "#64748b", "#1d4ed8", "#c1121f"])
        hist.update_layout(
            height=520,
            margin=dict(l=10, r=10, t=30, b=10),
            legend_title_text="",
        )
        st.plotly_chart(polish_plotly_figure(hist), use_container_width=True, key="hops_rating_distribution")

with data_tab:
    section_header("Player Log", f"{len(filtered):,} players")
    render_analyst_table(
        filtered.sort_values("Rating", ascending=False)[["Player", "Team", "Rating", "Percentile", "Tier"]],
        height=620,
    )
