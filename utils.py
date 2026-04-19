
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PITCH_LENGTH = 120
PITCH_WIDTH = 80
HALF_START = 60
BASE_DIR = Path(__file__).resolve().parent

def _candidate_paths(filename: str) -> list[Path]:
    return [BASE_DIR / filename, BASE_DIR.parent / filename, Path(filename)]

def _read_excel_if_exists(filename: str, sheet_name=0) -> pd.DataFrame:
    for path in _candidate_paths(filename):
        if path.exists():
            return pd.read_excel(path, sheet_name=sheet_name)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_corner_data() -> pd.DataFrame:
    return _read_excel_if_exists("Allsvenskan - Corners 2025.xlsx").copy()

@st.cache_data(show_spinner=False)
def load_swe_sp_data() -> pd.DataFrame:
    return _read_excel_if_exists("SWE SP.xlsx").copy()

@st.cache_data(show_spinner=False)
def load_sp_data(label: str) -> pd.DataFrame:
    if label == "Corners":
        return load_corner_data().copy()

    raw = load_swe_sp_data().copy()
    if raw.empty or "SP_Type" not in raw.columns:
        return pd.DataFrame()

    mapping = {
        "Freekicks": "From Free Kick",
        "Throw ins": "From Throw In",
    }
    sp_type = mapping.get(label)
    if sp_type:
        return raw[raw["SP_Type"].astype(str).str.strip().eq(sp_type)].copy()
    return pd.DataFrame()

def _ensure_column(df: pd.DataFrame, target: str, candidates: list[str], default=np.nan):
    if target in df.columns:
        return
    for cand in candidates:
        if cand in df.columns:
            df[target] = df[cand]
            return
    df[target] = default

