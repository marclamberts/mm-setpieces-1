
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PITCH_LENGTH = 120
PITCH_WIDTH = 80
HALF_START = 60

SP_MAP = {
    "Corners": "Allsvenskan - Corners 2025.xlsx",
    "Freekicks": "Allsvenskan - Freekicks 2025.xlsx",
    "Throw ins": "Allsvenskan - Throw ins 2025.xlsx",
}

BASE_DIR = Path(__file__).resolve().parent


def _candidate_paths(filename: str) -> list[Path]:
    return [
        BASE_DIR / filename,
        BASE_DIR.parent / filename,
        Path(filename),
    ]


def _read_excel_if_exists(filename: str) -> pd.DataFrame:
    for path in _candidate_paths(filename):
        if path.exists():
            return pd.read_excel(path)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_corner_data() -> pd.DataFrame:
    return _read_excel_if_exists(SP_MAP["Corners"])


@st.cache_data(show_spinner=False)
def load_sp_data(label: str) -> pd.DataFrame:
    filename = SP_MAP.get(label)
    if not filename:
        return pd.DataFrame()
    return _read_excel_if_exists(filename)


def _safe_col(df: pd.DataFrame, name: str, fallback=None):
    if name in df.columns:
        return df[name]
    return fallback


def _safe_sorted(values: pd.Series | list | None) -> list[str]:
    if values is None:
        return []
    ser = pd.Series(values)
    return sorted([str(v) for v in ser.dropna().astype(str).unique().tolist() if str(v).strip()])


def prepare_sp_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    mappings = {
        "Technique": [("inswing_outswing", "Unknown"), ("Technique", "Unknown")],
        "Delivery height": [("delivery_type", "Unknown"), ("Delivery height", "Unknown")],
        "Delivery outcome": [("delivery_outcome", "Unknown"), ("Delivery outcome", "Unknown")],
        "Shot outcome": [("shot.outcome.name", "No shot"), ("Shot outcome", "No shot")],
        "Shot body part": [("shot.body_part.name", "Unknown"), ("Shot body part", "Unknown")],
        "Defensive setup": [("Defensive_setup", "Unknown"), ("Defensive setup", "Unknown")],
        "Shooter": [("Shooter", "Unknown")],
        "Taker": [("Taker", "Unknown")],
        "League": [("League", "Allsvenskan")],
        "Team": [("Team", "Unknown")],
        "Match": [("Match", "Unknown")],
    }

    for target, options in mappings.items():
        if target in df.columns:
            df[target] = df[target].fillna(options[0][1] if options else "Unknown")
            continue
        created = False
        for source, default in options:
            if source in df.columns:
                df[target] = df[source].fillna(default)
                created = True
                break
        if not created:
            df[target] = options[0][1] if options else "Unknown"

    for numeric_col in [
        "minute", "second", "match_id", "match_rank", "xg",
        "shot_x", "shot_y", "delivery_end_x", "delivery_end_y"
    ]:
        if numeric_col in df.columns:
            df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")

    if "xg" not in df.columns:
        for alt in ["shot.statsbomb_xg", "shot_statsbomb_xg"]:
            if alt in df.columns:
                df["xg"] = pd.to_numeric(df[alt], errors="coerce")
                break
        else:
            df["xg"] = 0.0
    df["xg"] = pd.to_numeric(df["xg"], errors="coerce").fillna(0.0)

    if "shot_x" not in df.columns:
        if "shot_location_x" in df.columns:
            df["shot_x"] = pd.to_numeric(df["shot_location_x"], errors="coerce")
        else:
            df["shot_x"] = np.nan
    if "shot_y" not in df.columns:
        if "shot_location_y" in df.columns:
            df["shot_y"] = pd.to_numeric(df["shot_location_y"], errors="coerce")
        else:
            df["shot_y"] = np.nan

    if "delivery_end_x" not in df.columns:
        for alt in ["end_x", "delivery_end_x"]:
            if alt in df.columns:
                df["delivery_end_x"] = pd.to_numeric(df[alt], errors="coerce")
                break
        else:
            df["delivery_end_x"] = np.nan

    if "delivery_end_y" not in df.columns:
        for alt in ["end_y", "delivery_end_y"]:
            if alt in df.columns:
                df["delivery_end_y"] = pd.to_numeric(df[alt], errors="coerce")
                break
        else:
            df["delivery_end_y"] = np.nan

    if "side" not in df.columns:
        if "y" in df.columns:
            mid = PITCH_WIDTH / 2
            df["side"] = np.where(pd.to_numeric(df["y"], errors="coerce") <= mid, "Left", "Right")
        else:
            df["side"] = "Unknown"

    if "is_shot" not in df.columns:
        df["is_shot"] = df[["shot_x", "shot_y"]].notna().all(axis=1)

    if "is_goal" not in df.columns:
        df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

    if "game_period" not in df.columns:
        minute = pd.to_numeric(df.get("minute", pd.Series(dtype=float)), errors="coerce").fillna(0)
        bins = [-1, 15, 30, 45, 60, 75, 200]
        labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
        df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

    if "match_rank" not in df.columns:
        if "match_id" in df.columns:
            match_order = (
                df[["match_id"]]
                .dropna()
                .drop_duplicates()
                .sort_values("match_id", ascending=False)
                .reset_index(drop=True)
            )
            match_order["match_rank"] = range(1, len(match_order) + 1)
            df = df.merge(match_order, on="match_id", how="left")
        else:
            df["match_rank"] = 999

    return df


