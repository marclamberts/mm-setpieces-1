"""Throw-ins section — maximum analytical depth."""
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
    _cached_report_pdf,
    bar_chart,
    render_plotly_visual,
    render_mpl_visual,
    set_section,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _kpi_compare_row(label: str, val_a, val_b, fmt: str = "{:.2f}") -> None:
    def _f(v):
        try: return fmt.format(v)
        except Exception: return str(v)
    better_a = val_a >= val_b if isinstance(val_a, (int, float)) else None
    ca, cb, cc = st.columns([2, 1, 1])
    ca.markdown(f"**{label}**")
    cb.markdown(f"{'🟢 ' if better_a is True else ''}{_f(val_a)}")
    cc.markdown(f"{'🟢 ' if better_a is False else ''}{_f(val_b)}")


def _side_zone_breakdown(sequences: pd.DataFrame) -> pd.DataFrame:
    if sequences.empty:
        return pd.DataFrame()
    cols = [c for c in ["Zone", "Side"] if c in sequences.columns]
    if not cols:
        return pd.DataFrame()
    agg = (
        sequences.groupby(cols, dropna=False)
        .agg(
            Sequences=(cols[0], "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
        )
        .reset_index()
    )
    if "Box entry" in sequences.columns:
        be = sequences.groupby(cols, dropna=False)["Box entry"].sum().reset_index(name="Box_entries")
        agg = agg.merge(be, on=cols, how="left")
        agg["Box entry %"] = (agg["Box_entries"] / agg["Sequences"] * 100).round(2)
        agg = agg.drop(columns=["Box_entries"])
    agg["Shots / seq"] = (agg["Shots"] / agg["Sequences"]).round(3)
    agg["xG / seq"] = (agg["Total_xG"] / agg["Sequences"]).round(3)
    return agg.sort_values("xG / seq", ascending=False)


def _height_breakdown(sequences: pd.DataFrame) -> pd.DataFrame:
    if sequences.empty or "Initial height" not in sequences.columns:
        return pd.DataFrame()
    agg = (
        sequences.groupby("Initial height", dropna=False)
        .agg(Sequences=("Initial height", "size"), Shots=("Shots", "sum"), Goals=("Goals", "sum"), Total_xG=("Total xG", "sum"))
        .reset_index()
    )
    if "Box entry" in sequences.columns:
        be = sequences.groupby("Initial height", dropna=False)["Box entry"].sum().reset_index(name="Box_entries")
        agg = agg.merge(be, on="Initial height", how="left")
        agg["Box entry %"] = (agg["Box_entries"] / agg["Sequences"] * 100).round(2)
        agg = agg.drop(columns=["Box_entries"])
    agg["xG / seq"] = (agg["Total_xG"] / agg["Sequences"]).round(3)
    return agg.sort_values("xG / seq", ascending=False)


def _minute_band_breakdown(sequences: pd.DataFrame) -> pd.DataFrame:
    if sequences.empty or "Minute" not in sequences.columns:
        return pd.DataFrame()
    seqs = sequences.copy()
    seqs["Minute band"] = pd.cut(
        pd.to_numeric(seqs["Minute"], errors="coerce"),
        bins=[0, 15, 30, 45, 60, 75, 90, 120],
        labels=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"],
        right=True,
    ).astype(str)
    agg = (
        seqs.groupby("Minute band", dropna=False)
        .agg(Sequences=("Minute band", "size"), Shots=("Shots", "sum"), Goals=("Goals", "sum"), Total_xG=("Total xG", "sum"))
        .reset_index()
    )
    if "Box entry" in seqs.columns:
        be = seqs.groupby("Minute band", dropna=False)["Box entry"].sum().reset_index(name="Box_entries")
        agg = agg.merge(be, on="Minute band", how="left")
        agg["Box entry %"] = (agg["Box_entries"] / agg["Sequences"] * 100).round(2)
        agg = agg.drop(columns=["Box_entries"])
    return agg.assign(xG_per_seq=lambda d: (d["Total_xG"] / d["Sequences"]).round(3))


# ── Main render ──────────────────────────────────────────────────────────────

def render_throwins() -> None:
    label = "Throw-ins"
    df = _with_match_names(load_prepared_sp_data("Throw ins", DATA_VERSION))
    if df.empty:
        st.warning("No throw-in rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    _cur_league = st.session_state.get("throwins_league", "All")
    if _cur_league not in leagues:
        _cur_league = "All"
    _df_for_teams = df[df["League"].eq(_cur_league)] if _cur_league != "All" and "League" in df.columns else df
    teams = _set_piece_team_options(_df_for_teams)
    if st.session_state.get("throwins_team", "All") not in teams:
        st.session_state["throwins_team"] = "All"
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    # Throw-in pitch area zones
    TI_AREAS = ["Defensive Third", "Middle Third", "Attacking Third"]
    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shooters = _safe_sorted(df["Shooter"]) if "Shooter" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min()) if "minute" in df.columns else 0
    minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max())) if "minute" in df.columns else 95

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        league = _league_selectbox("League", leagues, key="throwins_league")
    with fc2:
        team = st.selectbox("Team", teams, key="throwins_team")
    with fc3:
        perspective = st.radio("Perspective", ["For", "Against"], horizontal=True, key="throwins_perspective")
    with fc4:
        sample = st.radio("Sample", ["Total", "Last 10"], horizontal=True, key="throwins_sample")

    period = "All"; minute_range = (minute_min, minute_max)
    taker_filter: list = []; shooter_filter: list = []; height_filter: list = []; outcome_filter: list = []
    area_filter: list = []

    with st.expander("More filters", expanded=False):
        mx1, mx2, mx3, mx4 = st.columns(4)
        with mx1:
            period = st.selectbox("Game period", periods, key="throwins_period")
            minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key="throwins_minutes")
        with mx2:
            taker_filter = st.multiselect("Thrower", takers, key="throwins_taker")
            shooter_filter = st.multiselect("Shooter", shooters, key="throwins_shooter")
        with mx3:
            height_filter = st.multiselect("Height", heights, key="throwins_height")
            outcome_filter = st.multiselect("Shot outcome", outcomes, key="throwins_outcome")
        with mx4:
            area_filter = st.multiselect("Pitch area", TI_AREAS, key="throwins_area",
                                         help="Filter throw-ins by pitch third (based on x-coordinate)")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if period != "All" and "game_period" in filtered.columns:
        filtered = filtered[filtered["game_period"].eq(period)].copy()
    if sample == "Last 10" and "match_rank" in filtered.columns:
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
    if area_filter and "pass_x" in filtered.columns:
        import numpy as np
        x_num = pd.to_numeric(filtered["pass_x"], errors="coerce")
        max_x = float(x_num.quantile(0.99)) if not x_num.isna().all() else 120.0
        t1, t2 = max_x * 0.33, max_x * 0.67
        def _area(x):
            if pd.isna(x): return None
            if x < t1: return "Defensive Third"
            if x < t2: return "Middle Third"
            return "Attacking Third"
        filtered = filtered.copy()
        filtered["_ti_area"] = x_num.map(_area)
        filtered = filtered[filtered["_ti_area"].isin(area_filter)].drop(columns=["_ti_area"])

    sequences = throwin_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Period", period), ("Sample", sample),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Thrower", taker_filter), ("Shooter", shooter_filter),
        ("Height", height_filter), ("Shot outcome", outcome_filter),
        ("Pitch area", area_filter),
    ]

    scope_parts = [p for p in [team if team != "All" else None, league if league != "All" else None] if p]
    scope_str = " · ".join(scope_parts) if scope_parts else "All teams"
    hero_block("Set pieces", label, f"{scope_str} · {len(filtered):,} events")

    render_export_controls(filtered, "throwins", label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    scope = team if team != "All" else league if league != "All" else "All teams"

    tabs = st.tabs([
        "📊 Overview", "🔗 Sequences", "🗺️ Zones", "🎯 Pitch",
        "👤 Roles", "📈 Trends", "⚖️ Compare", "📋 Report", "🗃️ Rows",
    ])
    tab_overview, tab_sequences, tab_zones, tab_pitch, tab_roles, tab_trends, tab_compare, tab_report, tab_rows = tabs

    # ── Overview ─────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(filtered)
        info_panel(filtered)

        seq_count = len(sequences)
        box_entry = float(sequences["Box entry"].mean() * 100) if not sequences.empty and "Box entry" in sequences.columns else 0.0
        attack_zone = float((sequences["Zone"].eq("Attacking channel")).mean() * 100) if not sequences.empty and "Zone" in sequences.columns else 0.0
        shots_total = int(sequences["Shots"].sum()) if not sequences.empty else 0
        best_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sequences", seq_count)
        c2.metric("Box entry %", f"{box_entry:.2f}%")
        c3.metric("Attacking third %", f"{attack_zone:.2f}%")
        c4.metric("Shots", shots_total)
        c5.metric("Best seq xG", f"{best_xg:.3f}")

        section_header(f"{scope} — Zone × Side board")
        side_zone = _side_zone_breakdown(sequences)
        render_analyst_table(
            side_zone, height=340,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Box entry %", "xG / seq", "Shots / seq"],
        )

        section_header("Key insights")
        insights = generate_set_piece_insights(filtered, label)
        if not sequences.empty and "Zone" in sequences.columns:
            top_zone = sequences["Zone"].value_counts().head(1)
            if not top_zone.empty:
                insights.insert(0, f"Most common zone: {top_zone.index[0].lower()} ({top_zone.iloc[0]} sequences).")
        cols = st.columns(2)
        for idx, insight in enumerate(insights[:8]):
            with cols[idx % 2]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

    # ── Sequences ─────────────────────────────────────────────────────────────
    with tab_sequences:
        seq_sort = st.radio("Order sequences by", ["Sequence (Minute)", "xG"], horizontal=True, key="throwins_seq_sort")
        section_header("Throw-in sequences")
        base_cols = ["Match", "Team", "Minute", "Zone", "Side", "Initial taker", "Initial height",
                     "Box entry", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
        priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
        if seq_sort == "Sequence (Minute)" and "Minute" in priority.columns:
            priority = priority.sort_values("Minute")
        elif "Total xG" in priority.columns:
            priority = priority.sort_values("Total xG", ascending=False)
        render_analyst_table(
            priority.head(60), height=520,
            color_cols=["Shots", "Goals", "Total xG", "Best shot xG"],
        )

        if not sequences.empty and "Side" in sequences.columns:
            section_header("Box entry % by side")
            side_mix = (
                sequences.groupby("Side", dropna=False)
                .agg(Sequences=("Side", "size"), Box_entries=("Box entry", "sum"))
                .reset_index()
            )
            side_mix["Box entry %"] = (side_mix["Box_entries"] / side_mix["Sequences"] * 100).round(2)
            c1, c2 = st.columns(2)
            with c1:
                fig = bar_chart(side_mix, x="Side", y="Box entry %", color="Side")
                fig.update_layout(showlegend=False, margin=dict(l=8, r=8, t=28, b=8))
                render_plotly_visual(polish_plotly_figure(fig), "Box entry % by side", "throwins_side_box_png")
            with c2:
                render_analyst_table(side_mix, height=200, color_cols=["Box entry %"])

    # ── Zones ─────────────────────────────────────────────────────────────────
    with tab_zones:
        section_header("Zone × Side breakdown", "Sequence output by pitch zone and touchline side")
        zone_df = throwin_zone_summary(filtered)
        render_analyst_table(
            zone_df, height=380,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Avg_xG", "Box entry %", "Shots / seq"],
        )

        if not zone_df.empty:
            zc1, zc2 = st.columns(2)
            label_col = "Zone" if "Zone" in zone_df.columns else zone_df.columns[0]
            with zc1:
                section_header("Box entry % by zone")
                if "Box entry %" in zone_df.columns:
                    fig = bar_chart(zone_df.sort_values("Box entry %"), x="Box entry %", y=label_col, orientation="h")
                    fig.update_traces(marker_color="#4ade80")
                    fig.update_layout(height=360, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                    render_plotly_visual(polish_plotly_figure(fig), "Box entry % by zone", "throwins_zone_box_png")
            with zc2:
                section_header("Sequences by zone")
                fig2 = bar_chart(zone_df.sort_values("Sequences", ascending=False), x="Sequences", y=label_col, orientation="h")
                fig2.update_traces(marker_color="#60a5fa")
                fig2.update_layout(height=360, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig2), "Sequence volume by zone", "throwins_zone_vol_png")

        section_header("Delivery height breakdown")
        render_analyst_table(
            _height_breakdown(sequences), height=260,
            color_cols=["Sequences", "Shots", "Goals", "Box entry %", "xG / seq"],
        )

        section_header("Minute band breakdown")
        render_analyst_table(
            _minute_band_breakdown(sequences), height=280,
            color_cols=["Sequences", "Shots", "Goals", "Box entry %", "xG_per_seq"],
        )

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
                "Start locations", "throwins_start_locations_png",
            )
        with p2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(filtered, f"{scope} — throw-in shots")),
                "Shot map", "throwins_shot_map_png",
            )

        section_header("Height breakdown chart")
        if "Delivery height" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Delivery height", "Delivery height", top_n=8, color="#60a5fa"),
                "Delivery height", "throwins_height_png",
            )

    # ── Roles ─────────────────────────────────────────────────────────────────
    with tab_roles:
        section_header("Thrower summary", "Ranked by box entry rate")
        taker_df = throwin_taker_summary(filtered)
        render_analyst_table(
            taker_df.head(35), height=460,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Avg_xG", "Box entry %", "Shots / seq"],
        )
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top throwers", top_n=15, color="#fca5a5"),
            "Top throwers", "throwins_top_takers_png",
        )

        section_header("Shooter summary", "Ranked by total xG from throw-in sequences")
        shooter_df = throwin_shooter_summary(filtered)
        render_analyst_table(
            shooter_df.head(35), height=440,
            color_cols=["Shots", "Goals", "Total_xG", "Avg_xG", "Best_xG", "Conversion %"],
        )
        if not shooter_df.empty and "Shooter" in shooter_df.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Shooter", "Top shooters", top_n=15, color="#93c5fd"),
                "Top shooters from throw-ins", "throwins_top_shooters_png",
            )

    # ── Trends ────────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution", "When throw-ins are taken across 90 minutes")
        render_plotly_visual(minute_distribution_figure(filtered, "Throw-in minute distribution"), "Minute distribution", "throwins_minute_png")

        if st.button("⏱ Analyse throw-in delivery delays →", key="ti_jump_delay", help="Jump to Delay Analysis"):
            set_section("Delay Analysis")

        section_header("Match log", "Per-match throw-in output")
        match_log = build_match_log(filtered)
        if not match_log.empty:
            render_analyst_table(
                match_log, height=460,
                color_cols=["Events", "Shots", "Goals", "Shot rate %", "Total xG"],
            )
            section_header("xG per match — top 20")
            top_m = match_log.sort_values("Total xG", ascending=False).head(20)
            match_col = "Match" if "Match" in top_m.columns else top_m.columns[0]
            fig = bar_chart(top_m.sort_values("Total xG"), x="Total xG", y=match_col, orientation="h")
            fig.update_traces(marker_color="#60a5fa")
            fig.update_layout(height=480, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "xG per match", "throwins_match_xg_png")
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
            seq_a = throwin_sequence_summary(df_a)
            seq_b = throwin_sequence_summary(df_b)
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
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.2f}")
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

            section_header("Zone × Side comparison")
            zc1, zc2 = st.columns(2)
            with zc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(_side_zone_breakdown(seq_a), height=300, color_cols=["Box entry %", "xG / seq"])
            with zc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(_side_zone_breakdown(seq_b), height=300, color_cols=["Box entry %", "xG / seq"])

            section_header("Thrower comparison")
            tc1, tc2 = st.columns(2)
            with tc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(throwin_taker_summary(df_a).head(12), height=320, color_cols=["Box entry %", "Total_xG"])
            with tc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(throwin_taker_summary(df_b).head(12), height=320, color_cols=["Box entry %", "Total_xG"])

    # ── Report ────────────────────────────────────────────────────────────────
    with tab_report:
        section_header("Pre-match PDF brief")
        pdf_teams = ["All"] + _safe_sorted(filtered["Team"]) if "Team" in filtered.columns else ["All"]
        if st.session_state.get("throwins_pdf_team") not in pdf_teams:
            st.session_state["throwins_pdf_team"] = "All"
        pdf_team = st.selectbox("Report team", pdf_teams, key="throwins_pdf_team")
        opponent = st.text_input("Opponent / label for filename", value="", key="throwins_pdf_label")
        pdf_filtered = filtered[filtered["Team"].astype(str).eq(pdf_team)].copy() if pdf_team != "All" and "Team" in filtered.columns else filtered.copy()
        pdf_label = f"Throw-ins – {pdf_team}" if pdf_team != "All" else "Throw-ins"
        safe_name = (opponent.strip() or pdf_label).lower().replace(" ", "_").replace("/", "-")
        st.info("PDF generation may take a few seconds on large datasets.")
        st.download_button(
            "⬇ Download pre-match PDF",
            data=_cached_report_pdf(pdf_filtered, pdf_label, opponent.strip()),
            file_name=f"{safe_name}_throwins_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="throwins_pdf_download",
        )

    # ── Rows ──────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("Sequences", f"{len(sequences):,} sequences")
        render_analyst_table(sequences, height=380, color_cols=["Shots", "Goals", "Total xG", "Best shot xG"])

        section_header("Raw rows", f"{len(filtered):,} events")
        display_cols = [c for c in [
            "Match", "Team", "Taker", "Shooter", "minute", "second",
            "pass_x", "pass_y", "Delivery height", "Shot outcome", "xg",
            "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob", "OPS_Opponent_Rating",
            "League", "game_period", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(
            filtered[display_cols], height=520,
            color_cols=["xg", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob", "OPS_Opponent_Rating"],
        )
