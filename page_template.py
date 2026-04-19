
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils import (
    build_summary_tables,
    delivery_map_figure,
    info_panel,
    kpi_row,
    load_sp_data,
    prepare_sp_dataframe,
    filter_by_sp_type,
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

    st.markdown(
        '''
        <style>
            .stApp {background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);}
            .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
            .page-card {
                background: rgba(255,255,255,0.97);
                border: 1px solid rgba(15,23,42,0.08);
                border-radius: 24px;
                padding: 1.4rem 1.45rem 1.15rem 1.45rem;
                box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
                margin-bottom: 1rem;
            }
            .mini-title {font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b;}
            .main-title {font-size: 2.25rem; font-weight: 800; color: #0f172a; margin: 0.2rem 0 0.35rem 0;}
            .copy {color: #475569; line-height: 1.65;}
        </style>
        ''',
        unsafe_allow_html=True,
    )

    raw = load_sp_data(label)
    if raw.empty:
        st.markdown(
            f'''
            <div class="page-card">
                <div class="mini-title">Set piece analysis</div>
                <div class="main-title">{label}</div>
                <div class="copy">No source rows were found for this page in the bundled workbook(s).</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
        return

    df = prepare_sp_dataframe(raw, label=label)
    df = filter_by_sp_type(df, label)
    filtered = _filter_page_data(df, label)
    filtered = filter_by_sp_type(filtered, label)

    st.markdown(
        f'''
        <div class="page-card">
            <div class="mini-title">Set piece analysis</div>
            <div class="main-title">{label}</div>
            <div class="copy">
                Filter and explore delivery profiles, outcomes, and resulting shots. The plots use a compact vertical half-pitch layout with StatsBomb 120×80 coordinates.
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if label == "Corners":
        st.caption("Corners use Allsvenskan - Corners 2025.xlsx. 'Last 10 games' is approximated via descending match_id when dates are missing.")
    else:
        st.caption(f"{label} use SWE SP.xlsx filtered by SP_Type. Delivery maps use available shot end locations where explicit delivery end coordinates are not present.")

    kpi_row(filtered)
    info_panel(filtered)

    summary, technique_mix, outcome_mix = build_summary_tables(filtered)

    st.markdown("### General information")
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        st.dataframe(summary, width="stretch", hide_index=True)
    with c2:
        st.dataframe(technique_mix, width="stretch", hide_index=True)
    with c3:
        st.dataframe(outcome_mix, width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left:
        st.plotly_chart(shotmap_figure(filtered, f"{label} shotmap · vertical half pitch"), width="stretch")
    with right:
        if label == "Corners":
            st.plotly_chart(delivery_map_figure(filtered, f"{label} delivery map · vertical half pitch"), width="stretch")
        else:
            st.plotly_chart(starting_location_map_figure(filtered, f"{label} starting location map · vertical half pitch"), width="stretch")

    st.markdown("### Event details")
    display_cols = [c for c in [
        "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
        "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome", "timestamp"
    ] if c in filtered.columns]
    st.dataframe(filtered[display_cols], width="stretch", hide_index=True)
