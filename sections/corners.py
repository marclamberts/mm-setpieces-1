"""Corners section — maximum analytical depth."""
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
    build_team_leaderboard,
    build_team_archetypes,
    build_role_archetypes,
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
    add_delivery_zones,
    shotmap_figure,
    starting_location_map_figure,
    corner_landing_heatmap_figure,
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
    set_section,
)


# ── Sidebar filters ─────────────────────────────────────────────────────────

def _filter_data(df: pd.DataFrame, key_prefix: str):
    leagues = _league_filter_options(df, "Corners")
    _cur_league = st.session_state.get(f"{key_prefix}_league", "All")
    if _cur_league not in leagues:
        _cur_league = "All"
    _df_for_teams = df[df["League"].eq(_cur_league)] if _cur_league != "All" and "League" in df.columns else df
    teams = _set_piece_team_options(_df_for_teams)
    if st.session_state.get(f"{key_prefix}_team", "All") not in teams:
        st.session_state[f"{key_prefix}_team"] = "All"
    sides = ["All"] + _safe_sorted(df["side"]) if "side" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    techniques = _safe_sorted(df["Technique"]) if "Technique" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    shot_outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []
    delivery_outcomes = _safe_sorted(df["Delivery outcome"]) if "Delivery outcome" in df.columns else []

    minute_min, minute_max = 0, 95
    if "minute" in df.columns:
        vals = pd.to_numeric(df["minute"], errors="coerce").dropna()
        if not vals.empty:
            minute_min = int(vals.min())
            minute_max = max(95, int(vals.max()))

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        team = st.selectbox("Team", teams, key=f"{key_prefix}_team")
    with fc2:
        league = _league_selectbox("League", leagues, key=f"{key_prefix}_league")
    with fc3:
        perspective = st.radio("Perspective", ["For", "Against"], horizontal=True, key=f"{key_prefix}_perspective")
    with fc4:
        sample = st.radio("Sample", ["Total", "Last 10"], horizontal=True, key=f"{key_prefix}_sample")

    # Compute takers from selected team's data (team-specific player list)
    if team != "All":
        team_df = _apply_team_perspective(df.copy(), team, perspective)
        takers = _safe_sorted(team_df["Taker"]) if "Taker" in team_df.columns else []
    else:
        takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []

    side = "All"; time_in_game = "All"; minute_range = (minute_min, minute_max)
    taker_filter: list = []; technique_filter: list = []; height_filter: list = []
    shot_outcome_filter: list = []; delivery_outcome_filter: list = []; only_shots = False
    xg_min: float = 0.0

    with st.expander("More filters", expanded=False):
        mx1, mx2, mx3, mx4 = st.columns(4)
        with mx1:
            side = st.radio("Side", sides, key=f"{key_prefix}_side")
            time_in_game = st.selectbox("Time in game", periods, key=f"{key_prefix}_period")
        with mx2:
            minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key=f"{key_prefix}_minutes")
            only_shots = st.checkbox("Shots only", value=False, key=f"{key_prefix}_shots_only")
        with mx3:
            taker_filter = st.multiselect("Taker", takers, key=f"{key_prefix}_taker")
            technique_filter = st.multiselect("Technique", techniques, key=f"{key_prefix}_technique")
        with mx4:
            height_filter = st.multiselect("Height", heights, key=f"{key_prefix}_height")
            shot_outcome_filter = st.multiselect("Shot outcome", shot_outcomes, key=f"{key_prefix}_outcome")
        mx5, mx6 = st.columns(2)
        with mx5:
            delivery_outcome_filter = st.multiselect("First contact (Delivery outcome)", delivery_outcomes, key=f"{key_prefix}_delivery_outcome")
        with mx6:
            xg_min = st.number_input("Min xG (shot map filter)", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key=f"{key_prefix}_xg_min")

    filtered = df.copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]
    if sample == "Last 10" and "match_rank" in filtered.columns:
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
    if delivery_outcome_filter and "Delivery outcome" in filtered.columns:
        filtered = filtered[filtered["Delivery outcome"].isin(delivery_outcome_filter)]
    if only_shots and "is_shot" in filtered.columns:
        filtered = filtered[filtered["is_shot"]]

    filters = [
        ("Team", team), ("Perspective", perspective if team != "All" else "All"),
        ("League", league), ("Sample", sample), ("Side", side), ("Period", time_in_game),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Taker", taker_filter), ("Technique", technique_filter),
        ("Height", height_filter), ("Shot outcome", shot_outcome_filter),
        ("First contact", delivery_outcome_filter),
        ("Min xG", f"≥{xg_min:.2f}" if xg_min > 0 else "All"),
        ("Shot only", "Yes" if only_shots else "All"),
    ]
    # Store xg_min for use in calling code
    st.session_state[f"{key_prefix}_current_xg_min"] = xg_min
    return filtered, filters, team, league


