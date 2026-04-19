from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import load_corner_data

st.set_page_config(page_title="Michael Mackin Set Piece | Corners", page_icon="⚽", layout="wide")

PITCH_LENGTH = 120
PITCH_WIDTH = 80
HALF_START = 60
SIDE_SPLIT = PITCH_WIDTH / 2

st.markdown(
    """
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
        .section-title {font-size: 1.02rem; font-weight: 700; color: #0f172a; margin-bottom: 0.55rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])


@st.cache_data(show_spinner=False)
def load_corner_page_data() -> pd.DataFrame:
    df = load_corner_data().copy()

    df["Technique"] = df["inswing_outswing"].fillna("Unknown")
    df["Delivery height"] = df["delivery_type"].fillna("Unknown")
    df["Delivery outcome"] = df["delivery_outcome"].fillna("Unknown")
    df["Shot outcome"] = df["shot.outcome.name"].fillna("No shot")
    df["Shot body part"] = df["shot.body_part.name"].fillna("Unknown")
    df["Defensive setup"] = df["Defensive_setup"].fillna("Unknown")
    df["Shooter"] = df["Shooter"].fillna("Unknown")
    df["Taker"] = df["Taker"].fillna("Unknown")
    df["League"] = df.get("League", "Allsvenskan")

    return df


def filter_corner_data(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Corners filters")

    teams = ["All"] + _safe_sorted(df["Team"])
    leagues = ["All"] + _safe_sorted(df["League"])
    sides = ["All"] + _safe_sorted(df["side"])
    periods = ["All"] + ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
    techniques = _safe_sorted(df["Technique"])
    heights = _safe_sorted(df["Delivery height"])
    takers = _safe_sorted(df["Taker"])
    shot_outcomes = _safe_sorted(df["Shot outcome"])

    team = st.sidebar.selectbox("Team", teams)
    league = st.sidebar.selectbox("League", leagues)
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], horizontal=True)
    side = st.sidebar.radio("Side", sides, horizontal=True)
    time_in_game = st.sidebar.selectbox("Time in the game", periods)

    st.sidebar.markdown("---")
    minute_range = st.sidebar.slider("Minute range", 0, 95, (0, 95))
    taker_filter = st.sidebar.multiselect("Taker", takers)
    technique_filter = st.sidebar.multiselect("Delivery technique", techniques)
    height_filter = st.sidebar.multiselect("Delivery height", heights)
    shot_outcome_filter = st.sidebar.multiselect("Shot outcome", shot_outcomes)
    only_shots = st.sidebar.checkbox("Only corners that ended with a shot", value=False)

    filtered = df.copy()

    if team != "All":
        filtered = filtered[filtered["Team"] == team]
    if league != "All":
        filtered = filtered[filtered["League"] == league]
    if sample == "Last 10 games":
        filtered = filtered[filtered["match_rank"] <= 10]
    if side != "All":
        filtered = filtered[filtered["side"] == side]
    if time_in_game != "All":
        filtered = filtered[filtered["game_period"] == time_in_game]

    filtered = filtered[filtered["minute"].between(minute_range[0], minute_range[1])]

    if taker_filter:
        filtered = filtered[filtered["Taker"].isin(taker_filter)]
    if technique_filter:
        filtered = filtered[filtered["Technique"].isin(technique_filter)]
    if height_filter:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)]
    if shot_outcome_filter:
        filtered = filtered[filtered["Shot outcome"].isin(shot_outcome_filter)]
    if only_shots:
        filtered = filtered[filtered["is_shot"]]

    return filtered


def add_vertical_pitch_layout(fig: go.Figure, title: str, pitch_color: str = "white") -> go.Figure:
    # Vertical HALF pitch using StatsBomb 120x80, cropped from midfield (60) to goal line (120)
    fig.update_xaxes(range=[0, PITCH_WIDTH], visible=False)
    fig.update_yaxes(range=[HALF_START, PITCH_LENGTH], visible=False, scaleanchor="x", scaleratio=1)

    penalty_left = (PITCH_WIDTH / 2) - 22
    penalty_right = (PITCH_WIDTH / 2) + 22
    six_left = (PITCH_WIDTH / 2) - 10
    six_right = (PITCH_WIDTH / 2) + 10

    shapes = [
        # Half pitch boundary
        dict(
            type="rect",
            x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=PITCH_LENGTH,
            line=dict(width=2, color="#1e293b")
        ),

        # Midfield cut line
        dict(
            type="line",
            x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=HALF_START,
            line=dict(width=2, color="#94a3b8")
        ),

        # Penalty area
        dict(
            type="rect",
            x0=penalty_left, y0=102, x1=penalty_right, y1=120,
            line=dict(width=1.6, color="#1e293b")
        ),

        # Six-yard box
        dict(
            type="rect",
            x0=six_left, y0=114, x1=six_right, y1=120,
            line=dict(width=1.6, color="#1e293b")
        ),

        # Goal
        dict(
            type="line",
            x0=36, y0=120, x1=44, y1=120,
            line=dict(width=3, color="#1e293b")
        ),

        # Penalty spot
        dict(
            type="circle",
            x0=39.5, y0=107.5, x1=40.5, y1=108.5,
            line=dict(width=1, color="#1e293b"),
            fillcolor="#1e293b"
        ),

        # Penalty arc
        dict(
            type="circle",
            x0=34, y0=102, x1=46, y1=114,
            line=dict(width=1.2, color="#1e293b")
        ),
    ]

    fig.update_layout(
        title=title,
        shapes=shapes,
        margin=dict(l=10, r=10, t=50, b=10),
        height=620,
        plot_bgcolor=pitch_color,
        paper_bgcolor=pitch_color,
        legend_title_text="",
    )
    return fig


def corner_origin_xy(side: str) -> tuple[float, float]:
    # Vertical pitch coordinates: x is width (0-80), y is length (0-120)
    return (0.0, 120.0) if str(side).lower() == "left" else (80.0, 120.0)


def vertical_coords_from_statsbomb(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    # Convert StatsBomb coordinates:
    # original: x=length (0-120), y=width (0-80)
    # vertical plot: x=width, y=length
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")


def shotmap_vertical(df: pd.DataFrame, title: str) -> go.Figure:
    shots = df[df["shot_x"].notna() & df["shot_y"].notna()].copy()

    # Keep only shots in attacking half
    shots = shots[pd.to_numeric(shots["shot_x"], errors="coerce") >= HALF_START]

    fig = go.Figure()

    if shots.empty:
        fig.add_annotation(
            text="No shots for current filter",
            x=40, y=90,
            showarrow=False,
            font=dict(size=18, color="#64748b")
        )
        return add_vertical_pitch_layout(fig, title)

    shots["vx"], shots["vy"] = vertical_coords_from_statsbomb(shots["shot_x"], shots["shot_y"])
    shots["Result"] = np.where(shots["is_goal"], "Goal", "Shot")
    color_map = {"Shot": "#2563eb", "Goal": "#16a34a"}

    for result in ["Shot", "Goal"]:
        part = shots[shots["Result"] == result]
        if part.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=part["vx"],
                y=part["vy"],
                mode="markers",
                name=result,
                marker=dict(
                    size=np.clip(part["xg"].fillna(0) * 95 + 10, 10, 38),
                    color=color_map[result],
                    opacity=0.75,
                    line=dict(width=1, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Shooter"].fillna("Unknown"),
                        part["Shot outcome"],
                        part["xg"].fillna(0).round(3),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    return add_vertical_pitch_layout(fig, title)


def delivery_map_vertical(df: pd.DataFrame, title: str) -> go.Figure:
    deliveries = df[df["delivery_end_x"].notna() & df["delivery_end_y"].notna()].copy()

    # Keep only deliveries ending in attacking half
    deliveries = deliveries[pd.to_numeric(deliveries["delivery_end_x"], errors="coerce") >= HALF_START]

    fig = go.Figure()

    if deliveries.empty:
        fig.add_annotation(
            text="No deliveries for current filter",
            x=40, y=90,
            showarrow=False,
            font=dict(size=18, color="#64748b")
        )
        return add_vertical_pitch_layout(fig, title)

    sample = deliveries.copy()
    if len(sample) > 250:
        sample = sample.sample(250, random_state=7)

    sample["vx_end"], sample["vy_end"] = vertical_coords_from_statsbomb(
        sample["delivery_end_x"], sample["delivery_end_y"]
    )

    color_map = {
        "Inswinging": "#2563eb",
        "Outswinging": "#f59e0b",
        "Straight": "#7c3aed",
        "Unknown": "#94a3b8",
    }

    for tech, part in sample.groupby("Technique"):
        color = color_map.get(tech, "#7c3aed")

        for _, row in part.iterrows():
            start_x, start_y = corner_origin_xy(row["side"])
            fig.add_trace(
                go.Scatter(
                    x=[start_x, row["vx_end"]],
                    y=[start_y, row["vy_end"]],
                    mode="lines",
                    line=dict(color=color, width=1.3),
                    opacity=0.28,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        fig.add_trace(
            go.Scatter(
                x=part["vx_end"],
                y=part["vy_end"],
                mode="markers",
                name=tech,
                marker=dict(
                    size=10,
                    color=color,
                    opacity=0.82,
                    line=dict(width=0.8, color="white")
                ),
                customdata=np.stack(
                    [
                        part["Taker"].fillna("Unknown"),
                        part["Delivery height"].fillna("Unknown"),
                        part["Delivery outcome"].fillna("Unknown"),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    # Corner spots
    fig.add_trace(
        go.Scatter(
            x=[0, 80],
            y=[120, 120],
            mode="markers",
            name="Corner spot",
            marker=dict(
                size=11,
                color="#0f172a",
                symbol="circle-open",
                line=dict(width=2, color="#0f172a")
            ),
            hoverinfo="skip",
        )
    )

    return add_vertical_pitch_layout(fig, title)


def build_general_info(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = (
        df.groupby("Team", dropna=False)
        .agg(
            Matches=("match_id", "nunique"),
            Corners=("possession", "nunique"),
            Shots=("is_shot", "sum"),
            Goals=("is_goal", "sum"),
            Total_xG=("xg", "sum"),
            Avg_xG=("xg", "mean"),
        )
        .reset_index()
        .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
    )

    summary["Shot conversion %"] = np.where(
        summary["Shots"] > 0,
        (summary["Goals"] / summary["Shots"] * 100).round(1),
        0
    )
    summary["Avg_xG"] = summary["Avg_xG"].fillna(0).round(3)
    summary["Total_xG"] = summary["Total_xG"].fillna(0).round(2)

    technique_mix = (
        df.groupby(["Technique", "Delivery height"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    outcome_mix = (
        df.groupby(["Delivery outcome", "Shot outcome"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    return summary, technique_mix, outcome_mix


def render_kpis(df: pd.DataFrame) -> None:
    sequences = int(df[["match_id", "possession", "Team"]].drop_duplicates().shape[0]) if not df.empty else 0
    shots = int(df["is_shot"].sum()) if not df.empty else 0
    goals = int(df["is_goal"].sum()) if not df.empty else 0
    total_xg = float(df["xg"].sum()) if not df.empty else 0.0
    shot_rate = (shots / sequences * 100) if sequences else 0.0
    goal_rate = (goals / shots * 100) if shots else 0.0

    cols = st.columns(6)
    metrics = [
        ("Matches", int(df["match_id"].nunique()) if not df.empty else 0),
        ("Corners", sequences),
        ("Shots", shots),
        ("Goals", goals),
        ("Shot rate", f"{shot_rate:.1f}%"),
        ("Total xG", f"{total_xg:.2f}"),
    ]

    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

    st.caption(f"Goal conversion from shots: {goal_rate:.1f}%")


def render_page() -> None:
    df = load_corner_page_data()
    filtered = filter_corner_data(df)

    st.markdown(
        """
        <div class='page-card'>
            <div class='mini-title'>Allsvenskan 2025 · Set piece analysis</div>
            <div class='main-title'>Corners</div>
            <div class='copy'>
                Vertical half-pitch analysis of corner creation, delivery profiles, and resulting shots.
                Use the filters to isolate specific takers, delivery types, game states, or shot outcomes.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "League is set to Allsvenskan by default. 'Last 10 games' is approximated using the highest match_id values because the file does not include explicit match dates."
    )

    render_kpis(filtered)

    general_info, technique_mix, outcome_mix = build_general_info(filtered)

    st.markdown("### General information")
    c1, c2, c3 = st.columns([1.4, 1, 1])

    with c1:
        st.dataframe(general_info, use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(technique_mix, use_container_width=True, hide_index=True)
    with c3:
        st.dataframe(outcome_mix, use_container_width=True, hide_index=True)

    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            shotmap_vertical(filtered, "Corner shotmap · vertical half pitch"),
            use_container_width=True
        )

    with right:
        st.plotly_chart(
            delivery_map_vertical(filtered, "Corner delivery map · vertical half pitch"),
            use_container_width=True
        )

    st.markdown("### Event details")
    display_cols = [
        "Match", "Team", "Taker", "Shooter", "side", "minute", "second",
        "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome"
    ]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)


render_page()