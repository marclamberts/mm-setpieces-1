"""League Comparison section — tabbed layout."""
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
    _league_comparison_source,
    _league_summary_table,
    _league_phase_summary_table,
    _league_set_piece_difference_table,
    _apply_team_perspective,
    bar_chart,
    render_plotly_visual,
    set_section,
)


@st.cache_data(show_spinner="Loading data…")
def _lc_datasets(_data_version: str = DATA_VERSION):
    corners = _with_match_names(load_prepared_sp_data("Corners", _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_data_version))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _data_version))
    return corners, freekicks, throwins


def _build_team_sp_table(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()
    all_teams_in_df = [t for t in df["Team"].dropna().astype(str).unique() if t.strip() and t not in ("Unknown", "nan")]
    corner_df = df[df["Phase"].eq("Corners")] if "Phase" in df.columns else pd.DataFrame()
    rows = []
    for team in sorted(all_teams_in_df):
        sp_for = df[df["Team"].astype(str).eq(team)]
        c_for  = corner_df[corner_df["Team"].astype(str).eq(team)] if not corner_df.empty else pd.DataFrame()
        sp_vs  = _apply_team_perspective(df, team, "Against")
        c_vs   = _apply_team_perspective(corner_df, team, "Against") if not corner_df.empty else pd.DataFrame()

        sp_n   = max(len(sp_for), 1)
        c_n    = max(len(c_for), 1)
        vs_n   = max(len(sp_vs), 1)
        c_vs_n = max(len(c_vs), 1)

        goals_for = int(sp_for["is_goal"].sum()) if not sp_for.empty and "is_goal" in sp_for.columns else 0
        goals_vs  = int(sp_vs["is_goal"].sum()) if not sp_vs.empty and "is_goal" in sp_vs.columns else 0
        xg_for    = float(sp_for["xg"].fillna(0).sum()) if not sp_for.empty and "xg" in sp_for.columns else 0.0
        xg_vs     = float(sp_vs["xg"].fillna(0).sum()) if not sp_vs.empty and "xg" in sp_vs.columns else 0.0
        xg_c_for  = float(c_for["xg"].fillna(0).sum()) if not c_for.empty and "xg" in c_for.columns else 0.0
        xg_c_vs   = float(c_vs["xg"].fillna(0).sum()) if not c_vs.empty and "xg" in c_vs.columns else 0.0

        rows.append({
            "Team":                    team,
            "SP Goals":                goals_for,
            "SP Goals Conceded":       goals_vs,
            "SP xG":                   round(xg_for, 2),
            "SP xG Conceded":          round(xg_vs, 2),
            "SP xG / 100":             round(xg_for / sp_n * 100, 2),
            "SP xG / 100 Conceded":    round(xg_vs / vs_n * 100, 2),
            "Corner xG / corner":      round(xg_c_for / c_n, 3),
            "Corner xG / corner Conc": round(xg_c_vs / c_vs_n, 3),
            "Set Pieces":              len(sp_for),
            "Corners":                 len(c_for),
        })
    return pd.DataFrame(rows).sort_values("SP xG / 100", ascending=False)


def render_league_comparison() -> None:
    corners, freekicks, throwins = _lc_datasets(DATA_VERSION)
    df = _league_comparison_source(corners, freekicks, throwins)
    if df.empty:
        st.warning("No restart rows were found for league comparison.")
        return

    phases = ["All"] + _safe_sorted(df["Phase"]) if "Phase" in df.columns else ["All"]
    leagues = _safe_sorted(df["League"]) if "League" in df.columns else []
    selected_leagues = leagues
    min_set_pieces = 10
    top_n = min(10, max(3, len(leagues)))
    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        phase = st.selectbox("Phase", phases, key="league_comparison_phase")
    with fc2:
        selected_leagues = st.multiselect("Leagues", leagues, default=leagues, key="league_comparison_leagues")
    with fc3:
        min_set_pieces = st.slider("Min set pieces", 1, 100, 10, key="league_comparison_min_sp")
    with fc4:
        top_n = st.slider("Rows shown", 3, 25, top_n, key="league_comparison_top_n")

    filtered = df.copy()
    if phase != "All" and "Phase" in filtered.columns:
        filtered = filtered[filtered["Phase"].eq(phase)].copy()
    if selected_leagues and "League" in filtered.columns:
        filtered = filtered[filtered["League"].isin(selected_leagues)].copy()

    phase_label = phase if phase != "All" else "All phases"
    hero_block("League comparison", "League Comparison", f"{phase_label} · {len(selected_leagues)} leagues · {len(filtered):,} events")

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
        [("Phase", phase), ("Leagues", selected_leagues), ("Min set pieces", min_set_pieces)],
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

    tab_summary, tab_charts, tab_phase, tab_teams, tab_rows = st.tabs([
        "📊 Summary", "📈 Charts", "🔀 Phase split", "🏆 Teams", "🗃️ Rows"
    ])

    with tab_summary:
        left, right = st.columns([1.2, 1])
        with left:
            section_header("League threat board", "Restart output by competition")
            render_analyst_table(summary.head(top_n), height=460)
        with right:
            section_header("Set piece differences", "xG and goals per restart by phase")
            render_analyst_table(set_piece_differences.head(top_n), height=460)

    with tab_charts:
        chart_left, chart_right = st.columns(2)
        chart_df = summary.head(top_n).sort_values("xG / 100")
        with chart_left:
            section_header("xG / 100", "Shot value per 100 restarts")
            fig = bar_chart(chart_df, x="xG / 100", y="League", orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "League xG per 100", "lc_xg_per_100_png")
        with chart_right:
            section_header("Shot rate %", "Restarts ending in a shot")
            shot_df = summary.head(top_n).sort_values("Shot rate %")
            fig = bar_chart(shot_df, x="Shot rate %", y="League", orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "League shot rate", "lc_shot_rate_png")

        if not set_piece_differences.empty:
            section_header("Set piece edge evidence", "Where corners, FKs, and throw-ins diverge")
            diff_cols = ["League", "Corner xG edge vs indirect FK", "Corner xG edge vs throw-in", "Indirect FK xG edge vs throw-in"]
            diff_chart = set_piece_differences[diff_cols].head(top_n).melt("League", var_name="Difference", value_name="xG edge")
            fig = bar_chart(diff_chart, x="League", y="xG edge", color="Difference", barmode="group")
            fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "League set piece differences", "lc_sp_diff_png")

    with tab_phase:
        section_header("Phase split", "xG / 100 by league and restart type")
        render_analyst_table(phase_summary.sort_values(["xG / 100", "Set pieces"], ascending=False).head(top_n * 3), height=480)

        if not phase_summary.empty:
            phase_chart = phase_summary[phase_summary["League"].isin(summary.head(top_n)["League"])].copy()
            fig = bar_chart(phase_chart, x="League", y="xG / 100", color="Phase", barmode="group")
            fig.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "Phase threat mix", "lc_phase_threat_png")

    with tab_teams:
        section_header("Team comparison", "Set piece output and conceded metrics by team")
        team_table = _build_team_sp_table(filtered, top_n)
        if team_table.empty:
            st.info("No team data available for the current filter.")
        else:
            render_analyst_table(
                team_table.head(top_n * 3), height=520,
                color_cols=["SP Goals", "SP Goals Conceded", "SP xG", "SP xG Conceded",
                            "SP xG / 100", "SP xG / 100 Conceded",
                            "Corner xG / corner", "Corner xG / corner Conc"],
            )

            chart_top = team_table.head(top_n).copy()
            tc1, tc2 = st.columns(2)
            with tc1:
                section_header("Set piece goals — attack vs conceded")
                goals_melt = chart_top[["Team", "SP Goals", "SP Goals Conceded"]].melt(
                    "Team", var_name="Type", value_name="Goals"
                )
                fig_goals = bar_chart(goals_melt, x="Team", y="Goals", color="Type", barmode="group")
                fig_goals.update_layout(height=400, margin=dict(l=8, r=8, t=30, b=8))
                render_plotly_visual(polish_plotly_figure(fig_goals), "SP goals vs conceded", "lc_team_goals_png")
            with tc2:
                section_header("Corner xG — attack vs conceded")
                xg_melt = chart_top[["Team", "Corner xG / corner", "Corner xG / corner Conc"]].melt(
                    "Team", var_name="Type", value_name="xG"
                )
                fig_xg = bar_chart(xg_melt, x="Team", y="xG", color="Type", barmode="group")
                fig_xg.update_layout(height=400, margin=dict(l=8, r=8, t=30, b=8))
                render_plotly_visual(polish_plotly_figure(fig_xg), "Corner xG per corner", "lc_team_corner_xg_png")

    with tab_rows:
        section_header("Raw rows", f"{len(filtered):,} restart events")
        display_cols = [c for c in [
            "League", "Phase", "Match", "Team", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=640)

    section_header("Drill down", "Jump to a detailed section")
    ja1, ja2, ja3, ja4 = st.columns(4)
    if ja1.button("⏱ Delay Analysis", key="lc_jump_delay", use_container_width=True):
        set_section("Delay Analysis")
    if ja2.button("⚽ Corners", key="lc_jump_corners", use_container_width=True):
        set_section("Corners")
    if ja3.button("🎯 Free Kicks", key="lc_jump_freekicks", use_container_width=True):
        set_section("Freekicks")
    if ja4.button("↗ Throw-ins", key="lc_jump_throwins", use_container_width=True):
        set_section("Throw-ins")
