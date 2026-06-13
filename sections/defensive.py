"""Defensive Set Piece Analysis — how teams concede from restarts."""
from __future__ import annotations

import numpy as np
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
    set_section,
)

_CODE_V = "defensive_v1"

OUTCOME_COLOURS = {
    "Goal": "#ef4444",
    "Saved": "#f59e0b",
    "Off T": "#94a3b8",
    "Blocked": "#94a3b8",
    "Wayward": "#94a3b8",
    "Post": "#94a3b8",
    "No shot": "#334155",
}


@st.cache_data(show_spinner="Loading data…")
def _load(_dv: str = DATA_VERSION, _cv: str = _CODE_V):
    corners = _with_match_names(load_prepared_sp_data("Corners", _dv))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_dv))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _dv))
    hops = load_hops_data(_dv)
    return corners, freekicks, throwins, hops


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _defence_kpis(df: pd.DataFrame) -> dict:
    deliveries = max(len(df), 1)
    shots = int(df["is_shot"].sum()) if "is_shot" in df.columns else 0
    goals = int(df["is_goal"].sum()) if "is_goal" in df.columns else 0
    xg = float(df["xg"].fillna(0).sum()) if "xg" in df.columns else 0.0
    return {
        "deliveries": deliveries,
        "shots": shots,
        "goals": goals,
        "xg": xg,
        "xg_per_100": round(xg / deliveries * 100, 2),
        "shot_rate": round(shots / deliveries * 100, 2),
        "goals_per_shot": round(goals / shots, 3) if shots else 0.0,
    }


def _defensive_score(kpis: dict) -> float:
    """Inverted percentile rank — lower conceded = better. Returns 0-100 raw score here."""
    xg_100 = kpis["xg_per_100"]
    shot_rate = kpis["shot_rate"]
    gps = kpis["goals_per_shot"]
    league_avg_xg100 = 2.5
    league_avg_shot = 15.0
    league_avg_gps = 0.10
    raw_xg = max(0.0, min(100.0, (1 - xg_100 / max(league_avg_xg100 * 2, 0.01)) * 100))
    raw_shot = max(0.0, min(100.0, (1 - shot_rate / max(league_avg_shot * 2, 0.01)) * 100))
    raw_gps = max(0.0, min(100.0, (1 - gps / max(league_avg_gps * 2, 0.001)) * 100))
    return round(raw_xg * 0.40 + raw_shot * 0.35 + raw_gps * 0.25, 1)


def _all_teams_defensive_scores(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame) -> pd.DataFrame:
    teams: set[str] = set()
    for df in [corners, freekicks, throwins]:
        if "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    rows = []
    for team in sorted(teams):
        pieces = []
        for df in [corners, freekicks, throwins]:
            sub = _apply_team_perspective(df, team, "Against")
            if not sub.empty:
                pieces.append(sub)
        if not pieces:
            continue
        combined = pd.concat(pieces, ignore_index=True, sort=False)
        kpis = _defence_kpis(combined)
        rows.append({"Team": team, **kpis})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _match_xg_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Match" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby("Match", dropna=False)
    rows = []
    for match, part in grp:
        rows.append({
            "Match": match,
            "xG conceded": round(float(part["xg"].fillna(0).sum()), 3) if "xg" in part.columns else 0.0,
            "Shots conceded": int(part["is_shot"].sum()) if "is_shot" in part.columns else 0,
            "Goals conceded": int(part["is_goal"].sum()) if "is_goal" in part.columns else 0,
        })
    return pd.DataFrame(rows).sort_values("xG conceded", ascending=False)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def _shot_scatter(df: pd.DataFrame, key_prefix: str) -> go.Figure:
    shot_df = df[df.get("is_shot", pd.Series(dtype=bool)).astype(bool)].copy() if "is_shot" in df.columns else df.copy()
    if "shot_x" not in shot_df.columns or "shot_y" not in shot_df.columns:
        return go.Figure()
    shot_df = shot_df.dropna(subset=["shot_x", "shot_y"])
    outcome_col = shot_df["Shot outcome"].astype(str) if "Shot outcome" in shot_df.columns else pd.Series(["Unknown"] * len(shot_df))
    colours = outcome_col.map(lambda o: OUTCOME_COLOURS.get(o, "#94a3b8"))
    fig = go.Figure()
    for outcome in ["Goal", "Saved", "Off T", "Blocked", "Wayward", "Post"]:
        mask = outcome_col == outcome
        sub = shot_df[mask]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["shot_x"], y=sub["shot_y"],
            mode="markers",
            name=outcome,
            marker=dict(color=OUTCOME_COLOURS.get(outcome, "#94a3b8"), size=8, opacity=0.8,
                        line=dict(width=1, color="rgba(255,255,255,.3)")),
        ))
    fig.update_layout(
        xaxis=dict(range=[0, 120], title="X"),
        yaxis=dict(range=[0, 80], title="Y"),
        height=340,
        margin=dict(l=8, r=8, t=24, b=8),
        legend=dict(font=dict(color="#cbd5e1")),
    )
    return polish_plotly_figure(fig)