def vertical_coords_from_statsbomb(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")


def corner_origin_xy(side: str) -> tuple[float, float]:
    return (0.0, 120.0) if str(side).lower() == "left" else (80.0, 120.0)


def add_half_vertical_pitch_layout(fig: go.Figure, title: str, pitch_color: str = "white", height: int = 620) -> go.Figure:
    fig.update_xaxes(range=[0, PITCH_WIDTH], visible=False)
    fig.update_yaxes(range=[HALF_START, PITCH_LENGTH], visible=False, scaleanchor="x", scaleratio=1)

    penalty_left = (PITCH_WIDTH / 2) - 22
    penalty_right = (PITCH_WIDTH / 2) + 22
    six_left = (PITCH_WIDTH / 2) - 10
    six_right = (PITCH_WIDTH / 2) + 10

    shapes = [
        dict(type="rect", x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=PITCH_LENGTH, line=dict(width=2, color="#1e293b")),
        dict(type="line", x0=0, y0=HALF_START, x1=PITCH_WIDTH, y1=HALF_START, line=dict(width=2, color="#94a3b8")),
        dict(type="rect", x0=penalty_left, y0=102, x1=penalty_right, y1=120, line=dict(width=1.6, color="#1e293b")),
        dict(type="rect", x0=six_left, y0=114, x1=six_right, y1=120, line=dict(width=1.6, color="#1e293b")),
        dict(type="line", x0=36, y0=120, x1=44, y1=120, line=dict(width=3, color="#1e293b")),
        dict(type="circle", x0=39.5, y0=107.5, x1=40.5, y1=108.5, line=dict(width=1, color="#1e293b"), fillcolor="#1e293b"),
        dict(type="circle", x0=34, y0=102, x1=46, y1=114, line=dict(width=1.2, color="#1e293b")),
    ]

    fig.update_layout(
        title=title,
        shapes=shapes,
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        plot_bgcolor=pitch_color,
        paper_bgcolor=pitch_color,
        legend_title_text="",
    )
    return fig


def shotmap_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    shots = df[df["shot_x"].notna() & df["shot_y"].notna()].copy()
    shots = shots[pd.to_numeric(shots["shot_x"], errors="coerce") >= HALF_START]

    if shots.empty:
        fig.add_annotation(text="No shots for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

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
                    opacity=0.78,
                    line=dict(width=1, color="white"),
                ),
                customdata=np.stack(
                    [
                        part["Shooter"].fillna("Unknown"),
                        part["Shot outcome"].fillna("Unknown"),
                        part["xg"].fillna(0).round(3),
                        part["Match"].fillna("Unknown"),
                    ],
                    axis=1,
                ),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<extra></extra>",
            )
        )

    return add_half_vertical_pitch_layout(fig, title)


