"""Corners section."""
from __future__ import annotations

import streamlit as st

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
)

from sections._shared import (
    _safe_sorted,
    _league_filter_options,
    _league_selectbox,
    _set_piece_team_options,
    _apply_team_perspective,
    _cached_report_pdf,
    render_plotly_visual,
    render_mpl_visual,
)


def _filter_data(df, key_prefix: str):
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

    minute_min = 0
    minute_max = 95
    if "minute" in df.columns and not df["minute"].dropna().empty:
        import pandas as pd
        minute_values = pd.to_numeric(df["minute"], errors="coerce").dropna()
        if not minute_values.empty:
            minute_min = int(min(0, minute_values.min()))
            minute_max = max(95, int(minute_values.max()))

    side = "All"
    time_in_game = "All"
    minute_range = (minute_min, minute_max)
    taker_filter: list[str] = []
    technique_filter: list[str] = []
    height_filter: list[str] = []
    shot_outcome_filter: list[str] = []
    only_shots = False

    with st.sidebar.expander("More filters", expanded=False):
        side = st.radio("Side", sides, key=f"{key_prefix}_side")
        time_in_game = st.selectbox("Time in game", periods, key=f"{key_prefix}_period")
        minute_range = st.slider("Minutes", minute_min, minute_max, (minute_min, minute_max), key=f"{key_prefix}_minutes")
        taker_filter = st.multiselect("Taker", takers, key=f"{key_prefix}_taker")
        technique_filter = st.multiselect("Technique", techniques, key=f"{key_prefix}_technique")
        height_filter = st.multiselect("Height", heights, key=f"{key_prefix}_height")
        shot_outcome_filter = st.multiselect("Shot outcome", shot_outcomes, key=f"{key_prefix}_outcome")
        only_shots = st.checkbox("Shots only", value=False, key=f"{key_prefix}_shots_only")

    import pandas as pd
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
        ("Team", team),
        ("Perspective", perspective if team != "All" else "All"),
        ("League", league),
        ("Sample", sample),
        ("Side", side),
        ("Period", time_in_game),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Taker", taker_filter),
        ("Technique", technique_filter),
        ("Height", height_filter),
        ("Shot outcome", shot_outcome_filter),
        ("Shot only", "Yes" if only_shots else "All"),
    ]
    return filtered, filters


def render_corners() -> None:
    label = "Corners"
    df = load_prepared_sp_data(label, DATA_VERSION)
    hero_block("Set pieces", label, "Choose a team or league and read the full dashboard on one page.")
    if df.empty:
        st.warning("No corner rows were found.")
        return

    filtered, filters = _filter_data(df, "corners")
    render_export_controls(filtered, label, label)
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()

    kpi_row(filtered)
    info_panel(filtered)

    filter_lookup = {str(name): value for name, value in filters}
    selected_team = str(filter_lookup.get("Team", "All"))
    selected_league = str(filter_lookup.get("League", "All"))
    scope = selected_team if selected_team != "All" else selected_league if selected_league != "All" else "All teams"
    summary, technique_mix, outcome_mix = build_summary_tables(filtered)

    section_header(f"{scope} Dashboard")
    c1, c2, c3 = st.columns([1.35, 1, 1])
    with c1:
        render_analyst_table(summary.head(12), height=300)
    with c2:
        render_analyst_table(technique_mix.head(12), height=300)
    with c3:
        render_analyst_table(outcome_mix.head(12), height=300)

    section_header("Notes")
    insight_cols = st.columns(2)
    for idx, insight in enumerate(generate_set_piece_insights(filtered, label)[:4]):
        with insight_cols[idx % 2]:
            st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

    section_header("Charts")
    qr1, qr2, qr3 = st.columns(3)
    with qr1:
        render_plotly_visual(categorical_breakdown_figure(filtered, "Taker", "Top takers", top_n=8, color="#c1121f"), "Corners top takers", "corners_top_takers_png")
    with qr2:
        render_plotly_visual(categorical_breakdown_figure(filtered, "Shot outcome", "Shot outcomes", top_n=8, color="#1d4ed8"), "Corners shot outcomes", "corners_shot_outcomes_png")
    with qr3:
        render_plotly_visual(minute_distribution_figure(filtered, "Minute distribution"), "Corners minute distribution", "corners_minute_distribution_png")

    section_header("Pitch")
    pitch_left, pitch_right = st.columns(2)
    with pitch_left:
        render_mpl_visual(mplsoccer_delivery_figure(filtered, label), "Corners delivery map", "corners_delivery_map_png")
    with pitch_right:
        render_mpl_visual(mplsoccer_shot_figure(filtered, label), "Corners shot quality", "corners_shot_quality_png")
    render_mpl_visual(mplsoccer_delivery_sp_outcome_figure(filtered, label), "Corners delivery map SP outcomes", "corners_delivery_map_sp_outcomes_png")

    section_header("Boards")
    board_left, board_right = st.columns(2)
    with board_left:
        render_analyst_table(build_taker_leaderboard(filtered).head(20), height=360)
    with board_right:
        render_analyst_table(build_shooter_leaderboard(filtered).head(20), height=360)
    render_analyst_table(build_pattern_library(filtered).head(30), height=360)

    with st.expander("Report", expanded=False):
        pdf_teams = ["All"]
        if "Team" in filtered.columns:
            pdf_teams += _safe_sorted(filtered["Team"])
        if st.session_state.get("corners_pdf_team") not in pdf_teams:
            st.session_state["corners_pdf_team"] = "All"
        pdf_team = st.selectbox("Report team", pdf_teams, key="corners_pdf_team")
        opponent = st.text_input("Opponent / report label", value="", key="corners_pdf_label")
        pdf_filtered = filtered.copy()
        if pdf_team != "All" and "Team" in pdf_filtered.columns:
            pdf_filtered = pdf_filtered[pdf_filtered["Team"].astype(str).eq(pdf_team)].copy()
        pdf_label = f"{label} - {pdf_team}" if pdf_team != "All" else label
        safe_base = opponent.strip() or pdf_label
        safe_name = safe_base.lower().replace(" ", "_").replace("/", "-")
        st.info("PDF generation may take a few seconds.")
        st.download_button(
            "Download pre-match PDF",
            data=_cached_report_pdf(pdf_filtered, pdf_label, opponent.strip()),
            file_name=f"{safe_name}_set_piece_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with st.expander("Rows", expanded=False):
        display_cols = [c for c in [
            "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
            "Defensive_setup", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob",
            "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=520)