def _outcome_bar(df: pd.DataFrame) -> go.Figure:
    if "Shot outcome" not in df.columns:
        return go.Figure()
    counts = df["Shot outcome"].value_counts().reset_index()
    counts.columns = ["Outcome", "Count"]
    colours = counts["Outcome"].map(lambda o: OUTCOME_COLOURS.get(o, "#94a3b8")).tolist()
    fig = go.Figure(go.Bar(x=counts["Outcome"], y=counts["Count"], marker_color=colours))
    fig.update_layout(margin=dict(l=8, r=8, t=24, b=8), height=280, xaxis_title="Outcome", yaxis_title="Count")
    return polish_plotly_figure(fig)


def _defence_vs_avg_bar(kpis: dict, label: str) -> go.Figure:
    metrics = ["xG/100", "Shot Rate %", "Goals/Shot %"]
    team_vals = [kpis["xg_per_100"], kpis["shot_rate"], kpis["goals_per_shot"] * 100]
    avg_vals = [2.5, 15.0, 10.0]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=label, x=metrics, y=team_vals, marker_color="#ef4444"))
    fig.add_trace(go.Bar(name="League avg", x=metrics, y=avg_vals, marker_color="#334155"))
    fig.update_layout(barmode="group", margin=dict(l=8, r=8, t=24, b=8), height=300,
                      legend=dict(font=dict(color="#cbd5e1")))
    return polish_plotly_figure(fig)