def prepare_sp_dataframe(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    if label == "Corners":
        _ensure_column(df, "Team", ["Team", "pass_team_name", "shot_team_name"], "Unknown")
        _ensure_column(df, "Match", ["Match"], "Unknown")
        _ensure_column(df, "minute", ["minute", "Minute"], 0)
        _ensure_column(df, "second", ["second", "Second"], 0)
        _ensure_column(df, "Technique", ["Technique", "pass.technique.name"], "Unknown")
        _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name"], "Unknown")
        _ensure_column(df, "Delivery outcome", ["Delivery outcome", "pass.outcome.name", "SP_outcome"], "Unknown")
        _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name"], "No shot")
        _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
        _ensure_column(df, "Taker", ["Taker"], "Unknown")
        _ensure_column(df, "League", ["League"], "Allsvenskan")
        _ensure_column(df, "shot_x", ["shot_x", "shot_location_x"], np.nan)
        _ensure_column(df, "shot_y", ["shot_y", "shot_location_y"], np.nan)
        _ensure_column(df, "delivery_end_x", ["delivery_end_x", "pass_end_location_x", "end_x"], np.nan)
        _ensure_column(df, "delivery_end_y", ["delivery_end_y", "pass_end_location_y", "end_y"], np.nan)
        _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg", "shot_statsbomb_xg"], 0.0)

        for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Shooter", "Taker", "League"]:
            fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
            df[col] = df[col].fillna(fill)

        for col in ["minute", "second", "match_id", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "side" not in df.columns:
            if "pass_location_y" in df.columns:
                py = pd.to_numeric(df["pass_location_y"], errors="coerce")
                df["side"] = np.where(py <= 40, "Left", "Right")
            else:
                df["side"] = "Unknown"

        if "is_shot" not in df.columns:
            df["is_shot"] = df[["shot_x", "shot_y"]].notna().all(axis=1)
        if "is_goal" not in df.columns:
            df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

        if "game_period" not in df.columns:
            minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
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

    _ensure_column(df, "Team", ["Team", "team.name"], "Unknown")
    _ensure_column(df, "Match", ["Match"], "Unknown")
    _ensure_column(df, "Technique", ["Technique", "type.name"], "Unknown")
    _ensure_column(df, "Delivery height", ["Delivery height", "pass.height.name"], "Unknown")
    _ensure_column(df, "Delivery outcome", ["Delivery outcome", "Metrics"], "Unknown")
    _ensure_column(df, "Shot outcome", ["Shot outcome", "shot.outcome.name"], "No shot")
    _ensure_column(df, "Taker", ["Taker"], "Unknown")
    _ensure_column(df, "Shooter", ["Shooter"], "Unknown")
    _ensure_column(df, "League", ["League"], "Allsvenskan")
    _ensure_column(df, "xg", ["xg", "shot.statsbomb_xg"], 0.0)

    if "Match" in df.columns and df["Match"].isna().all() and "match_id" in df.columns:
        df["Match"] = "Match " + df["match_id"].astype(str)

    for col in ["Team", "Match", "Technique", "Delivery height", "Delivery outcome", "Shot outcome", "Taker", "Shooter", "League"]:
        fill = "Allsvenskan" if col == "League" else ("No shot" if col == "Shot outcome" else "Unknown")
        df[col] = df[col].fillna(fill)

    if "location.pass" in df.columns:
        pass_xy = df["location.pass"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if pass_xy.shape[1] >= 2:
            df["pass_x"] = pd.to_numeric(pass_xy[0].str.strip(), errors="coerce")
            df["pass_y"] = pd.to_numeric(pass_xy[1].str.strip(), errors="coerce")

    if "side" not in df.columns:
        if "pass_y" in df.columns:
            df["side"] = np.where(df["pass_y"] <= 40, "Left", "Right")
        else:
            df["side"] = "Unknown"

    if "location.shot" in df.columns:
        shot_xy = df["location.shot"].astype(str).str.replace(r"[\[\]]", "", regex=True).str.split(",", expand=True)
        if shot_xy.shape[1] >= 2:
            df["shot_x"] = pd.to_numeric(shot_xy[0].str.strip(), errors="coerce")
            df["shot_y"] = pd.to_numeric(shot_xy[1].str.strip(), errors="coerce")

    _ensure_column(df, "shot_x", ["shot_x"], np.nan)
    _ensure_column(df, "shot_y", ["shot_y"], np.nan)
    _ensure_column(df, "delivery_end_x", ["delivery_end_x", "shot_x"], np.nan)
    _ensure_column(df, "delivery_end_y", ["delivery_end_y", "shot_y"], np.nan)

    if "minute" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            df["minute"] = pd.to_numeric(parts[0], errors="coerce").fillna(0) if parts.shape[1] >= 1 else 0
        else:
            df["minute"] = 0

    if "second" not in df.columns:
        if "timestamp" in df.columns:
            parts = df["timestamp"].astype(str).str.split(":", expand=True)
            df["second"] = pd.to_numeric(parts[2], errors="coerce").fillna(0) if parts.shape[1] >= 3 else 0
        else:
            df["second"] = 0

    for col in ["minute", "second", "match_id", "shot_x", "shot_y", "delivery_end_x", "delivery_end_y", "xg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "is_shot" not in df.columns:
        df["is_shot"] = df["shot_x"].notna() & df["shot_y"].notna()
    if "is_goal" not in df.columns:
        df["is_goal"] = df["Shot outcome"].astype(str).str.lower().eq("goal")

    if "game_period" not in df.columns:
        minute = pd.to_numeric(df["minute"], errors="coerce").fillna(0)
        bins = [-1, 15, 30, 45, 60, 75, 200]
        labels = ["0-15", "16-30", "31-45", "46-60", "61-75", "76+"]
        df["game_period"] = pd.cut(minute, bins=bins, labels=labels).astype(str)

    if "match_rank" not in df.columns:
        if "match_id" in df.columns:
            order = (
                df[["match_id"]]
                .dropna()
                .drop_duplicates()
                .sort_values("match_id", ascending=False)
                .reset_index(drop=True)
            )
            order["match_rank"] = range(1, len(order) + 1)
            df = df.merge(order, on="match_id", how="left")
        else:
            df["match_rank"] = 999
    return df

def vertical_coords_from_statsbomb(x: pd.Series, y: pd.Series) -> tuple[pd.Series, pd.Series]:
    return pd.to_numeric(y, errors="coerce"), pd.to_numeric(x, errors="coerce")

def restart_origin_xy(side: str) -> tuple[float, float]:
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
        fig.add_annotation(text="No deliveries with end locations for current filter", x=40, y=90, showarrow=False, font=dict(size=18, color="#64748b"))
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
            start_x, start_y = restart_origin_xy(row.get("side", "Left"))
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
                        part["Shot outcome"].fillna("Unknown"),
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
            name="Restart spot",
            marker=dict(size=11, color="#0f172a", symbol="circle-open", line=dict(width=2, color="#0f172a")),
            hoverinfo="skip",
        )
    )

    return add_half_vertical_pitch_layout(fig, title)

def build_summary_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if set(["match_id", "possession", "Team"]).issubset(df.columns):
        summary = (
            df.groupby("Team", dropna=False)
            .agg(
                Matches=("match_id", "nunique"),
                Set_Pieces=("possession", "nunique"),
                Shots=("is_shot", "sum"),
                Goals=("is_goal", "sum"),
                Total_xG=("xg", "sum"),
                Avg_xG=("xg", "mean"),
            )
            .reset_index()
            .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
        )
    else:
        summary = (
            df.groupby("Team", dropna=False)
            .agg(
                Matches=("Match", "nunique") if "Match" in df.columns else ("Team", "size"),
                Set_Pieces=("Team", "size"),
                Shots=("is_shot", "sum"),
                Goals=("is_goal", "sum"),
                Total_xG=("xg", "sum"),
                Avg_xG=("xg", "mean"),
            )
            .reset_index()
            .sort_values(["Total_xG", "Goals", "Shots"], ascending=False)
        )

    summary["Shot conversion %"] = np.where(summary["Shots"] > 0, (summary["Goals"] / summary["Shots"] * 100).round(1), 0)
    summary["Avg_xG"] = summary["Avg_xG"].fillna(0).round(3)
    summary["Total_xG"] = summary["Total_xG"].fillna(0).round(2)

    technique_mix = (
        df.groupby(["Technique", "Delivery height"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Technique", "Delivery height"]).issubset(df.columns) else pd.DataFrame()

    outcome_mix = (
        df.groupby(["Delivery outcome", "Shot outcome"], dropna=False)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    ) if set(["Delivery outcome", "Shot outcome"]).issubset(df.columns) else pd.DataFrame()

    return summary, technique_mix, outcome_mix

def kpi_row(df: pd.DataFrame) -> None:
    if not df.empty and set(["match_id", "possession", "Team"]).issubset(df.columns):
        sequences = int(df[["match_id", "possession", "Team"]].drop_duplicates().shape[0])
    else:
        sequences = int(len(df))
    shots = int(df["is_shot"].sum()) if not df.empty and "is_shot" in df.columns else 0
    goals = int(df["is_goal"].sum()) if not df.empty and "is_goal" in df.columns else 0
    total_xg = float(df["xg"].sum()) if not df.empty and "xg" in df.columns else 0.0
    shot_rate = (shots / sequences * 100) if sequences else 0.0
    goal_rate = (goals / shots * 100) if shots else 0.0
    matches = int(df["match_id"].nunique()) if not df.empty and "match_id" in df.columns else (int(df["Match"].nunique()) if not df.empty and "Match" in df.columns else 0)

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
    notes = []
    if "Technique" in df.columns:
        vc = df["Technique"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top technique: {vc.index[0]} ({int(vc.iloc[0])})")
    if "Taker" in df.columns:
        vc = df["Taker"].fillna("Unknown").value_counts().head(1)
        if not vc.empty:
            notes.append(f"Top taker: {vc.index[0]} ({int(vc.iloc[0])})")
    if notes:
        st.caption(" · ".join(notes))
