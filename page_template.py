
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils import (
    build_summary_tables,
    delivery_map_figure,
    hero_block,
    info_panel,
    inject_app_style,
    kpi_row,
    load_sp_data,
    polish_plotly_figure,
    prepare_sp_dataframe,
    filter_by_sp_type,
    section_header,
    shotmap_figure,
    starting_location_map_figure,
)

def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])

def _filter_page_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    st.sidebar.header(f"{label} filters")

    teams = ["All"] + _safe_sorted(df["Team"]) if "Team" in df.columns else ["All"]
    leagues = ["All"] + _safe_sorted(df["League"]) if "League" in df.columns else ["All"]
    sides = ["All"] + _safe_sorted(df["side"]) if "side" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    techniques = _safe_sorted(df["Technique"]) if "Technique" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shot_outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    team = st.sidebar.selectbox("Team", teams)
    league = st.sidebar.selectbox("League", leagues)
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], horizontal=True)
    side = st.sidebar.radio("Side", sides, horizontal=True)
    time_in_game = st.sidebar.selectbox("Time in the game", periods)

    st.sidebar.markdown("---")
    minute_min = 0
    minute_max = 95
    if "minute" in df.columns and not df["minute"].dropna().empty:
        minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min())
        minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max()))
    minute_range = st.sidebar.slider("Minute range", minute_min, minute_max, (minute_min, minute_max))

    taker_filter = st.sidebar.multiselect("Taker", takers)
    technique_filter = st.sidebar.multiselect("Delivery technique", techniques)
    height_filter = st.sidebar.multiselect("Delivery height", heights)
    shot_outcome_filter = st.sidebar.multiselect("Shot outcome", shot_outcomes)
    only_shots = st.sidebar.checkbox(f"Only {label.lower()} ending with a shot", value=False)

    filtered = df.copy()
    if team != "All" and "Team" in filtered.columns:
        filtered = filtered[filtered["Team"] == team]
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

    return filtered

def render_page(label: str) -> None:
    st.set_page_config(page_title=f"Michael Mackin Set Piece | {label}", page_icon="⚽", layout="wide")
    inject_app_style()

    raw = load_sp_data(label)
    if raw.empty:
        hero_block(
            "Set piece analysis",
            label,
            "No source rows were found for this page in the bundled workbook(s).",
        )
        return

    df = prepare_sp_dataframe(raw, label=label)
    df = filter_by_sp_type(df, label)
    filtered = _filter_page_data(df, label)
    filtered = filter_by_sp_type(filtered, label)

    hero_block(
        "Set piece analysis",
        label,
        "Filter and explore delivery profiles, outcomes, and resulting shots. "
        "The plots use a compact vertical half-pitch layout with StatsBomb 120x80 coordinates.",
    )

    if label == "Corners":
        st.caption("Corners use Allsvenskan - Corners 2025.xlsx. 'Last 10 games' is approximated via descending match_id when dates are missing.")
    else:
        st.caption(f"{label} use SWE SP.xlsx filtered by SP_Type. Delivery maps use available shot end locations where explicit delivery end coordinates are not present.")

    kpi_row(filtered)
    info_panel(filtered)

    summary, technique_mix, outcome_mix = build_summary_tables(filtered)

    section_header("General Information", "Team summary, delivery mix, and outcome mix")
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        st.dataframe(summary, use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(technique_mix, use_container_width=True, hide_index=True)
    with c3:
        st.dataframe(outcome_mix, use_container_width=True, hide_index=True)

    section_header("Pitch Maps", "Shot locations and delivery/start locations")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(polish_plotly_figure(shotmap_figure(filtered, f"{label} shotmap · vertical half pitch")), use_container_width=True)
    with right:
        if label == "Corners":
            st.plotly_chart(polish_plotly_figure(delivery_map_figure(filtered, f"{label} delivery map · vertical half pitch")), use_container_width=True)
        else:
            st.plotly_chart(polish_plotly_figure(starting_location_map_figure(filtered, f"{label} starting location map · vertical half pitch")), use_container_width=True)

    section_header("Event Details", f"{len(filtered):,} rows in the current filter")
    display_cols = [c for c in [
        "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
        "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome", "timestamp"
    ] if c in filtered.columns]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