def _league_ranking_bar(scores_df: pd.DataFrame, team: str) -> go.Figure:
    if scores_df.empty or "def_score" not in scores_df.columns:
        return go.Figure()
    df = scores_df.sort_values("def_score", ascending=True).tail(30).copy()
    colours = ["#22c55e" if t == team else "#334155" for t in df["Team"]]
    fig = go.Figure(go.Bar(
        x=df["def_score"], y=df["Team"], orientation="h",
        marker_color=colours,
        text=df["def_score"].round(1), textposition="outside",
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Defensive Score (higher = better)"),
        height=max(300, len(df) * 22),
        margin=dict(l=10, r=40, t=20, b=20),
    )
    return polish_plotly_figure(fig)


# ---------------------------------------------------------------------------
# Section tabs helpers
# ---------------------------------------------------------------------------

def _type_defence_tab(df: pd.DataFrame, label: str, key: str) -> None:
    if df.empty:
        st.info(f"No {label} defensive data for this team.")
        return
    kpis = _defence_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("xG conceded", f"{kpis['xg']:.2f}")
    c2.metric("Shots conceded", f"{kpis['shots']:,}")
    c3.metric("Goals conceded", f"{kpis['goals']:,}")
    c4.metric("xG/100", f"{kpis['xg_per_100']:.2f}")

    section_header("Shot concede locations")
    render_plotly_visual(_shot_scatter(df, key), f"{label} shot scatter", f"{key}_scatter")

    section_header("Outcome breakdown")
    render_plotly_visual(_outcome_bar(df), f"{label} outcomes", f"{key}_outcomes")

    section_header("Top matches by xG conceded")
    render_analyst_table(_match_xg_table(df).head(15), height=360,
                         color_cols=["xG conceded", "Shots conceded", "Goals conceded"])


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_defensive() -> None:
    corners, freekicks, throwins, hops = _load()

    all_teams = sorted(set(
        list(_safe_sorted(corners["Team"])) +
        list(_safe_sorted(freekicks["Team"])) +
        list(_safe_sorted(throwins["Team"]))
    ))
    all_leagues = ["All"] + sorted(set(
        list(_safe_sorted(corners.get("League", pd.Series(dtype=str)))) +
        list(_safe_sorted(freekicks.get("League", pd.Series(dtype=str))))
    ))

    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    fc1, fc2 = st.columns(2)
    with fc1:
        selected_team = st.selectbox("Team", ["All"] + all_teams, key="defensive_team")
    with fc2:
        selected_league = st.selectbox("League", all_leagues, key="defensive_league")

    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        result = _apply_team_perspective(df, selected_team, "Against") if selected_team != "All" else df.copy()
        if selected_league != "All" and "League" in result.columns:
            result = result[result["League"] == selected_league]
        return result

    c_def = _filter(corners)
    fk_def = _filter(freekicks)
    ti_def = _filter(throwins)

    total_rows = len(c_def) + len(fk_def) + len(ti_def)
    hero_block("Set pieces", "Defensive Set Piece Analysis",
               f"{selected_team if selected_team != 'All' else 'All teams'} · {total_rows:,} events")
    st.session_state["ctx_row_count"] = f"Defensive · {total_rows:,} events"

    all_def = pd.concat([df for df in [c_def, fk_def, ti_def] if not df.empty],
                        ignore_index=True, sort=False) if total_rows else pd.DataFrame()

    tabs = st.tabs(["Overview", "Corner Defence", "FK Defence", "Throw-in Defence", "GK Analysis"])
    tab_ov, tab_corners, tab_fk, tab_ti, tab_gk = tabs

    # ── Overview ────────────────────────────────────────────────────────────
    with tab_ov:
        if all_def.empty:
            st.info("No defensive data found for this filter.")
        else:
            kpis = _defence_kpis(all_def)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("xG conceded", f"{kpis['xg']:.2f}")
            c2.metric("Shots conceded", f"{kpis['shots']:,}")
            c3.metric("Goals conceded", f"{kpis['goals']:,}")
            c4.metric("xG/100", f"{kpis['xg_per_100']:.2f}")
            c5.metric("Shot concede rate %", f"{kpis['shot_rate']:.1f}")

            def_score = _defensive_score(kpis)
            section_header("Defensive Impact Score", "Higher = better. Inverted from conceded metrics.")
            ds1, ds2 = st.columns([1, 2])
            with ds1:
                st.markdown(
                    f"""<div style="background:#161922;border:2px solid #22c55e;border-radius:10px;
                        padding:1rem;text-align:center;margin-top:.3rem">
                        <div style="font-size:.72rem;color:#94a3b8;margin-bottom:.2rem">Defensive Score</div>
                        <div style="font-size:3rem;font-weight:800;color:#22c55e;line-height:1">{def_score:.1f}</div>
                        <div style="font-size:.8rem;color:#22c55e;margin-top:.2rem">out of 100</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with ds2:
                section_header("Components vs league average")
                render_plotly_visual(
                    _defence_vs_avg_bar(kpis, selected_team if selected_team != "All" else "Selected"),
                    "Defence vs avg", "def_vs_avg",
                )

            if selected_team != "All":
                section_header("League ranking")
                scores_df = _all_teams_defensive_scores(corners, freekicks, throwins)
                if not scores_df.empty:
                    scores_df["def_score"] = scores_df.apply(
                        lambda r: _defensive_score({k: r[k] for k in ["xg_per_100", "shot_rate", "goals_per_shot"]}),
                        axis=1,
                    )
                    render_plotly_visual(
                        _league_ranking_bar(scores_df, selected_team),
                        "Defensive league ranking", "def_league_rank",
                    )

    # ── Corner / FK / Throw-in Defence ─────────────────────────────────────
    with tab_corners:
        _type_defence_tab(c_def, "Corner", "def_corners")

    with tab_fk:
        _type_defence_tab(fk_def, "FK", "def_fk")

    with tab_ti:
        _type_defence_tab(ti_def, "Throw-in", "def_ti")

    # ── GK Analysis ─────────────────────────────────────────────────────────
    with tab_gk:
        section_header("Goalkeeper Set Piece Analysis")
        gk_df = c_def.copy() if not c_def.empty else pd.DataFrame()
        if "Shot outcome" in gk_df.columns:
            gk_df = gk_df[gk_df["Shot outcome"].astype(str) != "No shot"]

        if gk_df.empty:
            st.info("No GK-relevant shot data found.")
        else:
            shots_faced = len(gk_df)
            saves = int((gk_df["Shot outcome"].isin(["Saved"])).sum()) if "Shot outcome" in gk_df.columns else 0
            goals_conceded = int(gk_df["is_goal"].sum()) if "is_goal" in gk_df.columns else 0
            on_target = saves + goals_conceded
            save_pct = round(saves / on_target * 100, 1) if on_target else 0.0

            g1, g2, g3, g4 = st.columns(4)
            g1.metric("Shots on target faced", f"{on_target:,}")
            g2.metric("Saves", f"{saves:,}")
            g3.metric("Goals conceded", f"{goals_conceded:,}")
            g4.metric("Save %", f"{save_pct:.1f}%")

            if "Shot outcome" in gk_df.columns:
                section_header("Shot outcome distribution")
                outcome_counts = gk_df["Shot outcome"].value_counts().reset_index()
                outcome_counts.columns = ["Outcome", "Count"]
                pie_colours = outcome_counts["Outcome"].map(lambda o: OUTCOME_COLOURS.get(o, "#94a3b8")).tolist()
                fig_pie = go.Figure(go.Pie(
                    labels=outcome_counts["Outcome"],
                    values=outcome_counts["Count"],
                    marker_colors=pie_colours,
                    hole=0.3,
                ))
                fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300,
                                      legend=dict(font=dict(color="#cbd5e1")))
                render_plotly_visual(polish_plotly_figure(fig_pie), "GK shot outcomes pie", "def_gk_pie")

                section_header("Shot locations")
                render_plotly_visual(_shot_scatter(gk_df, "def_gk"), "GK shot locations", "def_gk_scatter")

            if "League" in gk_df.columns:
                section_header("Breakdown by League")
                grp = gk_df.groupby("League", dropna=False).agg(
                    Shots=("is_shot", "count"),
                    Goals=("is_goal", "sum"),
                    xG=("xg", "sum") if "xg" in gk_df.columns else ("is_goal", "sum"),
                ).reset_index()
                render_analyst_table(grp, height=260, color_cols=["Goals", "xG"])

    section_header("Jump to attacking analysis", "See how this team attacks from set pieces")
    team_label = selected_team if selected_team != "All" else None
    jd1, jd2, jd3, jd4, jd5 = st.columns(5)
    if jd1.button("⚽ Corners", key="def_jump_corners", use_container_width=True):
        set_section("Corners", team=team_label)
    if jd2.button("🎯 Free Kicks", key="def_jump_fk", use_container_width=True):
        set_section("Freekicks", team=team_label)
    if jd3.button("↗ Throw-ins", key="def_jump_ti", use_container_width=True):
        set_section("Throw-ins", team=team_label)
    if jd4.button("🏃 HOPS", key="def_jump_hops", use_container_width=True):
        set_section("HOPS", team=team_label)
    if jd5.button("🏆 Impact Score", key="def_jump_impact", use_container_width=True):
        set_section("Impact Score")
