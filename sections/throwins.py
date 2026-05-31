"""Throw-ins section — tabbed layout with Compare tab."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    render_analyst_table,
    hero_block,
    section_header,
    kpi_row,
    info_panel,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    generate_set_piece_insights,
    polish_plotly_figure,
    throwin_sequence_summary,
    throwin_zone_summary,
    throwin_taker_summary,
    throwin_shooter_summary,
    throwin_delivery_map_figure,
    throwin_outcome_zone_figure,
    shotmap_figure,
    starting_location_map_figure,
    set_piece_kpi_values,
    categorical_breakdown_figure,
    minute_distribution_figure,
    build_match_log,
)

from sections._shared import (
    _safe_sorted,
    _league_filter_options,
    _league_selectbox,
    _set_piece_team_options,
    _apply_team_perspective,
    _with_match_names,
    bar_chart,
    render_plotly_visual,
    render_mpl_visual,
)


def _kpi_compare_row(label: str, val_a, val_b, fmt: str = "{:.1f}") -> None:
    def _f(v):
        try: return fmt.format(v)
        except Exception: return str(v)
    better_a = val_a >= val_b if isinstance(val_a, (int, float)) else None
    ca, cb, cc = st.columns([2, 1, 1])
    ca.markdown(f"**{label}**")
    cb.markdown(f"{'🟢 ' if better_a is True else ''}{_f(val_a)}")
    cc.markdown(f"{'🟢 ' if better_a is False else ''}{_f(val_b)}")


def render_throwins() -> None:
    label = "Throw-ins"
    df = _with_match_names(load_prepared_sp_data("Throw ins", DATA_VERSION))
    hero_block("Set pieces", label, "Throw-in sequences, zone entry, box threat, and personnel breakdown.")
    if df.empty:
        st.warning("No throw-in rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    teams = _set_piece_team_options(df)
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shooters = _safe_sorted(df["Shooter"]) if "Shooter" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    league = _league_selectbox("League", leagues, key="throwins_league")
    team = st.sidebar.selectbox("Team", teams, key="throwins_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key="throwins_perspective")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key="throwins_sample")

    minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min()) if "minute" in df.columns else 0
    minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max())) if "minute" in df.columns else 95

    period = "All"; minute_range = (minute_min, minute_max)
    taker_filter: list = []; shooter_filter: list = []; height_filter: list = []; outcome_filter: list = []

    with st.sidebar.expander("More filters", expanded=False):
        period = st.selectbox("Game period", periods, key="throwins_period")
        minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key="throwins_minutes")
        taker_filter = st.multiselect("Thrower", takers, key="throwins_taker")
        shooter_filter = st.multiselect("Shooter", shooters, key="throwins_shooter")
        height_filter = st.multiselect("Height", heights, key="throwins_height")
        outcome_filter = st.multiselect("Shot outcome", outcomes, key="throwins_outcome")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if period != "All" and "game_period" in filtered.columns:
        filtered = filtered[filtered["game_period"].eq(period)].copy()
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10].copy()
    if "minute" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["minute"], errors="coerce").between(minute_range[0], minute_range[1])].copy()
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()
    if shooter_filter and "Shooter" in filtered.columns:
        filtered = filtered[filtered["Shooter"].isin(shooter_filter)].copy()
    if height_filter and "Delivery height" in filtered.columns:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)].copy()
    if outcome_filter and "Shot outcome" in filtered.columns:
        filtered = filtered[filtered["Shot outcome"].isin(outcome_filter)].copy()

    sequences = throwin_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Period", period), ("Sample", sample),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Thrower", taker_filter), ("Shooter", shooter_filter),
        ("Height", height_filter), ("Shot outcome", outcome_filter),
    ]

    render_export_controls(filtered, "throwins", label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    scope = team if team != "All" else league if league != "All" else "All teams"

    tab_overview, tab_sequences, tab_pitch, tab_roles, tab_trends, tab_compare, tab_rows = st.tabs([
        "📊 Overview", "🔗 Sequences", "🎯 Pitch", "👤 Roles", "📈 Trends", "⚖️ Compare", "🗃️ Rows"
    ])

    # ── Overview ─────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(filtered)
        info_panel(filtered)

        seq_count = len(sequences)
        box_entry = float(sequences["Box entry"].mean() * 100) if not sequences.empty and "Box entry" in sequences.columns else 0.0
        attack_zone = float((sequences["Zone"].eq("Attacking channel")).mean() * 100) if not sequences.empty else 0.0
        shots_total = int(sequences["Shots"].sum()) if not sequences.empty else 0
        best_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sequences", seq_count)
        c2.metric("Box entry %", f"{box_entry:.1f}%")
        c3.metric("Attacking third", f"{attack_zone:.1f}%")
        c4.metric("Shots", shots_total)
        c5.metric("Best seq xG", f"{best_xg:.3f}")

        section_header(f"{scope} — Zone breakdown")
        dash_l, dash_r = st.columns([0.9, 1.3])
        with dash_l:
            insights = generate_set_piece_insights(filtered, label)
            if not sequences.empty:
                top_zone = sequences["Zone"].value_counts().head(1)
                if not top_zone.empty:
                    insights.insert(0, f"Most common zone: {top_zone.index[0].lower()} ({top_zone.iloc[0]} sequences).")
            for insight in insights[:5]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)
        with dash_r:
            render_analyst_table(throwin_zone_summary(filtered).head(12), height=330)

    # ── Sequences ─────────────────────────────────────────────────────────────
    with tab_sequences:
        section_header("Priority sequences", "Ranked by xG — highest-threat throw-in sequences")
        base_cols = ["Match", "Team", "Minute", "Zone", "Side", "Initial taker", "Initial height",
                     "Box entry", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
        priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
        render_analyst_table(priority.head(40), height=480)

        section_header("Box entry % by side")
        if not sequences.empty and "Side" in sequences.columns:
            side_mix = (sequences.groupby("Side", dropna=False)
                        .agg(Sequences=("Side", "size"), Box_entries=("Box entry", "sum"))
                        .reset_index())
            side_mix["Box entry %"] = (side_mix["Box_entries"] / side_mix["Sequences"] * 100).round(1)
            fig = bar_chart(side_mix, x="Side", y="Box entry %", color="Side")
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            render_plotly_visual(polish_plotly_figure(fig), "Box entry % by side", "throwins_side_box_png")

    # ── Pitch ─────────────────────────────────────────────────────────────────
    with tab_pitch:
        section_header("Delivery map")
        render_mpl_visual(throwin_delivery_map_figure(filtered), "Throw-in deliveries", "throwins_delivery_map_png")

        section_header("Outcome zones")
        render_mpl_visual(throwin_outcome_zone_figure(filtered), "Throw-in outcome zones", "throwins_outcome_zones_png")

        section_header("Start locations and shot map")
        p1, p2 = st.columns(2)
        with p1:
            render_plotly_visual(
                polish_plotly_figure(starting_location_map_figure(filtered, f"{label} start locations")),
                f"{label} start locations", "throwins_start_locations_png",
            )
        with p2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(filtered, f"{label} shot map")),
                f"{label} shot map", "throwins_shot_map_png",
            )

    # ── Roles ─────────────────────────────────────────────────────────────────
    with tab_roles:
        section_header("Thrower summary")
        render_analyst_table(throwin_taker_summary(filtered).head(25), height=420)
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top throwers", top_n=12, color="#c1121f"),
            "Throw-in top throwers", "throwins_top_takers_png",
        )
        section_header("Shooter summary")
        render_analyst_table(throwin_shooter_summary(filtered).head(25), height=420)

    # ── Trends ────────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution")
        render_plotly_visual(minute_distribution_figure(filtered, "Throw-in minute distribution"), "Throw-in minute distribution", "throwins_minute_png")
        section_header("Match log")
        match_log = build_match_log(filtered)
        if not match_log.empty:
            render_analyst_table(match_log, height=420)
        else:
            st.info("No match-level log available for this filter.")

    # ── Compare ───────────────────────────────────────────────────────────────
    with tab_compare:
        section_header("Team comparison", "Side-by-side throw-in metrics")
        all_teams = sorted({str(t) for t in df["Team"].dropna().unique()} if "Team" in df.columns else [])
        if len(all_teams) < 2:
            st.info("Need at least two teams in the data.")
        else:
            col_a, col_b = st.columns(2)
            team_a = col_a.selectbox("Team A", all_teams, key="ti_cmp_a")
            team_b = col_b.selectbox("Team B", [t for t in all_teams if t != team_a], key="ti_cmp_b")

            df_a = df[df["Team"].astype(str).eq(team_a)].copy()
            df_b = df[df["Team"].astype(str).eq(team_b)].copy()
            kpi_a = set_piece_kpi_values(df_a)
            kpi_b = set_piece_kpi_values(df_b)

            section_header(f"{team_a}  vs  {team_b}")
            hdr, ca, cb = st.columns([2, 1, 1])
            hdr.markdown("**Metric**"); ca.markdown(f"**{team_a}**"); cb.markdown(f"**{team_b}**")
            st.divider()
            _kpi_compare_row("Sequences", kpi_a["restarts"], kpi_b["restarts"], "{:,}")
            _kpi_compare_row("Shots", kpi_a["shots"], kpi_b["shots"], "{:,}")
            _kpi_compare_row("Goals", kpi_a["goals"], kpi_b["goals"], "{:,}")
            _kpi_compare_row("xG", kpi_a["total_xg"], kpi_b["total_xg"], "{:.2f}")
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.1f}")
            _kpi_compare_row("xG / 100", kpi_a["xg_per_100"], kpi_b["xg_per_100"], "{:.2f}")

            st.divider()
            section_header("Delivery maps")
            mc1, mc2 = st.columns(2)
            with mc1:
                st.caption(f"**{team_a}**")
                render_mpl_visual(throwin_delivery_map_figure(df_a), f"{team_a} deliveries", "ti_cmp_a_map")
            with mc2:
                st.caption(f"**{team_b}**")
                render_mpl_visual(throwin_delivery_map_figure(df_b), f"{team_b} deliveries", "ti_cmp_b_map")

    # ── Rows ──────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("Sequences", f"{len(sequences)} sequences")
        render_analyst_table(sequences, height=360)
        section_header("Raw rows", f"{len(filtered):,} events")
        display_cols = [c for c in [
            "Match", "Team", "Taker", "Shooter", "minute", "second", "pass_x", "pass_y",
            "Delivery height", "Shot outcome", "xg", "Occupation_Rating", "Proximity_Rating",
            "Duel_Win_Prob", "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=480)
