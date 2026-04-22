from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import hero_block, inject_app_style, polish_plotly_figure, section_header

st.set_page_config(page_title="Michael Mackin Set Piece | Delay Analysis", page_icon="⚽", layout="wide")
inject_app_style()

@st.cache_data
def load_delay():
    df = pd.read_excel("corner_delays (1).xlsx")
    return df

def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None

df = load_delay()

hero_block(
    "Corner timing analysis",
    "Delay Analysis",
    "Measure how long corners take before delivery and compare delay windows against xG, goals, outcomes, and team behaviour.",
)

if df.empty:
    st.warning("No data loaded")
else:
    delay_col = _find_column(df, ["Delay", "delay", "delay_seconds", "Delay_seconds"])
    team_col = _find_column(df, ["Team", "team", "team_name"])
    xg_col = _find_column(df, ["xg", "XG", "shot.statsbomb_xg", "shot_statsbomb_xg"])
    outcome_col = _find_column(df, ["Shot outcome", "shot.outcome.name", "Outcome", "outcome"])
    match_col = _find_column(df, ["match_id", "Match", "match"])

    st.sidebar.header("Filters")

    if team_col:
        team = st.sidebar.selectbox("Team", ["All"] + sorted(df[team_col].dropna().astype(str).unique().tolist()))
        if team != "All":
            df = df[df[team_col].astype(str) == team].copy()

    if delay_col:
        df[delay_col] = pd.to_numeric(df[delay_col], errors="coerce")
        df = df[df[delay_col].notna()].copy()
        if not df.empty:
            lo = float(df[delay_col].min())
            hi = float(df[delay_col].max())
            delay_range = st.sidebar.slider("Delay range (s)", min_value=float(lo), max_value=float(hi), value=(float(lo), float(hi)))
            df = df[df[delay_col].between(delay_range[0], delay_range[1])].copy()

    if xg_col:
        df[xg_col] = pd.to_numeric(df[xg_col], errors="coerce").fillna(0)

    goals = 0
    if outcome_col:
        goals = int(df[outcome_col].astype(str).str.lower().eq("goal").sum())

    total_rows = len(df)
    avg_delay = float(df[delay_col].mean()) if delay_col and not df.empty else 0.0
    avg_xg = float(df[xg_col].mean()) if xg_col and not df.empty else 0.0
    total_xg = float(df[xg_col].sum()) if xg_col and not df.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Events", total_rows)
    c2.metric("Average Delay", f"{avg_delay:.2f}s")
    c3.metric("Average xG", f"{avg_xg:.3f}")
    c4.metric("Goals", goals)

    if delay_col and xg_col and not df.empty:
        # Delay buckets
        bucket_labels = ["0-5s", "5-10s", "10-15s", "15-20s", "20s+"]
        bins = [-0.001, 5, 10, 15, 20, 10_000]
        df["Delay bucket"] = pd.cut(df[delay_col], bins=bins, labels=bucket_labels)

        bucket_summary = (
            df.groupby("Delay bucket", dropna=False)
            .agg(
                Events=(delay_col, "size"),
                Avg_Delay=(delay_col, "mean"),
                Avg_xG=(xg_col, "mean"),
                Total_xG=(xg_col, "sum"),
            )
            .reset_index()
        )

        if outcome_col:
            goals_by_bucket = (
                df.assign(IsGoal=df[outcome_col].astype(str).str.lower().eq("goal"))
                .groupby("Delay bucket", dropna=False)["IsGoal"]
                .sum()
                .reset_index(name="Goals")
            )
            bucket_summary = bucket_summary.merge(goals_by_bucket, on="Delay bucket", how="left")
            bucket_summary["Goals"] = bucket_summary["Goals"].fillna(0).astype(int)
        else:
            bucket_summary["Goals"] = 0

        section_header("Delay Impact Summary", "Buckets compare volume, xG, and goals")
        st.dataframe(bucket_summary, width="stretch", hide_index=True)

        col1, col2 = st.columns(2)

        with col1:
            section_header("Delay Distribution")
            fig = px.histogram(df, x=delay_col, nbins=20, color_discrete_sequence=["#c1121f"])
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            st.plotly_chart(polish_plotly_figure(fig), width="stretch")

        with col2:
            section_header("Delay vs xG")
            scatter = px.scatter(
                df,
                x=delay_col,
                y=xg_col,
                color=team_col if team_col else None,
                hover_data=[c for c in [team_col, outcome_col, match_col] if c],
                trendline=None,
                color_discrete_sequence=["#c1121f", "#0b0f14", "#2563eb", "#16a34a", "#f59e0b"],
            )
            scatter.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            st.plotly_chart(polish_plotly_figure(scatter), width="stretch")

        col3, col4 = st.columns(2)

        with col3:
            section_header("Average xG by Delay")
            bar = px.bar(bucket_summary, x="Delay bucket", y="Avg_xG", color_discrete_sequence=["#c1121f"])
            bar.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            st.plotly_chart(polish_plotly_figure(bar), width="stretch")

        with col4:
            if team_col:
                section_header("Delay by Team")
                box = px.box(df, x=team_col, y=delay_col, color_discrete_sequence=["#c1121f"])
                box.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                st.plotly_chart(polish_plotly_figure(box), width="stretch")
            else:
                section_header("Total xG by Delay")
                bar2 = px.bar(bucket_summary, x="Delay bucket", y="Total_xG", color_discrete_sequence=["#c1121f"])
                bar2.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                st.plotly_chart(polish_plotly_figure(bar2), width="stretch")

        if outcome_col:
            section_header("Outcome Mix by Delay")
            outcome_mix = (
                df.groupby(["Delay bucket", outcome_col], dropna=False)
                .size()
                .reset_index(name="Count")
            )
            outcome_fig = px.bar(
                outcome_mix,
                x="Delay bucket",
                y="Count",
                color=outcome_col,
                barmode="stack",
                color_discrete_sequence=["#c1121f", "#0b0f14", "#2563eb", "#16a34a", "#f59e0b"],
            )
            outcome_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            st.plotly_chart(polish_plotly_figure(outcome_fig), width="stretch")

    else:
        st.info("This file does not include both a delay column and an xG column, so advanced delay-vs-outcome charts could not be created.")

        if delay_col:
            col1, col2 = st.columns(2)
            with col1:
                section_header("Delay Distribution")
                fig = px.histogram(df, x=delay_col, nbins=20, color_discrete_sequence=["#c1121f"])
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                st.plotly_chart(polish_plotly_figure(fig), width="stretch")
            with col2:
                if team_col:
                    section_header("Delay by Team")
                    fig2 = px.box(df, x=team_col, y=delay_col, color_discrete_sequence=["#c1121f"])
                    fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
                    st.plotly_chart(polish_plotly_figure(fig2), width="stretch")

    section_header("Raw Data", f"{len(df):,} rows in the current filter")
    st.dataframe(df, width="stretch", hide_index=True)
