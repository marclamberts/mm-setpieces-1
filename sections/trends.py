"""Set Piece Trends — per-match rolling performance evolution."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    hero_block,
    load_prepared_freekick_brief_data,
    load_prepared_sp_data,
    polish_plotly_figure,
    render_analyst_table,
    section_header,
)
from sections._shared import (
    _apply_team_perspective,
    _safe_sorted,
    _with_match_names,
    load_hops_data,
    render_plotly_visual,
)

_CODE_V = "trends_v1"


@st.cache_data(show_spinner="Loading data…")
def _load(_dv: str = DATA_VERSION, _cv: str = _CODE_V):
    corners = _with_match_names(load_prepared_sp_data("Corners", _dv))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_dv))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _dv))
    hops = load_hops_data(_dv)
    return corners, freekicks, throwins, hops


def _all_teams(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame) -> list[str]:
    teams: set[str] = set()
    for df in [corners, freekicks, throwins]:
        if "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    return sorted(t for t in teams if t.strip())


def _combined_sp(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, sp_type: str) -> pd.DataFrame:
    if sp_type == "Corner":
        return corners.copy()
    if sp_type == "FK":
        return freekicks.copy()
    if sp_type == "Throw-in":
        return throwins.copy()
    frames = [df for df in [corners, freekicks, throwins] if not df.empty]
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def _per_match_series(df: pd.DataFrame, team: str, perspective: str, window: int) -> pd.DataFrame:
    """Group by match_rank, compute rolling stats, return sorted series."""
    if df.empty or "match_rank" not in df.columns:
        return pd.DataFrame()
    filtered = _apply_team_perspective(df, team, perspective)
    if filtered.empty:
        return pd.DataFrame()

    agg: dict[str, object] = {"deliveries": ("match_rank", "count")}
    if "xg" in filtered.columns:
        agg["xg"] = ("xg", "sum")
    if "is_shot" in filtered.columns:
        agg["shots"] = ("is_shot", "sum")
    if "is_goal" in filtered.columns:
        agg["goals"] = ("is_goal", "sum")

    grp = filtered.groupby("match_rank", dropna=False).agg(**agg).reset_index()
    grp = grp.sort_values("match_rank").reset_index(drop=True)
    grp["match_num"] = range(1, len(grp) + 1)

    if "xg" not in grp.columns:
        grp["xg"] = 0.0
    if "shots" not in grp.columns:
        grp["shots"] = 0
    if "goals" not in grp.columns:
        grp["goals"] = 0

    grp["shots"] = pd.to_numeric(grp["shots"], errors="coerce").fillna(0)
    grp["goals"] = pd.to_numeric(grp["goals"], errors="coerce").fillna(0)
    grp["xg"] = pd.to_numeric(grp["xg"], errors="coerce").fillna(0.0)

    roll = grp[["xg", "shots", "deliveries"]].rolling(window, min_periods=1)
    grp["rolling_xg_per_match"] = roll["xg"].mean().round(3)
    grp["rolling_shot_rate"] = (roll["shots"].sum() / roll["deliveries"].sum().clip(lower=1) * 100).round(2)
    grp["rolling_xg_per_100"] = (roll["xg"].sum() / roll["deliveries"].sum().clip(lower=1) * 100).round(3)
    return grp


def _avg_line(series: pd.Series) -> float:
    return float(series.mean()) if not series.empty else 0.0


def _line_chart_with_avg(x, y_series: pd.Series, avg: float, series_name: str, y_label: str,
                          line_color: str, key: str, title: str) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y_series.tolist(),
        mode="lines+markers",
        name=series_name,
        line=dict(color=line_color, width=2),
        marker=dict(size=5),
    ))
    fig.add_hline(y=avg, line_dash="dash", line_color="#94a3b8",
                  annotation_text=f"Avg {avg:.2f}", annotation_position="top right")
    fig.update_layout(
        title=title,
        xaxis_title="Match #",
        yaxis_title=y_label,
        height=320,
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(font=dict(color="#cbd5e1")),
    )
    render_plotly_visual(polish_plotly_figure(fig), title, key)


def _recent_form_table(grp: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["match_num", "match_rank", "xg", "shots", "goals", "deliveries"] if c in grp.columns]
    return grp[cols].tail(10).sort_values("match_num", ascending=False).rename(columns={
        "match_num": "Match #", "match_rank": "Rank", "xg": "xG",
        "shots": "Shots", "goals": "Goals", "deliveries": "Deliveries",
    })


def _attack_trends_tab(grp: pd.DataFrame, team: str, window: int) -> None:
    if grp.empty:
        st.info("No attacking data for this filter.")
        return

    x = grp["match_num"].tolist()
    avg_xg = _avg_line(grp["rolling_xg_per_match"])
    avg_shot = _avg_line(grp["rolling_shot_rate"])

    c1, c2 = st.columns(2)
    with c1:
        section_header(f"Rolling xG / match (window={window})")
        _line_chart_with_avg(x, grp["rolling_xg_per_match"], avg_xg,
                             "Rolling xG/match", "xG / match", "#22c55e",
                             "trends_atk_xg", f"{team} — rolling xG / match")
    with c2:
        section_header(f"Rolling shot rate (window={window})")
        _line_chart_with_avg(x, grp["rolling_shot_rate"], avg_shot,
                             "Rolling shot rate", "Shots / 100 del.", "#3b82f6",
                             "trends_atk_shot", f"{team} — rolling shot rate %")

    section_header("Recent form — last 10 matches")
    render_analyst_table(_recent_form_table(grp), height=300,
                         color_cols=["xG", "Shots", "Goals"])


def _defence_trends_tab(grp: pd.DataFrame, team: str, window: int) -> None:
    if grp.empty:
        st.info("No defensive data for this filter.")
        return

    x = grp["match_num"].tolist()
    avg_xg = _avg_line(grp["rolling_xg_per_match"])
    avg_shot = _avg_line(grp["rolling_shot_rate"])

    c1, c2 = st.columns(2)
    with c1:
        section_header(f"Rolling xG conceded / match (window={window})")
        _line_chart_with_avg(x, grp["rolling_xg_per_match"], avg_xg,
                             "Rolling xG conceded", "xG conceded / match", "#ef4444",
                             "trends_def_xg", f"{team} — rolling xG conceded / match")
    with c2:
        section_header(f"Rolling shot concede rate (window={window})")
        _line_chart_with_avg(x, grp["rolling_shot_rate"], avg_shot,
                             "Rolling shot concede rate", "Shots conceded / 100", "#f59e0b",
                             "trends_def_shot", f"{team} — rolling shot concede rate %")

    section_header("Recent form defended — last 10 matches")
    render_analyst_table(_recent_form_table(grp), height=300,
                         color_cols=["xG", "Shots", "Goals"])


def _atk_vs_def_tab(atk: pd.DataFrame, def_: pd.DataFrame, team: str) -> None:
    if atk.empty and def_.empty:
        st.info("Insufficient data for comparison.")
        return

    fig_line = go.Figure()
    if not atk.empty:
        fig_line.add_trace(go.Scatter(
            x=atk["match_num"].tolist(), y=atk["rolling_xg_per_match"].tolist(),
            mode="lines+markers", name="Attack xG/match",
            line=dict(color="#22c55e", width=2), marker=dict(size=5),
        ))
    if not def_.empty:
        fig_line.add_trace(go.Scatter(
            x=def_["match_num"].tolist(), y=def_["rolling_xg_per_match"].tolist(),
            mode="lines+markers", name="Defence xG conceded/match",
            line=dict(color="#ef4444", width=2), marker=dict(size=5),
        ))
    fig_line.update_layout(
        title=f"{team} — Attack vs Defence xG / match",
        xaxis_title="Match #", yaxis_title="xG / match", height=340,
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(font=dict(color="#cbd5e1")),
    )
    section_header("Attack vs Defence xG / match")
    render_plotly_visual(polish_plotly_figure(fig_line), "Attack vs Defence", "trends_avd_line")

    if not atk.empty and not def_.empty:
        # Align on match_num for net differential
        merged = pd.merge(
            atk[["match_num", "xg"]].rename(columns={"xg": "atk_xg"}),
            def_[["match_num", "xg"]].rename(columns={"xg": "def_xg"}),
            on="match_num", how="inner",
        )
        if not merged.empty:
            merged["net_xg"] = merged["atk_xg"] - merged["def_xg"]
            bar_colors = ["#22c55e" if v >= 0 else "#ef4444" for v in merged["net_xg"]]
            fig_net = go.Figure(go.Bar(
                x=merged["match_num"].tolist(), y=merged["net_xg"].tolist(),
                marker_color=bar_colors, name="Net xG",
            ))
            fig_net.update_layout(
                title=f"{team} — Net xG differential per match (Attack minus Defence)",
                xaxis_title="Match #", yaxis_title="Net xG",
                height=300, margin=dict(l=8, r=8, t=36, b=8),
            )
            section_header("Net xG differential per match")
            render_plotly_visual(polish_plotly_figure(fig_net), "Net xG differential", "trends_avd_net")


def render_trends() -> None:
    corners, freekicks, throwins, hops = _load()

    all_teams = _all_teams(corners, freekicks, throwins)
    all_leagues = ["All"] + sorted(set(
        _safe_sorted(corners.get("League", pd.Series(dtype=str))) +
        _safe_sorted(freekicks.get("League", pd.Series(dtype=str))) +
        _safe_sorted(throwins.get("League", pd.Series(dtype=str)))
    ))

    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        selected_league = st.selectbox("League", all_leagues, key="trends_league")
    with fc2:
        team_opts = ["All"] + all_teams
        selected_team = st.selectbox("Team", team_opts, key="trends_team")
    with fc3:
        sp_type = st.selectbox("Set Piece Type", ["All", "Corner", "FK", "Throw-in"], key="trends_sp_type")
    with fc4:
        window = st.selectbox("Rolling window", [3, 5, 10], index=1, key="trends_window")

    def _apply_league(df: pd.DataFrame) -> pd.DataFrame:
        if selected_league != "All" and "League" in df.columns:
            return df[df["League"] == selected_league].copy()
        return df.copy()

    c = _apply_league(corners)
    fk = _apply_league(freekicks)
    ti = _apply_league(throwins)

    combined = _combined_sp(c, fk, ti, sp_type)

    hero_block("Set pieces", "Set Piece Trends",
               f"{selected_team if selected_team != 'All' else 'All teams'} · {sp_type} · rolling {window}")
    st.session_state["ctx_row_count"] = f"Trends · {len(combined):,} events"

    if selected_team == "All":
        st.info("Select a team to view match-by-match trends.")
        return

    atk_grp = _per_match_series(combined, selected_team, "For", int(window))
    def_grp = _per_match_series(combined, selected_team, "Against", int(window))

    tabs = st.tabs(["Attack Trends", "Defence Trends", "Attack vs Defence"])
    tab_atk, tab_def, tab_avd = tabs

    with tab_atk:
        _attack_trends_tab(atk_grp, selected_team, int(window))

    with tab_def:
        _defence_trends_tab(def_grp, selected_team, int(window))

    with tab_avd:
        _atk_vs_def_tab(atk_grp, def_grp, selected_team)
