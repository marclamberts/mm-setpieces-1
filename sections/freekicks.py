"""Freekicks section — tabbed layout with Compare tab."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_freekick_brief_data,
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
    freekick_sequence_summary,
    freekick_zone_summary,
    freekick_taker_summary,
    freekick_shooter_summary,
    freekick_origin_map_figure,
    shotmap_figure,
    starting_location_map_figure,
    set_piece_kpi_values,
    categorical_breakdown_figure,
    minute_distribution_figure,
    build_match_log,
)

from sections._shared import (
    _safe_sorted,
    _fmt_num,
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


def render_freekicks() -> None:
    label = "Freekicks"
    df = _with_match_names(load_prepared_freekick_brief_data(DATA_VERSION))
    hero_block("Set pieces", label, "Indirect free kick sequences, zones, takers, and shot creation.")
    if df.empty:
        st.warning("No freekick rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    teams = _set_piece_team_options(df)
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []

    league = _league_selectbox("League", leagues, key="freekicks_league")
    team = st.sidebar.selectbox("Team", teams, key="freekicks_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key="freekicks_perspective")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key="freekicks_sample")
    taker_filter: list = []
    with st.sidebar.expander("More filters", expanded=False):
        taker_filter = st.multiselect("Taker", takers, key="freekicks_taker")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10].copy()
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()

    sequences = freekick_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Sample", sample), ("Taker", taker_filter),
    ]

    render_export_controls(filtered, "freekicks", label)
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
        avg_actions = float(sequences["Actions"].mean()) if not sequences.empty else 0.0
        direct_threat = float((sequences["Zone"].eq("Direct threat")).mean() * 100) if not sequences.empty else 0.0
        wide_delivery = float((sequences["Zone"].eq("Wide delivery")).mean() * 100) if not sequences.empty else 0.0
        best_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sequences", seq_count)
        c2.metric("Avg actions", f"{avg_actions:.1f}")
        c3.metric("Direct threat", f"{direct_threat:.1f}%")
        c4.metric("Wide delivery", f"{wide_delivery:.1f}%")
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
            render_analyst_table(freekick_zone_summary(filtered).head(12), height=330)

    # ── Sequences ─────────────────────────────────────────────────────────────
    with tab_sequences:
        section_header("Priority sequences", "Ranked by xG — highest-threat FK sequences")
        base_cols = ["Match", "Team", "Minute", "Zone", "Channel", "Initial taker", "Initial height",
                     "Actions", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
        priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
        render_analyst_table(priority.head(40), height=480)

        section_header("Channel mix")
        if not sequences.empty and "Channel" in sequences.columns:
            mix = sequences.groupby("Channel", dropna=False).size().reset_index(name="Sequences")
            fig = bar_chart(mix.sort_values("Sequences", ascending=False), x="Channel", y="Sequences", color="Channel")
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            render_plotly_visual(polish_plotly_figure(fig), "Freekicks channel mix", "freekicks_mix_png")

    # ── Pitch ─────────────────────────────────────────────────────────────────
    with tab_pitch:
        section_header("FK origin map", "Where free kicks are taken from")
        render_mpl_visual(freekick_origin_map_figure(filtered), "Freekick origin map", "freekicks_origin_map_png")

        section_header("Start locations and shot map")
        p1, p2 = st.columns(2)
        with p1:
            render_plotly_visual(
                polish_plotly_figure(starting_location_map_figure(filtered, f"{label} start locations")),
                f"{label} start locations", "freekicks_start_locations_png",
            )
        with p2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(filtered, f"{label} shot map")),
                f"{label} shot map", "freekicks_shot_map_png",
            )

    # ── Roles ─────────────────────────────────────────────────────────────────
    with tab_roles:
        section_header("Taker summary")
        render_analyst_table(freekick_taker_summary(filtered).head(25), height=420)
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top FK takers", top_n=12, color="#c1121f"),
            "Freekicks top takers", "freekicks_top_takers_png",
        )
        section_header("Shooter summary")
        render_analyst_table(freekick_shooter_summary(filtered).head(25), height=420)

    # ── Trends ────────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution")
        render_plotly_visual(minute_distribution_figure(filtered, "FK minute distribution"), "FK minute distribution", "freekicks_minute_png")
        section_header("Match log")
        match_log = build_match_log(filtered)
        if not match_log.empty:
            render_analyst_table(match_log, height=420)
        else:
            st.info("No match-level log available for this filter.")

    # ── Compare ───────────────────────────────────────────────────────────────
    with tab_compare:
        section_header("Team comparison", "Side-by-side FK metrics")
        all_teams = sorted({str(t) for t in df["Team"].dropna().unique()} if "Team" in df.columns else [])
        if len(all_teams) < 2:
            st.info("Need at least two teams in the data.")
        else:
            col_a, col_b = st.columns(2)
            team_a = col_a.selectbox("Team A", all_teams, key="fk_cmp_a")
            team_b = col_b.selectbox("Team B", [t for t in all_teams if t != team_a], key="fk_cmp_b")

            df_a = df[df["Team"].astype(str).eq(team_a)].copy()
            df_b = df[df["Team"].astype(str).eq(team_b)].copy()
            kpi_a = set_piece_kpi_values(df_a)
            kpi_b = set_piece_kpi_values(df_b)

            section_header(f"{team_a}  vs  {team_b}")
            hdr, ca, cb = st.columns([2, 1, 1])
            hdr.markdown("**Metric**"); ca.markdown(f"**{team_a}**"); cb.markdown(f"**{team_b}**")
            st.divider()
            _kpi_compare_row("FK sequences", kpi_a["restarts"], kpi_b["restarts"], "{:,}")
            _kpi_compare_row("Shots", kpi_a["shots"], kpi_b["shots"], "{:,}")
            _kpi_compare_row("Goals", kpi_a["goals"], kpi_b["goals"], "{:,}")
            _kpi_compare_row("xG", kpi_a["total_xg"], kpi_b["total_xg"], "{:.2f}")
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.1f}")
            _kpi_compare_row("xG / 100", kpi_a["xg_per_100"], kpi_b["xg_per_100"], "{:.2f}")

            st.divider()
            section_header("Origin maps")
            mc1, mc2 = st.columns(2)
            with mc1:
                st.caption(f"**{team_a}**")
                render_mpl_visual(freekick_origin_map_figure(df_a), f"{team_a} FK origins", "fk_cmp_a_origin")
            with mc2:
                st.caption(f"**{team_b}**")
                render_mpl_visual(freekick_origin_map_figure(df_b), f"{team_b} FK origins", "fk_cmp_b_origin")

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
