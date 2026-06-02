"""Shared data helpers, filter widgets, chart wrappers used across every section."""
from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    _data_files,
    _league_from_filename,
    _read_excel_if_exists,
    _with_league,
    load_prepared_sp_data,
    prematch_report_pdf_bytes,
    polish_plotly_figure,
    render_plotly_png_download,
    render_matplotlib_png_download,
    unique_start_events,
)

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False
    from mm_setpieces_1.utils import go  # type: ignore[attr-defined]

from mm_setpieces_1.utils import plotly_figure_png_bytes  # noqa: F401


APP_SECTIONS = ["Home", "Corners", "Freekicks", "Throw-ins", "HOPS", "League Comparison", "Delay Analysis", "Match Prep", "Data Justification"]

FILTER_PREFIXES = {
    "Corners": "corners",
    "Freekicks": "freekicks",
    "Throw-ins": "throwins",
    "HOPS": "hops",
    "League Comparison": "league_comparison",
    "Delay Analysis": "delay",
    "Match Prep": "match_prep",
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])


def _source_league_options(folder: str) -> list[str]:
    suffixes = (".parquet",) if folder in {"Corners", "SP", "HOPS"} else (".xlsx", ".xlsm", ".xls")
    return sorted({
        league
        for league in (_league_from_filename(path) for path in _data_files(folder, suffixes))
        if league and league != "Unknown"
    })


def _league_filter_options(df: pd.DataFrame, source_folder: str | None = None) -> list[str]:
    leagues = set(_safe_sorted(df["League"])) if "League" in df.columns else set()
    if source_folder:
        leagues.update(_source_league_options(source_folder))
    return ["All"] + sorted(leagues)


def _league_selectbox(label: str, options: list[str], key: str) -> str:
    if key in st.session_state and st.session_state[key] not in options:
        st.session_state[key] = "All"
    return st.selectbox(label, options, key=key)