def delivery_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data available", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    deliveries = df[df["delivery_end_x"].notna() & df["delivery_end_y"].notna()].copy()
    deliveries = deliveries[pd.to_numeric(deliveries["delivery_end_x"], errors="coerce") >= HALF_START]

    if deliveries.empty:
        fig.add_annotation(text="No deliveries for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
        return add_half_vertical_pitch_layout(fig, title)

    sample = deliveries.copy()
    if len(sample) > 250:
        sample = sample.sample(250, random_state=7)

    sample["vx_end"], sample["vy_end"] = vertical_coords_from_statsbomb(sample["delivery_end_x"], sample["delivery_end_y"])

    color_map = {
        "Inswinging": "#2563eb",
        "Outswinging": "#f59e0b",
        "Straight": "#7c3aed",
        "Unknown": "#94a3b8",
    }

    for tech, part in sample.groupby("Technique", dropna=False):
        color = color_map.get(str(tech), "#7c3aed")

        for _, row in part.iterrows():
            start_x, start_y = corner_origin_xy(row.get("side", "Left"))
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
                name=str(tech),
                marker=dict(size=10, color=color, opacity=0.84, line=dict(width=0.8, color="white")),
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

    fig.add_trace(
        go.Scatter(
            x=[0, 80],
            y=[120, 120],
            mode="markers",
            name="Corner spot",
            marker=dict(size=11, color="#0f172a", symbol="circle-open", line=dict(width=2, color="#0f172a")),
            hoverinfo="skip",
        )
    )

    return add_half_vertical_pitch_layout(fig, title)


def build_summary_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    group_col = "Team" if "Team" in df.columns else None
    if group_col:
        summary = (
            df.groupby(group_col, dropna=False)
            .agg(
                Matches=("match_id", "nunique") if "match_id" in df.columns else ("Team", "size"),
                Set_Pieces=("possession", "nunique") if "possession" in df.columns else ("Team", "size"),
                Shots=("is_shot", "sum"),
                Goals=("is_goal", "sum"),
                Total_xG=("xg", "sum"),
                Avg_xG=("xg", "mean"),
            )
            .reset_index()
            .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
        )
    else:
        summary = pd.DataFrame({
            "Set_Pieces": [len(df)],
            "Shots": [int(df["is_shot"].sum())],
            "Goals": [int(df["is_goal"].sum())],
            "Total_xG": [float(df["xg"].sum())],
            "Avg_xG": [float(df["xg"].mean()) if len(df) else 0],
        })

    if "Shots" in summary.columns and "Goals" in summary.columns:
        summary["Shot conversion %"] = np.where(summary["Shots"] > 0, (summary["Goals"] / summary["Shots"] * 100).round(1), 0)
    if "Avg_xG" in summary.columns:
        summary["Avg_xG"] = pd.to_numeric(summary["Avg_xG"], errors="coerce").fillna(0).round(3)
    if "Total_xG" in summary.columns:
        summary["Total_xG"] = pd.to_numeric(summary["Total_xG"], errors="coerce").fillna(0).round(2)

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


def kpi_row(df: pd.DataFrame) -> None:
    sequences = 0
    if not df.empty:
        if set(["match_id", "possession", "Team"]).issubset(df.columns):
            sequences = int(df[["match_id", "possession", "Team"]].drop_duplicates().shape[0])
        else:
            sequences = int(len(df))
    shots = int(df["is_shot"].sum()) if not df.empty and "is_shot" in df.columns else 0
    goals = int(df["is_goal"].sum()) if not df.empty and "is_goal" in df.columns else 0
    total_xg = float(df["xg"].sum()) if not df.empty and "xg" in df.columns else 0.0
    shot_rate = (shots / sequences * 100) if sequences else 0.0
    goal_rate = (goals / shots * 100) if shots else 0.0
    matches = int(df["match_id"].nunique()) if not df.empty and "match_id" in df.columns else 0

    cols = st.columns(6)
    metrics = [
        ("Matches", matches),
        ("Set Pieces", sequences),
        ("Shots", shots),
        ("Goals", goals),
        ("Shot rate", f"{shot_rate:.1f}%"),
        ("Total xG", f"{total_xg:.2f}"),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    st.caption(f"Goal conversion from shots: {goal_rate:.1f}%")


def info_panel(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No rows match the current filters.")
        return
    counts = []
    if "Technique" in df.columns:
        top_technique = df["Technique"].fillna("Unknown").value_counts().head(1)
        if not top_technique.empty:
            counts.append(f"Most common technique: {top_technique.index[0]} ({int(top_technique.iloc[0])})")
    if "Taker" in df.columns:
        top_taker = df["Taker"].fillna("Unknown").value_counts().head(1)
        if not top_taker.empty:
            counts.append(f"Most frequent taker: {top_taker.index[0]} ({int(top_taker.iloc[0])})")
    if counts:
        st.caption(" · ".join(counts))
