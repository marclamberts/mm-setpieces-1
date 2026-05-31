"""Freekicks section — maximum analytical depth."""
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
    _league_filter_options,
    _league_selectbox,
    _set_piece_team_options,
    _apply_team_perspective,
    _with_match_names,
    bar_chart,
    render_plotly_visual,
    render_mpl_visual,
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


def _zone_channel_breakdown(sequences: pd.DataFrame) -> pd.DataFrame:
    if sequences.empty:
        return pd.DataFrame()
    cols = [c for c in ["Zone", "Channel"] if c in sequences.columns]
    if not cols:
        return pd.DataFrame()
    return (
        sequences.groupby(cols, dropna=False)
        .agg(
            Sequences=("Zone", "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
            Avg_xG=("Total xG", "mean"),
        )
        .reset_index()
        .assign(
            **{
                "Shot seq %": lambda d: (d["Shots"] / d["Sequences"] * 100).round(2),
                "xG / seq": lambda d: (d["Total_xG"] / d["Sequences"]).round(3),
            }
        )
        .sort_values("xG / seq", ascending=False)
    )


def _height_breakdown(sequences: pd.DataFrame) -> pd.DataFrame:
    if sequences.empty or "Initial height" not in sequences.columns:
        return pd.DataFrame()
    return (
        sequences.groupby("Initial height", dropna=False)
        .agg(
            Sequences=("Initial height", "size"),
            Shots=("Shots", "sum"),
            Goals=("Goals", "sum"),
            Total_xG=("Total xG", "sum"),
        )
        .reset_index()
        .assign(
            **{
                "Shot seq %": lambda d: (d["Shots"] / d["Sequences"] * 100).round(2),
                "xG / seq": lambda d: (d["Total_xG"] / d["Sequences"]).round(3),
            }
        )
        .sort_values("xG / seq", ascending=False)
    )


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
    return (
        seqs.groupby("Minute band", dropna=False)
        .agg(Sequences=("Minute band", "size"), Shots=("Shots", "sum"), Goals=("Goals", "sum"), Total_xG=("Total xG", "sum"))
        .reset_index()
        .assign(xG_per_seq=lambda d: (d["Total_xG"] / d["Sequences"]).round(3))
    )


# ── Main render ──────────────────────────────────────────────────────────────

def render_freekicks() -> None:
    label = "Freekicks"
    df = _with_match_names(load_prepared_freekick_brief_data(DATA_VERSION))
    hero_block("Set pieces", label, "Indirect free kick sequences, zones, channels, takers, and shot creation.")
    if df.empty:
        st.warning("No freekick rows were found.")
        return

    leagues = _league_filter_options(df, "SP")
    teams = _set_piece_team_options(df)
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []

    league = _league_selectbox("League", leagues, key="freekicks_league")
    team = st.sidebar.selectbox("Team", teams, key="freekicks_team")
    perspective = st.sidebar.radio("Perspective", ["For", "Against"], key="freekicks_perspective")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key="freekicks_sample")
    taker_filter: list = []
    height_filter: list = []
    with st.sidebar.expander("More filters", expanded=False):
        taker_filter = st.multiselect("Taker", takers, key="freekicks_taker")
        height_filter = st.multiselect("Delivery height", heights, key="freekicks_height")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
    filtered = _apply_team_perspective(filtered, team, perspective)
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10].copy()
    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()
    if height_filter and "Delivery height" in filtered.columns:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)].copy()

    sequences = freekick_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("Sample", sample), ("Taker", taker_filter), ("Height", height_filter),
    ]

    render_export_controls(filtered, "freekicks", label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    scope = team if team != "All" else league if league != "All" else "All teams"

    tabs = st.tabs([
        "📊 Overview", "🔗 Sequences", "🗺️ Zones", "🎯 Pitch",
        "👤 Roles", "📈 Trends", "⚖️ Compare", "🗃️ Rows",
    ])
    tab_overview, tab_sequences, tab_zones, tab_pitch, tab_roles, tab_trends, tab_compare, tab_rows = tabs

    # ── Overview ─────────────────────────────────────────────────────────────
    with tab_overview:
        kpi_row(filtered)
        info_panel(filtered)

        seq_count = len(sequences)
        avg_actions = float(sequences["Actions"].mean()) if not sequences.empty and "Actions" in sequences.columns else 0.0
        direct_threat = float((sequences["Zone"].eq("Direct threat")).mean() * 100) if not sequences.empty and "Zone" in sequences.columns else 0.0
        wide_delivery = float((sequences["Zone"].eq("Wide delivery")).mean() * 100) if not sequences.empty and "Zone" in sequences.columns else 0.0
        best_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sequences", seq_count)
        c2.metric("Avg actions / seq", f"{avg_actions:.2f}")
        c3.metric("Direct threat %", f"{direct_threat:.2f}%")
        c4.metric("Wide delivery %", f"{wide_delivery:.2f}%")
        c5.metric("Best seq xG", f"{best_xg:.3f}")

        section_header(f"{scope} — Zone × Channel board", "Sequences by origin zone and channel")
        zone_ch = _zone_channel_breakdown(sequences)
        render_analyst_table(
            zone_ch, height=340,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Shot seq %", "xG / seq"],
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
        section_header("Priority sequences", "Ranked by xG — highest-threat FK sequences")
        base_cols = ["Match", "Team", "Minute", "Zone", "Channel", "Initial taker", "Initial height",
                     "Actions", "Shots", "Goals", "Total xG", "Best shooter", "Best shot xG", "Shot outcome"]
        priority = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
        render_analyst_table(
            priority.head(60), height=520,
            color_cols=["Actions", "Shots", "Goals", "Total xG", "Best shot xG"],
        )

        if not sequences.empty and "Channel" in sequences.columns:
            section_header("Channel mix")
            mix = sequences.groupby("Channel", dropna=False).agg(
                Sequences=("Channel", "size"),
                Shots=("Shots", "sum"),
                Goals=("Goals", "sum"),
                Total_xG=("Total xG", "sum"),
            ).reset_index().assign(xG_per_seq=lambda d: (d["Total_xG"] / d["Sequences"]).round(3))
            c1, c2 = st.columns(2)
            with c1:
                fig = bar_chart(mix.sort_values("Sequences", ascending=False), x="Channel", y="Sequences", color="Channel")
                fig.update_layout(showlegend=False, margin=dict(l=8, r=8, t=28, b=8))
                render_plotly_visual(polish_plotly_figure(fig), "Channel mix", "freekicks_channel_mix_png")
            with c2:
                render_analyst_table(mix, height=280, color_cols=["Sequences", "Shots", "Goals", "xG_per_seq"])

    # ── Zones ─────────────────────────────────────────────────────────────────
    with tab_zones:
        section_header("Zone × Channel breakdown", "Where FKs originate and what they produce")
        zone_df = freekick_zone_summary(filtered)
        render_analyst_table(
            zone_df, height=380,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Avg_xG", "Shots / seq"],
        )

        if not zone_df.empty:
            zc1, zc2 = st.columns(2)
            with zc1:
                section_header("xG / seq by zone")
                plot_df = zone_df.copy()
                plot_df["Label"] = plot_df.get("Zone", plot_df.columns[0]).astype(str)
                if "Channel" in plot_df.columns:
                    plot_df["Label"] = plot_df["Zone"].astype(str) + " / " + plot_df["Channel"].astype(str)
                xg_col = "Avg_xG" if "Avg_xG" in plot_df.columns else plot_df.select_dtypes("number").columns[0]
                fig = bar_chart(plot_df.sort_values(xg_col), x=xg_col, y="Label", orientation="h")
                fig.update_layout(height=380, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig), "xG per seq by zone", "freekicks_zone_xg_png")
            with zc2:
                section_header("Sequence volume by zone")
                fig2 = bar_chart(plot_df.sort_values("Sequences", ascending=False), x="Sequences", y="Label", orientation="h")
                fig2.update_layout(height=380, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
                render_plotly_visual(polish_plotly_figure(fig2), "Sequence volume by zone", "freekicks_zone_vol_png")

        section_header("Delivery height breakdown")
        render_analyst_table(
            _height_breakdown(sequences), height=260,
            color_cols=["Sequences", "Shots", "Goals", "Shot seq %", "xG / seq"],
        )

        section_header("Minute band breakdown")
        render_analyst_table(
            _minute_band_breakdown(sequences), height=280,
            color_cols=["Sequences", "Shots", "Goals", "xG_per_seq"],
        )

    # ── Pitch ─────────────────────────────────────────────────────────────────
    with tab_pitch:
        section_header("FK origin map", "Where free kicks are taken from")
        render_mpl_visual(freekick_origin_map_figure(filtered), "FK origin map", "freekicks_origin_map_png")

        section_header("Start locations and shot map")
        p1, p2 = st.columns(2)
        with p1:
            render_plotly_visual(
                polish_plotly_figure(starting_location_map_figure(filtered, f"{label} start locations")),
                "Start locations", "freekicks_start_locations_png",
            )
        with p2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(filtered, f"{scope} — FK shots")),
                "Shot map", "freekicks_shot_map_png",
            )

        section_header("Technique breakdown")
        if "Technique" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Technique", "Technique", top_n=10, color="#0f172a"),
                "FK technique", "freekicks_technique_png",
            )
        section_header("Delivery height breakdown")
        if "Delivery height" in filtered.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Delivery height", "Delivery height", top_n=8, color="#1d4ed8"),
                "Delivery height", "freekicks_height_png",
            )

    # ── Roles ─────────────────────────────────────────────────────────────────
    with tab_roles:
        section_header("Taker summary", "Ranked by total xG")
        taker_df = freekick_taker_summary(filtered)
        render_analyst_table(
            taker_df.head(35), height=460,
            color_cols=["Sequences", "Shots", "Goals", "Total_xG", "Avg_xG", "Shots / seq"],
        )
        render_plotly_visual(
            categorical_breakdown_figure(filtered, "Taker", "Top FK takers", top_n=15, color="#c1121f"),
            "Top FK takers", "freekicks_top_takers_png",
        )

        section_header("Shooter summary", "Ranked by total xG")
        shooter_df = freekick_shooter_summary(filtered)
        render_analyst_table(
            shooter_df.head(35), height=440,
            color_cols=["Shots", "Goals", "Total_xG", "Avg_xG", "Best_xG", "Conversion %"],
        )
        if not shooter_df.empty and "Shooter" in shooter_df.columns:
            render_plotly_visual(
                categorical_breakdown_figure(filtered, "Shooter", "Top FK shooters", top_n=15, color="#1d4ed8"),
                "Top FK shooters", "freekicks_top_shooters_png",
            )

    # ── Trends ────────────────────────────────────────────────────────────────
    with tab_trends:
        section_header("Minute distribution", "When FKs are awarded across 90 minutes")
        render_plotly_visual(minute_distribution_figure(filtered, "FK minute distribution"), "FK minute distribution", "freekicks_minute_png")

        section_header("Match log", "Per-match FK output")
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
            fig.update_layout(height=480, margin=dict(l=8, r=8, t=24, b=8), showlegend=False)
            render_plotly_visual(polish_plotly_figure(fig), "xG per match", "freekicks_match_xg_png")
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
            seq_a = freekick_sequence_summary(df_a)
            seq_b = freekick_sequence_summary(df_b)
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
            _kpi_compare_row("Shot rate %", kpi_a["shot_rate"], kpi_b["shot_rate"], "{:.2f}")
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

            section_header("Zone × Channel comparison")
            zc1, zc2 = st.columns(2)
            with zc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(_zone_channel_breakdown(seq_a), height=300, color_cols=["xG / seq", "Shot seq %"])
            with zc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(_zone_channel_breakdown(seq_b), height=300, color_cols=["xG / seq", "Shot seq %"])

            section_header("Taker comparison")
            tc1, tc2 = st.columns(2)
            with tc1:
                st.caption(f"**{team_a}**")
                render_analyst_table(freekick_taker_summary(df_a).head(12), height=320, color_cols=["Total_xG", "Avg_xG"])
            with tc2:
                st.caption(f"**{team_b}**")
                render_analyst_table(freekick_taker_summary(df_b).head(12), height=320, color_cols=["Total_xG", "Avg_xG"])

    # ── Rows ──────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("Sequences", f"{len(sequences):,} sequences")
        render_analyst_table(sequences, height=380, color_cols=["Actions", "Shots", "Goals", "Total xG", "Best shot xG"])

        section_header("Raw rows", f"{len(filtered):,} events")
        display_cols = [c for c in [
            "Match", "Team", "Taker", "Shooter", "minute", "second",
            "pass_x", "pass_y", "Delivery height", "Shot outcome", "xg",
            "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob", "OPS_Opponent_Rating",
            "League", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(
            filtered[display_cols], height=520,
            color_cols=["xg", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob", "OPS_Opponent_Rating"],
        )