def _fmt_num(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        value = 0
    return f"{value:,.{digits}f}"


def _mode_text(series: pd.Series) -> str:
    values = series.dropna().astype(str)
    values = values[values.str.strip().ne("") & values.str.lower().ne("unknown")]
    if values.empty:
        return "Unknown"
    return values.value_counts().index[0]


def _has_values(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns and df[column].notna().any()


def _match_team_parts(match: object) -> list[str]:
    text = str(match)
    if " - " not in text:
        return []
    return [part.strip() for part in text.split(" - ", 1) if part.strip()]


def _team_in_match_mask(df: pd.DataFrame, team: str) -> pd.Series:
    if "Match" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["Match"].apply(lambda match: team in _match_team_parts(match))


def _row_team_in_match_mask(df: pd.DataFrame) -> pd.Series:
    if "Match" not in df.columns or "Team" not in df.columns:
        return pd.Series(False, index=df.index)
    return df.apply(lambda row: str(row["Team"]) in _match_team_parts(row["Match"]), axis=1)


def _set_piece_team_options(df: pd.DataFrame) -> list[str]:
    teams = set(_safe_sorted(df["Team"])) if "Team" in df.columns else set()
    if "Match" in df.columns:
        for match in df["Match"].dropna():
            teams.update(_match_team_parts(match))
    teams = {team for team in teams if team and team != "Unknown"}
    return ["All"] + sorted(teams)


def _apply_team_perspective(df: pd.DataFrame, team: str, perspective: str) -> pd.DataFrame:
    if team == "All" or "Team" not in df.columns:
        return df
    team_series = df["Team"].astype(str)
    if perspective == "Against":
        return df[_team_in_match_mask(df, team) & _row_team_in_match_mask(df) & team_series.ne(team)].copy()
    return df[team_series.eq(team)].copy()


# ---------------------------------------------------------------------------
# Match name enrichment
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _match_name_lookup(_data_version: str = DATA_VERSION) -> dict[str, str]:
    data_dir = Path(__file__).resolve().parent.parent / "Data"
    lookup: dict[str, str] = {}

    path = data_dir / "all_matches.csv"
    if path.exists():
        matches = pd.read_csv(path, usecols=["match_id", "home_team", "away_team"])
        matches = matches.dropna(subset=["match_id", "home_team", "away_team"]).copy()
        matches["match_id"] = matches["match_id"].astype(str).str.replace(r"\.0$", "", regex=True)
        matches["Match"] = matches["home_team"].astype(str) + " - " + matches["away_team"].astype(str)
        lookup.update(dict(zip(matches["match_id"], matches["Match"])))

    corners_dir = data_dir / "Corners"
    for source in sorted(corners_dir.glob("*")) if corners_dir.exists() else []:
        if source.name.startswith("~$") or source.suffix.lower() != ".parquet":
            continue
        try:
            corner_matches = pd.read_parquet(source, columns=["match_id", "Match"], engine="pyarrow")
        except Exception:
            continue
        corner_matches = corner_matches.dropna(subset=["match_id", "Match"]).copy()
        corner_matches["match_id"] = corner_matches["match_id"].astype(str).str.replace(r"\.0$", "", regex=True)
        corner_matches["Match"] = corner_matches["Match"].astype(str)
        for match_id, match_name in zip(corner_matches["match_id"], corner_matches["Match"]):
            lookup.setdefault(match_id, match_name)

    return lookup


def _with_match_names(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "match_id" not in df.columns:
        return df
    lookup = _match_name_lookup()
    if not lookup:
        return df

    clean = df.copy()
    match_ids = clean["match_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    mapped = match_ids.map(lookup)
    if "Match" not in clean.columns:
        clean["Match"] = mapped
        return clean

    current = clean["Match"].astype("object")
    current_text = current.astype(str).str.strip()
    missing = (
        current.isna()
        | current_text.str.lower().isin(["", "unknown", "nan", "none"])
        | current_text.str.match(r"^Match\s+\d+(\.0)?$")
    )
    fill_mask = missing & mapped.notna()
    clean.loc[fill_mask, "Match"] = mapped.loc[fill_mask].to_numpy()
    return clean


# ---------------------------------------------------------------------------
# Cached data loaders (per section)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_hops_data(_data_version: str = DATA_VERSION, _code_v: str = "league_fix_v3") -> pd.DataFrame:
    sources = []
    for path in _data_files("HOPS", (".parquet",)):
        try:
            df = pd.read_parquet(path, engine="fastparquet")
        except Exception:
            df = pd.read_parquet(path, engine="pyarrow")
        sources.append(_with_league(df, _league_from_filename(path)))
    sources = [s for s in sources if not s.empty]
    if not sources:
        return pd.DataFrame(columns=["Player", "Team", "League", "Rating", "Percentile", "Tier"])

    df = pd.concat(sources, ignore_index=True, sort=False)
    df["Player"] = df["Player"].fillna("Unknown")
    df["Team"] = df["Team"].fillna("Unknown")
    df["League"] = df["League"].fillna("Unknown")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).copy()
    df["Percentile"] = (df["Rating"].rank(pct=True) * 100).round(1)
    df["Tier"] = pd.cut(
        df["Percentile"],
        bins=[-0.1, 50, 75, 90, 100],
        labels=["Depth", "Rotation", "Strong", "Elite"],
    ).astype(str)
    return df.sort_values("Rating", ascending=False)


@st.cache_data(show_spinner=False)
def _load_delay_workbook() -> dict[str, pd.DataFrame]:
    # Accept any file named corner_delays*.xlsx so a re-download doesn't break things
    data_dir = Path(__file__).resolve().parent.parent / "Data"
    candidates = sorted(data_dir.glob("corner_delays*.xlsx"))
    if not candidates:
        return {}
    path = candidates[0]
    try:
        import openpyxl  # noqa: F401
        engine = "openpyxl"
    except ImportError:
        engine = None
    try:
        return pd.read_excel(path, sheet_name=None, engine=engine) if engine else pd.read_excel(path, sheet_name=None)
    except Exception:
        return {}


@st.cache_data(show_spinner=False)
def _clean_delay_events(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    if "League" not in clean.columns:
        clean["League"] = "Unknown"
    else:
        clean["League"] = clean["League"].fillna("Unknown")
    for col in ["delay_sec", "out_time_sec", "corner_time_sec", "period", "out_value"]:
        if col in clean.columns:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
    if "delay_sec" in clean.columns:
        clean = clean[clean["delay_sec"].notna()].copy()
        clean["Delay band"] = pd.cut(
            clean["delay_sec"],
            bins=[-0.001, 10, 20, 30, 45, 10_000],
            labels=["0-10s", "10-20s", "20-30s", "30-45s", "45s+"],
        )
    return clean


# ---------------------------------------------------------------------------
# Home-page team snapshot
# ---------------------------------------------------------------------------

def _phase_snapshot(df: pd.DataFrame, phase: str, team: str, already_filtered: bool = False) -> dict[str, object]:
    empty = {"Phase": phase, "Rows": 0, "Set pieces": 0, "Shots": 0, "Goals": 0, "xG": 0.0,
             "xG / 100": 0.0, "xG / shot": 0.0, "Top taker": "Unknown", "Top shooter": "Unknown",
             "Shot rate %": 0.0, "Goal conv %": 0.0}
    if df.empty or "Team" not in df.columns:
        return empty
    part = df.copy() if already_filtered else df[df["Team"].astype(str).eq(team)].copy()
    if part.empty:
        return empty

    if _has_values(part, "possession"):
        set_pieces = int(part["possession"].nunique())
        shot_part = part[part["is_shot"]] if "is_shot" in part.columns else part.iloc[0:0]
        goal_part = part[part["is_goal"]] if "is_goal" in part.columns else part.iloc[0:0]
        shots = int(shot_part["possession"].nunique()) if not shot_part.empty else 0
        goals = int(goal_part["possession"].nunique()) if not goal_part.empty else 0
    else:
        set_pieces = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0

    if _has_values(part, "possession") and {"shot_x", "shot_y", "xg"}.issubset(part.columns):
        xg_rows = part[part["shot_x"].notna()][["possession", "shot_x", "shot_y", "xg"]].drop_duplicates()
        total_xg = float(xg_rows["xg"].fillna(0).sum()) if not xg_rows.empty else 0.0
    else:
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0

    return {
        "Phase": phase,
        "Rows": int(len(part)),
        "Set pieces": set_pieces,
        "Shots": shots,
        "Goals": goals,
        "xG": round(total_xg, 2),
        "xG / 100": round((total_xg / set_pieces * 100) if set_pieces else 0, 2),
        "xG / shot": round((total_xg / shots) if shots else 0, 3),
        "Top taker": _mode_text(part["Taker"]) if "Taker" in part.columns else "Unknown",
        "Top shooter": _mode_text(part["Shooter"]) if "Shooter" in part.columns else "Unknown",
        "Shot rate %": round((shots / set_pieces * 100) if set_pieces else 0, 1),
        "Goal conv %": round((goals / shots * 100) if shots else 0, 1),
    }


def team_snapshot_table(team: str, corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, perspective: str = "For") -> pd.DataFrame:
    rows = [
        _phase_snapshot(_apply_team_perspective(corners, team, perspective), "Corners", team, already_filtered=True),
        _phase_snapshot(_apply_team_perspective(freekicks, team, perspective), "Freekicks", team, already_filtered=True),
        _phase_snapshot(_apply_team_perspective(throwins, team, perspective), "Throw-ins", team, already_filtered=True),
    ]
    return pd.DataFrame(rows)


def selected_team_staff_read(team: str, snapshot: pd.DataFrame, hops: pd.DataFrame) -> tuple[str, str, str]:
    if snapshot.empty or snapshot["Set pieces"].sum() == 0:
        phase_read = "No restart volume found"
        role_read = "No taker data found"
    else:
        best_phase = snapshot.sort_values(["xG", "Shots", "Set pieces"], ascending=False).iloc[0]
        phase_read = f"{best_phase['Phase']} lead the threat profile: {_fmt_num(float(best_phase['xG']), 2)} xG from {int(best_phase['Shots'])} shots."
        takers = snapshot["Top taker"].dropna().astype(str)
        takers = takers[takers.ne("Unknown")]
        role_read = f"Primary repeat name: {takers.value_counts().index[0]}." if not takers.empty else "No clear repeat taker yet."

    if not hops.empty and "Team" in hops.columns:
        team_hops = hops[hops["Team"].astype(str).eq(team)].sort_values("Rating", ascending=False)
        if not team_hops.empty:
            top = team_hops.iloc[0]
            hops_read = f"{top['Player']} is the top HOPS profile ({float(top['Rating']):.3f}, {top.get('Tier', 'rated')})."
        else:
            hops_read = "No HOPS profile found for this team."
    else:
        hops_read = "No HOPS profile found for this team."

    return phase_read, role_read, hops_read


# ---------------------------------------------------------------------------
# League comparison aggregators
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _league_comparison_source(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for phase, df in [("Corners", corners), ("Freekicks", freekicks), ("Throw-ins", throwins)]:
        if df.empty:
            continue
        base = unique_start_events(df).copy()
        base["Phase"] = phase
        frames.append(base)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "League" not in combined.columns:
        combined["League"] = "Unknown"
    combined["League"] = combined["League"].fillna("Unknown").astype(str)
    return combined


@st.cache_data(show_spinner=False)
def _league_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "League" not in df.columns:
        return pd.DataFrame()
    rows = []
    for league, part in df.groupby("League", dropna=False):
        set_pieces = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        teams = int(part["Team"].nunique()) if "Team" in part.columns else 0
        matches = int(part["Match"].nunique()) if "Match" in part.columns else 0
        rows.append({
            "League": league, "Set pieces": set_pieces, "Teams": teams, "Matches": matches,
            "Shots": shots, "Goals": goals,
            "Shot rate %": round(shots / set_pieces * 100, 1) if set_pieces else 0.0,
            "xG": round(total_xg, 2),
            "xG / 100": round(total_xg / set_pieces * 100, 2) if set_pieces else 0.0,
            "xG / shot": round(total_xg / shots, 3) if shots else 0.0,
            "Goal conv %": round(goals / shots * 100, 1) if shots else 0.0,
            "Top team": _mode_text(part["Team"]) if "Team" in part.columns else "Unknown",
            "Top taker": _mode_text(part["Taker"]) if "Taker" in part.columns else "Unknown",
        })
    return pd.DataFrame(rows).sort_values(["xG / 100", "Shot rate %", "Set pieces"], ascending=False)


@st.cache_data(show_spinner=False)
def _league_phase_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not {"League", "Phase"}.issubset(df.columns):
        return pd.DataFrame()
    rows = []
    for (league, phase), part in df.groupby(["League", "Phase"], dropna=False):
        set_pieces = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        rows.append({
            "League": league, "Phase": phase,
            "Set pieces": set_pieces, "Shots": shots, "Goals": goals,
            "Shot rate %": round(shots / set_pieces * 100, 1) if set_pieces else 0.0,
            "xG / 100": round(total_xg / set_pieces * 100, 2) if set_pieces else 0.0,
            "Goals / set piece": round(goals / set_pieces, 3) if set_pieces else 0.0,
            "xG / set piece": round(total_xg / set_pieces, 3) if set_pieces else 0.0,
            "xG": round(total_xg, 2),
        })
    return pd.DataFrame(rows).sort_values(["League", "Phase"])


@st.cache_data(show_spinner=False)
def _league_set_piece_difference_table(phase_summary: pd.DataFrame) -> pd.DataFrame:
    if phase_summary.empty:
        return pd.DataFrame()
    phase_labels = {"Corners": "Corners", "Freekicks": "Indirect free kicks", "Throw-ins": "Throw-ins"}
    rows = []
    for league, part in phase_summary.groupby("League", dropna=False):
        row: dict[str, object] = {"League": league}
        metrics: dict[str, dict[str, float]] = {}
        for phase, label in phase_labels.items():
            phase_part = part[part["Phase"].eq(phase)]
            if phase_part.empty:
                set_pieces = goals = 0
                xg = goals_per = xg_per = 0.0
            else:
                first = phase_part.iloc[0]
                set_pieces = int(first.get("Set pieces", 0))
                goals = int(first.get("Goals", 0))
                xg = float(first.get("xG", 0))
                goals_per = float(first.get("Goals / set piece", 0))
                xg_per = float(first.get("xG / set piece", 0))
            metrics[phase] = {"Goals / set piece": goals_per, "xG / set piece": xg_per}
            row[f"{label}"] = set_pieces
            row[f"{label} goals"] = goals
            row[f"Goals / {label.lower()}"] = round(goals_per, 3)
            row[f"xG / {label.lower()}"] = round(xg_per, 3)
            row[f"{label} xG"] = round(xg, 2)
        row["Corner xG edge vs indirect FK"] = round(metrics["Corners"]["xG / set piece"] - metrics["Freekicks"]["xG / set piece"], 3)
        row["Corner xG edge vs throw-in"] = round(metrics["Corners"]["xG / set piece"] - metrics["Throw-ins"]["xG / set piece"], 3)
        row["Indirect FK xG edge vs throw-in"] = round(metrics["Freekicks"]["xG / set piece"] - metrics["Throw-ins"]["xG / set piece"], 3)
        row["Corner goal edge vs indirect FK"] = round(metrics["Corners"]["Goals / set piece"] - metrics["Freekicks"]["Goals / set piece"], 3)
        row["Corner goal edge vs throw-in"] = round(metrics["Corners"]["Goals / set piece"] - metrics["Throw-ins"]["Goals / set piece"], 3)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["Corner xG edge vs indirect FK", "Corner xG edge vs throw-in"], ascending=False)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_people(query: str, corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, hops: pd.DataFrame) -> pd.DataFrame:
    query = query.strip().lower()
    if len(query) < 2:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    for phase, df in [("Corners", corners), ("Freekicks", freekicks), ("Throw-ins", throwins)]:
        if df.empty:
            continue
        for role, col in [("Taker", "Taker"), ("Shooter", "Shooter")]:
            if col not in df.columns:
                continue
            matches = df[df[col].fillna("").astype(str).str.lower().str.contains(query, regex=False)]
            if matches.empty:
                continue
            grouped = (
                matches.groupby([col, "Team"], dropna=False)
                .agg(Rows=(col, "size"), xG=("xg", "sum") if "xg" in matches.columns else (col, "size"))
                .reset_index()
                .sort_values(["Rows", "xG"], ascending=False)
                .head(6)
            )
            for _, row in grouped.iterrows():
                rows.append({"Name": row[col], "Team": row["Team"], "Role": role,
                             "Dataset": phase, "Rows": int(row["Rows"]), "xG": round(float(row["xG"]), 2)})
    if not hops.empty and "Player" in hops.columns:
        h = hops[hops["Player"].fillna("").astype(str).str.lower().str.contains(query, regex=False)]
        for _, row in h.head(10).iterrows():
            rows.append({"Name": row["Player"], "Team": row.get("Team", "Unknown"),
                         "Role": "HOPS profile", "Dataset": "HOPS", "Rows": 1, "xG": np.nan,
                         "Rating": round(float(row.get("Rating", 0)), 3), "Tier": row.get("Tier", "")})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

def set_section(section: str, team: str | None = None) -> None:
    st.session_state["section"] = section
    if team:
        prefix = FILTER_PREFIXES.get(section)
        if prefix:
            st.session_state[f"{prefix}_team"] = team
    try:
        st.query_params["section"] = section
    except Exception:
        pass
    st.rerun()


def reset_current_filters(section: str) -> None:
    prefix = FILTER_PREFIXES.get(section)
    if prefix is None:
        return
    for key in list(st.session_state.keys()):
        if key.startswith(f"{prefix}_"):
            del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Chart wrappers
# ---------------------------------------------------------------------------

def render_plotly_visual(fig, label: str, key: str) -> None:
    if PLOTLY_AVAILABLE:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displaylogo": False, "displayModeBar": False},
            key=f"{key}_chart",
        )
    else:
        st.image(plotly_figure_png_bytes(fig), use_container_width=True)
    render_plotly_png_download(fig, label, key)


def render_mpl_visual(fig, label: str, key: str) -> None:
    st.pyplot(fig, use_container_width=True)
    render_matplotlib_png_download(fig, label, key)


def _plot_colors() -> list[str]:
    return ["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309", "#7c3aed", "#64748b"]


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str | None = None, orientation: str = "v", barmode: str = "relative") -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    groups = [(None, df)] if not color or color not in df.columns else list(df.groupby(color, dropna=False))
    for idx, (name, part) in enumerate(groups):
        trace_name = str(name) if name is not None else y
        if orientation == "h":
            fig.add_bar(x=part[x], y=part[y], name=trace_name, orientation="h", marker_color=colors[idx % len(colors)])
        else:
            fig.add_bar(x=part[x], y=part[y], name=trace_name, marker_color=colors[idx % len(colors)])
    fig.update_layout(title=title, barmode=barmode, legend_title_text="", xaxis_title=x, yaxis_title=y)
    return fig


def histogram_chart(df: pd.DataFrame, column: str, title: str = "", color: str | None = None, nbins: int = 20) -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    groups = [(None, df)] if not color or color not in df.columns else list(df.groupby(color, dropna=False))
    for idx, (name, part) in enumerate(groups):
        fig.add_histogram(x=part[column], nbinsx=nbins, name=str(name) if name is not None else column, marker_color=colors[idx % len(colors)])
    fig.update_layout(title=title, barmode="overlay", legend_title_text="", xaxis_title=column, yaxis_title="Count")
    fig.update_traces(opacity=0.82)
    return fig


def box_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    for idx, (name, part) in enumerate(df.groupby(x, dropna=False)):
        fig.add_box(y=part[y], name=str(name), marker_color=colors[idx % len(colors)], boxmean=True)
    fig.update_layout(title=title, legend_title_text="", xaxis_title=x, yaxis_title=y, showlegend=False)
    return fig


def simple_view_radio(key: str, options: list[str]) -> str:
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    return st.radio("View", options, horizontal=True, key=key)


# ---------------------------------------------------------------------------
# PDF helper
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _cached_report_pdf(df: pd.DataFrame, label: str, opponent: str) -> bytes:
    return prematch_report_pdf_bytes(df, label, opponent)