# ── Zone breakdown helper ────────────────────────────────────────────────────

def _zone_summary(df: pd.DataFrame) -> pd.DataFrame:
    base = add_delivery_zones(unique_start_events(df))
    if base.empty or "Delivery zone" not in base.columns:
        return pd.DataFrame()
    rows = []
    for zone, part in base.groupby("Delivery zone", dropna=False):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        rows.append({
            "Delivery zone": zone,
            "Corners": events,
            "Shots": shots,
            "Goals": goals,
            "Shot rate %": round(shots / events * 100, 2) if events else 0.0,
            "Total xG": round(xg, 2),
            "xG / corner": round(xg / events, 3) if events else 0.0,
            "xG / shot": round(xg / shots, 3) if shots else 0.0,
            "Conv %": round(goals / shots * 100, 2) if shots else 0.0,
        })
    return pd.DataFrame(rows).sort_values("xG / corner", ascending=False)


def _side_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    base = unique_start_events(df)
    if base.empty or "side" not in base.columns:
        return pd.DataFrame()
    rows = []
    for side, part in base.groupby("side", dropna=False):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        rows.append({
            "Side": side,
            "Corners": events,
            "Shots": shots,
            "Goals": goals,
            "Shot rate %": round(shots / events * 100, 2) if events else 0.0,
            "Total xG": round(xg, 2),
            "xG / corner": round(xg / events, 3) if events else 0.0,
        })
    return pd.DataFrame(rows).sort_values("xG / corner", ascending=False)


def _technique_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    base = add_delivery_zones(unique_start_events(df))
    if base.empty:
        return pd.DataFrame()
    rows = []
    for (tech, height), part in base.groupby(
        [c for c in ["Technique", "Delivery height"] if c in base.columns], dropna=False
    ):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        rows.append({
            "Technique": tech,
            "Height": height,
            "Corners": events,
            "Shots": shots,
            "Goals": goals,
            "Shot rate %": round(shots / events * 100, 2) if events else 0.0,
            "Total xG": round(xg, 2),
            "xG / corner": round(xg / events, 3) if events else 0.0,
            "xG / shot": round(xg / shots, 3) if shots else 0.0,
        })
    return pd.DataFrame(rows).sort_values("xG / corner", ascending=False)


