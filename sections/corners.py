"""Corners section — tabbed layout with Compare tab."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    hero_block,
    section_header,
    kpi_row,
    info_panel,
    build_summary_tables,
    build_taker_leaderboard,
    build_shooter_leaderboard,
    build_pattern_library,
    build_match_log,
    categorical_breakdown_figure,
    minute_distribution_figure,
    mplsoccer_delivery_figure,
    mplsoccer_shot_figure,
    mplsoccer_delivery_sp_outcome_figure,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    generate_set_piece_insights,
    polish_plotly_figure,
    set_piece_kpi_values,
    unique_start_events,
    shotmap_figure,
    starting_location_map_figure,
)

from sections._shared import (
    _safe_sorted,
    _fmt_num,
    _league_filter_options,
    _league_selectbox,
    _set_piece_team_options,
    _apply_team_perspective,
    _cached_report_pdf,
    bar_chart,
    histogram_chart,
    render_plotly_visual,
    render_mpl_visual,
)


# ── Sidebar filters ─────────────────────────────────────────────────────────

def _filter_data(df: pd.DataFrame, key_prefix: str):
    teams = _set_piece_team_options(df)
    leagues = _league_filter_options(df, "Corners")
    sides = ["All"] + _safe_sorted(df["side"]) if "side" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    techniques = _safe_sorted(df["Technique"]) if "Technique" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shot_outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    team = st.sidebar.selectbox("Team", teams, key=f"{key_prefix}_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key=f"{key_prefix}_perspective")
    league = _league_selectbox("League", leagues, key=f"{key_prefix}_league")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key=f"{key_prefix}_sample")

    minute_min, minute_max = 0, 95
    if "minute" in df.columns:
        vals = pd.to_numeric(df["minute"], errors="coerce").dropna()
        if not vals.empty:
            minute_min = int(min(0, vals.min()))
            minute_max = max(95, int(vals.max()))

    side = "All"; time_in_game = "All"; minute_range = (minute_min, minute_max)
    taker_filter: list = []; technique_filter: list = []; height_filter: list = []
    shot_outcome_filter: list = []; only_shots = False

    with st.sidebar.expander("More filters", expanded=False):
        side = st.radio("Side", sides, key=f"{key_prefix}_side")
        time_in_game = st.selectbox("Time in game", periods, key=f"{key_prefix}_period")
        minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key=f"{key_prefix}_minutes")
        taker_filter = st.multiselect("Taker", takers, key=f"{key_prefix}_taker")
        technique_filter = st.multiselect("Technique", techniques, key=f"{key_prefix}_technique")
        height_filter = st.multiselect("Height", heights, key=f"{key_prefix}_height")
        shot_outcome_filter = st.multiselect("Shot outcome", shot_outcomes, key=f"{key_prefix}_outcome")
        only_shots = st.checkbox("Shots only", value=False, key=f"{key_prefix}_shots_only")

    filtered = df.copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10]
    if side != "All" and "side" in filtered.columns:
        filtered = filtered[filtered["side"] == side]
    if time_in_game != "All" and "game_period" in filtered.columns:
        filtered = filtered[filtered["game_period"] == time_in_game]
    if "minute" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["minute"], errors="coerce").between(minute_range[0], minute_range[1])]
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)]
    if technique_filter and "Technique" in filtered.columns:
        filtered = filtered[filtered["Technique"].isin(technique_filter)]
    if height_filter and "Delivery height" in filtered.columns:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)]
    if shot_outcome_filter and "Shot outcome" in filtered.columns:
        filtered = filtered[filtered["Shot outcome"].isin(shot_outcome_filter)]
    if only_shots and "is_shot" in filtered.columns:
        filtered = filtered[filtered["is_shot"]]

    filters = [
        ("Team", team), ("Perspective", perspective if team != "All" else "All"),
        ("League", league), ("Sample", sample), ("Side", side), ("Period", time_in_game),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Taker", taker_filter), ("Technique", technique_filter),
        ("Height", height_filter), ("Shot outcome", shot_outcome_filter),
        ("Shot only", "Yes" if only_shots else "All"),
    ]
    return filtered, filters, team, league


# ── Compare helpers ──────────────────────────────────────────────────────────

def _kpi_compare_row(label: str, val_a, val_b, fmt: str = "{:.1f}") -> None:
    better_a = val_a >= val_b if isinstance(val_a, (int, float)) else None
    def _f(v):
        try: return fmt.format(v)
        except Exception: return str(v)
    ca, cb, cc = st.columns([2, 1, 1])
    ca.markdown(f"**{label}**")
    cb.markdown(f"{'🟢 ' if better_a is True else ''}{_f(val_a)}")
    cc.markdown(f"{'🟢 ' if better_a is False else ''}{_f(val_b)}")


def _team_kpis(df: pd.DataFrame, team: str) -> dict:
    sub = df[df["Team"].astype(str).eq(team)].copy() if team != "All" and "Team" in df.columns else df
    return set_piece_kpi_values(sub)


# ── Main render ──────────────────────────────────────────────────────────────

def render_corners() -> None:
    label = "Corners"
    df = load_prepared_sp_data(label, DATA_VERSION)
    hero_block("Set pieces", label, "Corner delivery, shot creation, patterns, and role breakdown.")
    if df.empty:
        st.warning("No corner rows were found.")
        return

    filtered, filters, selected_team, selected_league = _filter_data(df, "corners")
    render_export_controls(filtered, label, label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    scope = selected_team if selected_team != "All" else selected_league if selected_league != "All" else "All teams"

    tab_overview, tab_delivery, tab_roles, tab_patterns, tab_trends, tab_compare, tab_report, tab_rows = st.tabs([
        "📊 Overview", "🎯 Delivery", "👤 Roles", "🔁 Patterns", "📈 Trends", "⚖️ Compare", "📋 Report", "🗃️ Rows"
    ])

    # ── Overview ────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(filtered)
        info_panel(filtered)

        summary, technique_mix, outcome_mix = build_summary_tables(filtered)
        section_header(f"{scope} — Summary tables")
        c1, c2, c3 = st.columns([1.35, 1, 1])
        with c1:
            st.caption("Teams")
            render_analyst_table(summary.head(15), height=320)
        with c2:
            st.caption("Technique × Height")
            render_analyst_table(technique_mix.head(15), height=320)
        with c3:
            st.caption("Delivery × Shot outcome")
            render_analyst_table(outcome_mix.head(15), height=320)

        section_header("Key insights")
        cols = st.columns(2)
        for idx, insight in enumerate(generate_set_piece_insights(filtered, label)[:6]):
            with cols[idx % 2]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

    # ── Delivery ────────────────────────────────────────────────────────────
    with tab_delivery:
        section_header("Delivery maps", "Where corners land and what happens")
        d1, d2 = st.columns(2)
        with d1:
            render_mpl_visual(mplsoccer_delivery_figure(filtered, label), "Corners delivery map", "corners_delivery_map_png")
        with d2:
            render_mpl_visual(mplsoccer_shot_figure(filtered, label), "Corners shot quality", "corners_shot_quality_png")
        render_mpl_visual(mplsoccer_delivery_sp_outcome_figure(filtered, label), "Corners delivery SP outcomes", "corners_delivery_sp_outcomes_png")

        section_header("Shot map")
        render_plotly_visual(
            polish_plotly_figure(shotmap_figure(filtered, f"{scope} — corner shot map")),
            "Corners shot map", "corners_shot_map_png",
        )

        section_header("Technique and height breakdown")
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Technique", "Technique", top_n=8, color="#111827"), "Corners technique", "corners_technique_png")
        with ch2:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Delivery height", "Height", top_n=8, color="#1d4ed8"), "Corners height", "corners_height_png")
        with ch3:
            render_plotly_visual(categorical_breakdown_figure(filtered, "side", "Side", top_n=6, color="#c1121f"), "Corners side", "corners_side_png")

    # ── Roles ────────────────────────────────────────────────────────────────
    with tab_roles:
        section_header("Taker leaderboard")
        render_analyst_table(build_taker_leaderboard(filtered).head(25), height=420)

        section_header("Shooter leaderboard")
        render_analyst_table(build_shooter_leaderboard(filtered).head(25), height=420)

        section_header("Top takers chart")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top takers", top_n=12, color="#c1121f"),
            "Corners top takers", "corners_top_takers_png",
        )
        section_header("Shot outcomes by player")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Shot outcome", "Shot outcomes", top_n=10, color="#1d4ed8"),
            "Corners shot outcomes", "corners_shot_outcomes_png",
        )

    # ── Patterns ─────────────────────────────────────────────────────────────
    with tab_patterns:
        section_header("Pattern library", "Technique × height × outcome combinations")
        render_analyst_table(build_pattern_library(filtered).head(40), height=480)

        section_header("Delivery outcome breakdown")
        if "Delivery outcome" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Delivery outcome", "Delivery outcomes", top_n=12, color="#15803d"),
                "Corners delivery outcomes", "corners_delivery_outcomes_png",
            )
        else:
            st.info("No delivery outcome column in this dataset.")

    # ── Trends ───────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution", "When corners are taken through the match")
        render_plotly_visual(minute_distribution_figure(filtered, "Minute distribution"), "Corners minute distribution", "corners_minute_distribution_png")

        if "match_rank" in filtered.columns and filtered["match_rank"].notna().any():
            section_header("Recent form", "xG and shots across last matches")
            match_log = build_match_log(filtered)
            if not match_log.empty:
                render_analyst_table(match_log, height=420)
        else:
            section_header("Match log")
            match_log = build_match_log(filtered)
            if not match_log.empty:
                render_analyst_table(match_log, height=420)
            else:
                st.info("No match-level log available for this filter.")

    # ── Compare ──────────────────────────────────────────────────────────────
    with tab_compare:
        section_header("Team comparison", "Side-by-side corner metrics for two teams")
        all_teams = sorted({str(t) for t in df["Team"].dropna().unique()} if "Team" in df.columns else [])
        if len(all_teams) < 2:
            st.info("Need at least two teams in the data to compare.")
        else:
            col_a, col_b = st.columns(2)
            team_a = col_a.selectbox("Team A", all_teams, key="corners_cmp_a")
            team_b = col_b.selectbox("Team B", [t for t in all_teams if t != team_a], key="corners_cmp_b")

            df_a = df[df["Team"].astype(str).eq(team_a)].copy()
            df_b = df[df["Team"].astype(str).eq(team_b)].copy()
            kpi_a = _team_kpis(df, team_a)
            kpi_b = _team_kpis(df, team_b)

            section_header(f"{team_a}  vs  {team_b}")
            hdr, ca, cb = st.columns([2, 1, 1])
            hdr.markdown("**Metric**")
            ca.markdown(f"**{team_a}**")
            cb.markdown(f"**{team_b}**")
            st.divider()
            _kpi_compare_row("Corners", kpi_a["restarts"], kpi_b["restarts"], "{:,}")
            _kpi_compare_row("Shots", kpi_a["shots"], kpi_b["shots"], "{:,}")
            _kpi_compare_row("Goals", kpi_a["goals"], kpi_b["goals"], "{:,}")
            _kpi_compare_row("xG", kpi_a["total_xg"], kpi_b["total_xg"], "{:.2f}")
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.1f}")
            _kpi_compare_row("xG / 100", kpi_a["xg_per_100"], kpi_b["xg_per_100"], "{:.2f}")
            _kpi_compare_row("xG / shot", kpi_a["xg_per_shot"], kpi_b["xg_per_shot"], "{:.3f}")
            _kpi_compare_row("Goal conv %", kpi_a["goal_conversion"], kpi_b["goal_conversion"], "{:.1f}")

            st.divider()
            section_header("Delivery maps")
            mc1, mc2 = st.columns(2)
            with mc1:
                st.caption(f"**{team_a}**")
                if df_a.empty:
                    st.info("No data for Team A.")
                else:
                    render_mpl_visual(mplsoccer_delivery_figure(df_a, team_a), f"{team_a} delivery", "corners_cmp_a_delivery")
            with mc2:
                st.caption(f"**{team_b}**")
                if df_b.empty:
                    st.info("No data for Team B.")
                else:
                    render_mpl_visual(mplsoccer_delivery_figure(df_b, team_b), f"{team_b} delivery", "corners_cmp_b_delivery")

            section_header("Taker comparison")
            tc1, tc2 = st.columns(2)
            with tc1:
                render_analyst_table(build_taker_leaderboard(df_a).head(10), height=300)
            with tc2:
                render_analyst_table(build_taker_leaderboard(df_b).head(10), height=300)

    # ── Report ───────────────────────────────────────────────────────────────
    with tab_report:
        section_header("Pre-match PDF brief")
        pdf_teams = ["All"] + _safe_sorted(filtered["Team"]) if "Team" in filtered.columns else ["All"]
        if st.session_state.get("corners_pdf_team") not in pdf_teams:
            st.session_state["corners_pdf_team"] = "All"
        pdf_team = st.selectbox("Report team", pdf_teams, key="corners_pdf_team")
        opponent = st.text_input("Opponent / label for report filename", value="", key="corners_pdf_label")
        pdf_filtered = filtered[filtered["Team"].astype(str).eq(pdf_team)].copy() if pdf_team != "All" and "Team" in filtered.columns else filtered.copy()
        pdf_label = f"Corners – {pdf_team}" if pdf_team != "All" else "Corners"
        safe_name = (opponent.strip() or pdf_label).lower().replace(" ", "_").replace("/", "-")
        st.info("PDF generation may take a few seconds on large datasets.")
        st.download_button(
            "⬇ Download pre-match PDF",
            data=_cached_report_pdf(pdf_filtered, pdf_label, opponent.strip()),
            file_name=f"{safe_name}_corners_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # ── Rows ─────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("Raw rows", f"{len(filtered):,} events in current filter")
        display_cols = [c for c in [
            "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
            "Defensive_setup", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob",
            "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=560)
