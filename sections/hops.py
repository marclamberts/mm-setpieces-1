"""HOPS section — tabbed layout with Compare tab."""
from __future__ import annotations

import streamlit as st
import pandas as pd

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
    render_plotly_visual,
)


def _rating_delta_color(delta: float) -> str:
    if delta > 0.05: return "🟢"
    if delta < -0.05: return "🔴"
    return "⬜"


def render_hops() -> None:
    df = load_hops_data(DATA_VERSION)
    hero_block("Players", "HOPS", "Heading and duel profile ratings — individual and squad-level views.")
    if df.empty:
        st.warning("No HOPS rows were found in Data/HOPS.")
        return

    leagues = _league_filter_options(df, "HOPS")
    teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
    league = _league_selectbox("League", leagues, key="hops_league")
    team = st.sidebar.selectbox("Team", teams, key="hops_team")
    with st.sidebar.expander("More filters", expanded=False):
        top_n = st.slider("Leaderboard rows", min_value=5, max_value=50, value=15, key="hops_top_n")
        tier_filter = st.multiselect("Tier", ["Elite", "Strong", "Rotation", "Depth"], key="hops_tier")

    filtered = df.copy()
    if league != "All":
        filtered = filtered[filtered["League"] == league].copy()
    if team != "All":
        filtered = filtered[filtered["Team"] == team].copy()
    if tier_filter:
        filtered = filtered[filtered["Tier"].isin(tier_filter)].copy()

    render_export_controls(filtered, "hops", "HOPS")
    render_filter_summary("HOPS", len(df), len(filtered), [
        ("League", league), ("Team", team),
        ("Tier", tier_filter), ("Rows", f"Top/bottom {top_n}"),
    ])
    if filtered.empty:
        render_empty_filter_state()
        return

    player_count = int(filtered["Player"].nunique())
    team_count = int(filtered["Team"].nunique())
    avg_rating = float(filtered["Rating"].mean())
    best_rating = float(filtered["Rating"].max())
    elite_count = int((filtered["Tier"] == "Elite").sum()) if "Tier" in filtered.columns else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Players", player_count)
    c2.metric("Teams", team_count)
    c3.metric("Avg rating", f"{avg_rating:.3f}")
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

    tab_summary, tab_charts, tab_compare, tab_rows = st.tabs([
        "📊 Summary", "📈 Charts", "⚖️ Compare", "🗃️ Rows"
    ])

    # ── Summary ───────────────────────────────────────────────────────────────
    with tab_summary:
        left, right = st.columns([1.15, 1])
        with left:
            section_header("Team duel board", "Average rating and high-end profiles by squad")
            render_analyst_table(team_summary, height=430)
        with right:
            section_header("Priority profiles", f"Top {top_n} in filter")
            render_analyst_table(top_players, height=430)

        section_header("Lowest ratings", "Bottom of the filter — defensive risk check")
        render_analyst_table(bottom_players, height=300)

    # ── Charts ────────────────────────────────────────────────────────────────
    with tab_charts:
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Top rating evidence")
            chart_df = filtered.nlargest(min(20, len(filtered)), "Rating").sort_values("Rating")
            fig = bar_chart(chart_df, x="Rating", y="Player", color="Team", orientation="h")
            fig.update_layout(height=560, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "HOPS top rating evidence", "hops_top_rating_evidence_png")
        with chart_right:
            section_header("Rating distribution")
            hist = histogram_chart(filtered, "Rating", color="Tier", nbins=25)
            hist.update_layout(height=560, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(hist), "HOPS rating distribution", "hops_rating_distribution_png")

        section_header("Squad depth by tier")
        if "Tier" in team_summary.columns:
            tier_data = filtered.groupby(["Team", "Tier"], dropna=False).size().reset_index(name="Count")
            fig = bar_chart(tier_data, x="Team", y="Count", color="Tier", barmode="stack")
            fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="Tier")
            render_plotly_visual(polish_plotly_figure(fig), "HOPS tier depth", "hops_tier_depth_png")

    # ── Compare ───────────────────────────────────────────────────────────────
    with tab_compare:
        section_header("Squad comparison", "Head-to-head rating profiles for two teams")
        all_teams = sorted(df["Team"].dropna().astype(str).unique().tolist())
        if len(all_teams) < 2:
            st.info("Need at least two teams.")
        else:
            col_a, col_b = st.columns(2)
            team_a = col_a.selectbox("Team A", all_teams, key="hops_cmp_a")
            team_b = col_b.selectbox("Team B", [t for t in all_teams if t != team_a], key="hops_cmp_b")

            sq_a = df[df["Team"].astype(str).eq(team_a)].sort_values("Rating", ascending=False)
            sq_b = df[df["Team"].astype(str).eq(team_b)].sort_values("Rating", ascending=False)

            hdr, ca, cb = st.columns([2, 1, 1])
            hdr.markdown("**Metric**"); ca.markdown(f"**{team_a}**"); cb.markdown(f"**{team_b}**")
            st.divider()

            def _cmp(label, va, vb, fmt="{:.3f}"):
                better = va >= vb
                h, a, b = st.columns([2, 1, 1])
                h.markdown(f"**{label}**")
                a.markdown(f"{'🟢 ' if better else ''}{fmt.format(va)}")
                b.markdown(f"{'🟢 ' if not better else ''}{fmt.format(vb)}")

            avg_a = float(sq_a["Rating"].mean()) if not sq_a.empty else 0.0
            avg_b = float(sq_b["Rating"].mean()) if not sq_b.empty else 0.0
            best_a = float(sq_a["Rating"].max()) if not sq_a.empty else 0.0
            best_b = float(sq_b["Rating"].max()) if not sq_b.empty else 0.0
            elite_a = int((sq_a["Tier"] == "Elite").sum()) if not sq_a.empty else 0
            elite_b = int((sq_b["Tier"] == "Elite").sum()) if not sq_b.empty else 0

            _cmp("Players", len(sq_a), len(sq_b), "{:,}")
            _cmp("Avg rating", avg_a, avg_b)
            _cmp("Best rating", best_a, best_b)
            _cmp("Elite profiles", elite_a, elite_b, "{:,}")

            st.divider()
            section_header("Player rosters")
            rc1, rc2 = st.columns(2)
            with rc1:
                st.caption(f"**{team_a}** — {len(sq_a)} players")
                render_analyst_table(sq_a[["Player", "Rating", "Percentile", "Tier"]].head(20), height=380)
            with rc2:
                st.caption(f"**{team_b}** — {len(sq_b)} players")
                render_analyst_table(sq_b[["Player", "Rating", "Percentile", "Tier"]].head(20), height=380)

            section_header("Rating distributions")
            dist_l, dist_r = st.columns(2)
            with dist_l:
                fig_a = histogram_chart(sq_a, "Rating", nbins=15)
                fig_a.update_layout(title=team_a, height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig_a), f"{team_a} distribution", "hops_cmp_a_dist")
            with dist_r:
                fig_b = histogram_chart(sq_b, "Rating", nbins=15)
                fig_b.update_layout(title=team_b, height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig_b), f"{team_b} distribution", "hops_cmp_b_dist")

    # ── Rows ──────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("All profiles", f"{len(filtered):,} players")
        render_analyst_table(
            filtered.sort_values("Rating", ascending=False)[["Player", "Team", "League", "Rating", "Percentile", "Tier"]],
            height=660,
        )