def _outcome_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    base = unique_start_events(df)
    cols = [c for c in ["Delivery outcome", "Shot outcome"] if c in base.columns]
    if base.empty or not cols:
        return pd.DataFrame()
    rows = []
    for keys, part in base.groupby(cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        record = dict(zip(cols, keys))
        events = int(len(part))
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        record["Count"] = events
        record["Total xG"] = round(xg, 2)
        record["xG / corner"] = round(xg / events, 3) if events else 0.0
        rows.append(record)
    return pd.DataFrame(rows).sort_values("Count", ascending=False)


def _period_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    base = unique_start_events(df)
    if base.empty or "game_period" not in base.columns:
        return pd.DataFrame()
    rows = []
    for period, part in base.groupby("game_period", dropna=False):
        events = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        rows.append({
            "Period": period,
            "Corners": events,
            "Shots": shots,
            "Goals": goals,
            "Shot rate %": round(shots / events * 100, 2) if events else 0.0,
            "Total xG": round(xg, 2),
            "xG / corner": round(xg / events, 3) if events else 0.0,
        })
    return pd.DataFrame(rows).sort_values("xG / corner", ascending=False)


# ── Compare helper ───────────────────────────────────────────────────────────

def _kpi_compare_row(label: str, val_a, val_b, fmt: str = "{:.2f}") -> None:
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
    if df.empty:
        st.warning("No corner rows were found.")
        return

    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    filtered, filters, selected_team, selected_league = _filter_data(df, "corners")

    scope_parts = [p for p in [selected_team if selected_team != "All" else None,
                                selected_league if selected_league != "All" else None] if p]
    scope_str = " · ".join(scope_parts) if scope_parts else "All teams"
    hero_block("Set pieces", label, f"{scope_str} · {len(filtered):,} events")
    st.session_state["ctx_row_count"] = f"{label} · {len(filtered):,} events"

    render_export_controls(filtered, label, label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    scope = selected_team if selected_team != "All" else selected_league if selected_league != "All" else "All teams"

    tabs = st.tabs([
        "📊 Overview",
        "🎯 Delivery",
        "🔥 Landing Zones",
        "🗺️ Zones",
        "👤 Takers",
        "🔁 Patterns",
        "📈 Trends",
        "⚖️ Compare",
        "🧠 Archetypes",
        "📋 Report",
        "🗃️ Rows",
    ])
    (
        tab_overview, tab_delivery, tab_heatmap, tab_zones, tab_takers,
        tab_patterns, tab_trends, tab_compare, tab_archetypes,
        tab_report, tab_rows,
    ) = tabs

    # ── Overview ────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(filtered)
        info_panel(filtered)

        section_header(f"{scope} — Team board", "Volume, shots, xG ranked by performance")
        team_board = build_team_leaderboard(filtered)
        render_analyst_table(
            team_board.head(30), height=420,
            color_cols=["Shot rate %", "Total xG", "xG / event", "xG / 100", "xG / shot", "Goals / shot %"],
        )

        section_header("Technique × Height mix")
        _, technique_mix, outcome_mix = build_summary_tables(filtered)
        col_t, col_o = st.columns(2)
        with col_t:
            render_analyst_table(technique_mix.head(20), height=320)
        with col_o:
            render_analyst_table(outcome_mix.head(20), height=320)

        section_header("Key insights")
        cols = st.columns(2)
        for idx, insight in enumerate(generate_set_piece_insights(filtered, label)[:8]):
            with cols[idx % 2]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

    # ── Delivery ────────────────────────────────────────────────────────────
    with tab_delivery:
        section_header("Pitch maps")
        d1, d2 = st.columns(2)
        with d1:
            render_mpl_visual(mplsoccer_delivery_figure(filtered, label), "Delivery map", "corners_delivery_map_png")
        with d2:
            render_mpl_visual(mplsoccer_shot_figure(filtered, label), "Shot quality map", "corners_shot_quality_png")
        render_mpl_visual(mplsoccer_delivery_sp_outcome_figure(filtered, label), "Delivery SP outcomes", "corners_delivery_sp_outcomes_png")

        section_header("Shot map")
        xg_min = st.session_state.get(f"corners_current_xg_min", 0.0)
        shot_map_df = filtered.copy()
        if xg_min > 0 and "xg" in shot_map_df.columns:
            shot_map_df = shot_map_df[pd.to_numeric(shot_map_df["xg"], errors="coerce").fillna(0) >= xg_min]
        render_plotly_visual(
            polish_plotly_figure(shotmap_figure(shot_map_df, f"{scope} — corner shots (xG ≥ {xg_min:.2f})" if xg_min > 0 else f"{scope} — corner shots")),
            "Shot map", "corners_shot_map_png",
        )

        section_header("Technique, height & side breakdown")
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Technique", "Technique", top_n=8, color="#e2e8f0"), "Technique", "corners_technique_png")
        with ch2:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Delivery height", "Height", top_n=8, color="#93c5fd"), "Height", "corners_height_png")
        with ch3:
            render_plotly_visual(categorical_breakdown_figure(filtered, "side", "Side", top_n=6, color="#fca5a5"), "Side", "corners_side_png")

        section_header("Technique × Height — detailed table")
        render_analyst_table(
            _technique_breakdown(filtered), height=420,
            color_cols=["Shot rate %", "Total xG", "xG / corner", "xG / shot"],
        )

        section_header("Delivery & shot outcome combinations")
        render_analyst_table(_outcome_breakdown(filtered), height=340)

    # ── Landing Zone Heatmap ─────────────────────────────────────────────────
    with tab_heatmap:
        section_header("Delivery landing zones", "KDE heatmap — where corners arrive in the box")
        hl1, hl2 = st.columns([1, 2])
        with hl1:
            colour_opts = {"By density (KDE)": "density"}
            render_mpl_visual(
                corner_landing_heatmap_figure(filtered),
                "Corner landing heatmap", "corners_landing_heatmap",
            )
        with hl2:
            section_header("Zone breakdown table")
            lz_df = filtered.copy()
            if "delivery_end_x" in lz_df.columns and "delivery_end_y" in lz_df.columns:
                from mm_setpieces_1.utils import add_delivery_zones
                lz_df = add_delivery_zones(lz_df)
                if "Delivery zone" in lz_df.columns:
                    zone_counts = (
                        lz_df.groupby("Delivery zone", dropna=False)
                        .agg(
                            Deliveries=("Delivery zone", "count"),
                            Shots=("is_shot", "sum") if "is_shot" in lz_df.columns else ("Delivery zone", "count"),
                            xG=("xg", "sum") if "xg" in lz_df.columns else ("Delivery zone", "count"),
                        )
                        .reset_index()
                        .sort_values("Deliveries", ascending=False)
                    )
                    zone_counts["xG"] = zone_counts["xG"].round(2)
                    zone_counts["xG / delivery"] = (zone_counts["xG"] / zone_counts["Deliveries"].clip(lower=1) * 100).round(2)
                    render_analyst_table(zone_counts, height=300)
            else:
                st.info("Landing zone data (delivery_end_x/y) not available in this dataset.")

    # ── Zones ────────────────────────────────────────────────────────────────
    with tab_zones:
        section_header("Delivery zone analysis", "Where the ball lands and what that produces")
        zone_df = _zone_summary(filtered)
        render_analyst_table(
            zone_df, height=380,
            color_cols=["Shot rate %", "Total xG", "xG / corner", "xG / shot", "Conv %"],
        )

        if not zone_df.empty and "Delivery zone" in zone_df.columns:
            zc1, zc2 = st.columns(2)
            with zc1:
                section_header("xG / corner by zone")
                fig = bar_chart(zone_df.sort_values("xG / corner"), x="xG / corner", y="Delivery zone", orientation="h")
                fig.update_traces(marker_color="#60a5fa")
                fig.update_layout(height=380, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig), "Zone xG per corner", "corners_zone_xg_png")
            with zc2:
                section_header("Shot rate by zone")
                fig2 = bar_chart(zone_df.sort_values("Shot rate %"), x="Shot rate %", y="Delivery zone", orientation="h")
                fig2.update_traces(marker_color="#4ade80")
                fig2.update_layout(height=380, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig2), "Zone shot rate", "corners_zone_shot_rate_png")

        section_header("Side breakdown")
        side_df = _side_breakdown(filtered)
        render_analyst_table(
            side_df, height=240,
            color_cols=["Shot rate %", "Total xG", "xG / corner"],
        )

        section_header("Period breakdown")
        period_df = _period_breakdown(filtered)
        render_analyst_table(
            period_df, height=260,
            color_cols=["Shot rate %", "Total xG", "xG / corner"],
        )

    # ── Takers ───────────────────────────────────────────────────────────────
    with tab_takers:
        taker_sort = st.radio("Sort takers by", ["Events", "xG / 100"], horizontal=True, key="corners_taker_sort")
        section_header("Taker leaderboard")
        taker_lb = build_taker_leaderboard(filtered)
        if taker_sort == "Events" and "Events" in taker_lb.columns:
            taker_lb = taker_lb.sort_values("Events", ascending=False)
        render_analyst_table(
            taker_lb.head(35), height=460,
            color_cols=["Events", "Shots", "Goals", "Shot rate", "xG / event", "xG / 100"],
        )

        section_header("Shooter leaderboard", "Ranked by total xG")
        render_analyst_table(
            build_shooter_leaderboard(filtered).head(35), height=420,
            color_cols=["Shots", "Goals", "Total xG", "xG / shot", "Conversion %"],
        )

        section_header("Top takers by volume (events)")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top takers", top_n=15, color="#fca5a5"),
            "Top takers", "corners_top_takers_png",
        )

        section_header("Shot outcomes by player")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Shooter", "Top shooters", top_n=15, color="#93c5fd"),
            "Top shooters", "corners_top_shooters_png",
        )

    # ── Patterns ─────────────────────────────────────────────────────────────
    with tab_patterns:
        st.info(
            "**What is the Patterns tab?**  "
            "It cross-references every delivery technique, height, landing zone, and shot outcome "
            "to reveal which combinations produce the most threat. "
            "Use it to identify your team's highest-value routines and expose the opponent's most dangerous patterns — "
            "then design training sessions or defensive setups around the evidence."
        )
        section_header("Full pattern library", "Every Technique × Height × Zone × Outcome combination")
        render_analyst_table(
            build_pattern_library(filtered).head(60), height=520,
            color_cols=["Events", "Shots", "Goals", "Shot rate %", "Total xG", "xG / event", "xG / 100", "xG / shot"],
        )

        section_header("Delivery outcome chart")
        if "Delivery outcome" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Delivery outcome", "Delivery outcomes", top_n=14, color="#86efac"),
                "Delivery outcomes", "corners_delivery_outcomes_png",
            )

        section_header("Shot outcome chart")
        if "Shot outcome" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Shot outcome", "Shot outcomes", top_n=12, color="#fcd34d"),
                "Shot outcomes", "corners_shot_outcomes_png",
            )

    # ── Trends ───────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution", "When corners are taken across 90 minutes")
        render_plotly_visual(minute_distribution_figure(filtered, "Minute distribution"), "Minute distribution", "corners_minute_distribution_png")

        if st.button("⏱ Analyse corner delivery delays →", key="corners_jump_delay", help="Jump to Delay Analysis"):
            set_section("Delay Analysis")

        section_header("Match log", "Per-match corner output")
        match_log = build_match_log(filtered)
        if not match_log.empty:
            render_analyst_table(
                match_log, height=460,
                color_cols=["Events", "Shots", "Goals", "Shot rate %", "Total xG"],
            )

            section_header("xG per match — top 20")
            top_matches = match_log.sort_values("Total xG", ascending=False).head(20)
            match_col = "Match" if "Match" in top_matches.columns else top_matches.columns[0]
            fig = bar_chart(top_matches.sort_values("Total xG"), x="Total xG", y=match_col, orientation="h")
            fig.update_traces(marker_color="#60a5fa")
            fig.update_layout(height=480, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "xG per match", "corners_match_xg_png")
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
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.2f}")
            _kpi_compare_row("xG / 100", kpi_a["xg_per_100"], kpi_b["xg_per_100"], "{:.2f}")
            _kpi_compare_row("xG / shot", kpi_a["xg_per_shot"], kpi_b["xg_per_shot"], "{:.3f}")
            _kpi_compare_row("Goal conv %", kpi_a["goal_conversion"], kpi_b["goal_conversion"], "{:.2f}")

            st.divider()
            section_header("Delivery maps")
            mc1, mc2 = st.columns(2)
            with mc1:
                st.caption(f"**{team_a}**")
                render_mpl_visual(mplsoccer_delivery_figure(df_a, team_a), f"{team_a} delivery", "corners_cmp_a_delivery") if not df_a.empty else st.info("No data.")
            with mc2:
                st.caption(f"**{team_b}**")
                render_mpl_visual(mplsoccer_delivery_figure(df_b, team_b), f"{team_b} delivery", "corners_cmp_b_delivery") if not df_b.empty else st.info("No data.")

            section_header("Zone breakdown comparison")
            zc1, zc2 = st.columns(2)
            with zc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(_zone_summary(df_a), height=300, color_cols=["xG / corner", "Shot rate %"])
            with zc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(_zone_summary(df_b), height=300, color_cols=["xG / corner", "Shot rate %"])

            section_header("Taker comparison")
            tc1, tc2 = st.columns(2)
            with tc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(build_taker_leaderboard(df_a).head(12), height=320, color_cols=["xG / 100", "Shot rate", "xG / event"])
            with tc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(build_taker_leaderboard(df_b).head(12), height=320, color_cols=["xG / 100", "Shot rate", "xG / event"])

            section_header("Pattern comparison")
            pc1, pc2 = st.columns(2)
            with pc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(build_pattern_library(df_a).head(15), height=340, color_cols=["xG / event", "Shot rate %"])
            with pc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(build_pattern_library(df_b).head(15), height=340, color_cols=["xG / event", "Shot rate %"])

    # ── Archetypes ────────────────────────────────────────────────────────────
    with tab_archetypes:
        section_header("Team archetypes", "Tactical profile for every team in the current filter")
        team_arch = build_team_archetypes(filtered)
        if not team_arch.empty:
            render_analyst_table(
                team_arch, height=420,
                color_cols=["Events", "Shots", "Goals", "Shot rate %", "xG / event", "xG / 100"],
            )

        section_header("Taker role archetypes", "Individual taker profiles with role classification")
        role_arch = build_role_archetypes(filtered)
        if not role_arch.empty:
            render_analyst_table(
                role_arch.head(50), height=500,
                color_cols=["Events", "Shots", "Goals", "Shot rate", "xG / event", "xG / 100"],
            )
        else:
            st.info("No taker archetype data available for this filter.")

        section_header("Technique chart — full breakdown")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Technique", "Technique share", top_n=12, color="#e2e8f0"),
            "Technique share", "corners_tech_arch_png",
        )

        section_header("Delivery height chart")
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Delivery height", "Delivery height", top_n=8, color="#fca5a5"),
            "Delivery height", "corners_height_arch_png",
        )

    # ── Report ───────────────────────────────────────────────────────────────
    with tab_report:
        section_header("Pre-match PDF brief")
        pdf_teams = ["All"] + _safe_sorted(filtered["Team"]) if "Team" in filtered.columns else ["All"]
        if st.session_state.get("corners_pdf_team") not in pdf_teams:
            st.session_state["corners_pdf_team"] = "All"
        pdf_team = st.selectbox("Report team", pdf_teams, key="corners_pdf_team")
        opponent = st.text_input("Opponent / label for filename", value="", key="corners_pdf_label")
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
            "OPS_Opponent_Rating", "League", "game_period", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(
            filtered[display_cols], height=600,
            color_cols=["xg", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob", "OPS_Opponent_Rating"],
        )
