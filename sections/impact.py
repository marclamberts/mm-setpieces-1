"""Set Piece Impact Score — composite team rating across all set piece phases."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    load_prepared_freekick_brief_data,
    render_analyst_table,
    hero_block,
    section_header,
    polish_plotly_figure,
)
from sections._shared import (
    _safe_sorted,
    _with_match_names,
    load_hops_data,
    render_plotly_visual,
)

_CODE_V = "impact_v2"

# ── Score weights ──────────────────────────────────────────────────────────
WEIGHTS = {
    "xG Threat":      0.28,
    "Shot Creation":  0.22,
    "Conversion":     0.20,
    "Volume":         0.15,
    "Aerial Power":   0.15,
}

# Sub-score weights (no Volume/Aerial for per-type; those are global)
SUB_WEIGHTS = {
    "xG Threat":    0.40,
    "Shot Creation": 0.35,
    "Conversion":   0.25,
}

COMPONENT_DESCRIPTIONS = {
    "xG Threat":    "Expected goals generated per 100 set piece deliveries. Measures quality of positions created.",
    "Shot Creation": "Shots generated per 100 set piece deliveries. Measures how often a delivery becomes a direct attempt.",
    "Conversion":   "Goals scored per shot from set pieces. Measures clinical finishing and penalty area execution.",
    "Volume":       "Set pieces earned per match relative to the league average. Rewards teams that win more restarts.",
    "Aerial Power": "Average HOPS rating of squad members. Measures aerial threat and defensive aerial resilience.",
}

COMPONENT_COLOURS = {
    "xG Threat":    "#22c55e",
    "Shot Creation": "#3b82f6",
    "Conversion":   "#f59e0b",
    "Volume":       "#8b5cf6",
    "Aerial Power": "#06b6d4",
}

TYPE_META = {
    "Corner":    ("⚽", "#22c55e", "corner_score"),
    "Free Kick": ("🎯", "#3b82f6", "fk_score"),
    "Throw-in":  ("↗",  "#f59e0b", "ti_score"),
}


# ── Data loading ────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _impact_data(_dv: str = DATA_VERSION, _cv: str = _CODE_V):
    corners   = _with_match_names(load_prepared_sp_data("Corners",   _dv))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(  _dv))
    throwins  = _with_match_names(load_prepared_sp_data("Throw ins", _dv))
    hops      = load_hops_data(_dv)
    return corners, freekicks, throwins, hops


# ── Score computation ───────────────────────────────────────────────────────

def _percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, method="average") * 100


def _agg_sp(df: pd.DataFrame, sp_type: str) -> pd.DataFrame:
    """Aggregate per-team stats for a single set piece type."""
    if df.empty:
        return pd.DataFrame()
    tmp = df.copy()
    keep = [c for c in ["Team", "League", "match_id", "xg", "is_shot", "is_goal"] if c in tmp.columns]
    tmp = tmp[keep]
    grp = tmp.groupby(["Team", "League"])
    stats = grp.agg(
        Deliveries=("is_shot", "count"),
        Shots=("is_shot", "sum"),
        Goals=("is_goal", "sum"),
        xG=("xg", "sum"),
    ).reset_index()
    if "match_id" in tmp.columns:
        mc = tmp.groupby("Team")["match_id"].nunique().reset_index().rename(columns={"match_id": "Matches"})
        stats = stats.merge(mc, on="Team", how="left")
    else:
        stats["Matches"] = 1
    stats["Matches"] = stats["Matches"].fillna(1).clip(lower=1)
    stats["xG_per_100"]    = (stats["xG"]    / stats["Deliveries"] * 100).fillna(0)
    stats["Shot_per_100"]  = (stats["Shots"] / stats["Deliveries"] * 100).fillna(0)
    stats["Goals_per_shot"] = (stats["Goals"] / stats["Shots"].replace(0, np.nan)).fillna(0)
    stats["SP_per_match"]  = stats["Deliveries"] / stats["Matches"]
    stats["SP_Type"] = sp_type
    return stats


def _compute_type_scores(type_stats: pd.DataFrame, score_col: str) -> pd.DataFrame:
    """Add percentile sub-score for a single type dataframe."""
    df = type_stats.copy()
    df["_pct_xg"]   = _percentile_rank(df["xG_per_100"])
    df["_pct_shot"] = _percentile_rank(df["Shot_per_100"])
    df["_pct_conv"] = _percentile_rank(df["Goals_per_shot"])
    df[score_col] = (
        df["_pct_xg"]   * SUB_WEIGHTS["xG Threat"]
        + df["_pct_shot"] * SUB_WEIGHTS["Shot Creation"]
        + df["_pct_conv"] * SUB_WEIGHTS["Conversion"]
    ).round(1)
    return df[["Team", "League", "Deliveries", "Shots", "Goals", "xG",
               "xG_per_100", "Shot_per_100", "Goals_per_shot", "SP_per_match",
               "_pct_xg", "_pct_shot", "_pct_conv", score_col]]


def _team_sp_stats(corners, freekicks, throwins) -> pd.DataFrame:
    """Combined per-team stats for the overall score."""
    pieces = []
    for df, label in [(corners, "Corner"), (freekicks, "Free Kick"), (throwins, "Throw-in")]:
        if df.empty:
            continue
        tmp = df.copy()
        tmp["SP_Type"] = label
        keep = [c for c in ["Team", "League", "match_id", "xg", "is_shot", "is_goal", "SP_Type"] if c in tmp.columns]
        pieces.append(tmp[keep])
    if not pieces:
        return pd.DataFrame()
    all_sp = pd.concat(pieces, ignore_index=True)
    grp = all_sp.groupby(["Team", "League"])
    stats = grp.agg(
        Deliveries=("SP_Type", "count"),
        Shots=("is_shot", "sum"),
        Goals=("is_goal", "sum"),
        xG=("xg", "sum"),
    ).reset_index()
    if "match_id" in all_sp.columns:
        mc = all_sp.groupby("Team")["match_id"].nunique().reset_index().rename(columns={"match_id": "Matches"})
        stats = stats.merge(mc, on="Team", how="left")
    else:
        stats["Matches"] = 1
    stats["Matches"] = stats["Matches"].fillna(1).clip(lower=1)
    stats["xG_per_100"]    = (stats["xG"]    / stats["Deliveries"] * 100).fillna(0)
    stats["Shot_per_100"]  = (stats["Shots"] / stats["Deliveries"] * 100).fillna(0)
    stats["Goals_per_shot"] = (stats["Goals"] / stats["Shots"].replace(0, np.nan)).fillna(0)
    stats["SP_per_match"]  = stats["Deliveries"] / stats["Matches"]
    return stats


def _compute_scores(stats: pd.DataFrame, hops: pd.DataFrame,
                    corner_sub: pd.DataFrame, fk_sub: pd.DataFrame, ti_sub: pd.DataFrame) -> pd.DataFrame:
    df = stats.copy()

    # HOPS
    if not hops.empty and "Team" in hops.columns and "Rating" in hops.columns:
        hops_avg = hops.groupby("Team")["Rating"].mean().reset_index().rename(columns={"Rating": "hops_avg"})
        df = df.merge(hops_avg, on="Team", how="left")
    else:
        df["hops_avg"] = np.nan
    df["hops_avg"] = df["hops_avg"].fillna(df["hops_avg"].median())

    # Overall components
    df["Score_xG Threat"]    = _percentile_rank(df["xG_per_100"])
    df["Score_Shot Creation"] = _percentile_rank(df["Shot_per_100"])
    df["Score_Conversion"]   = _percentile_rank(df["Goals_per_shot"])
    df["Score_Volume"]       = _percentile_rank(df["SP_per_match"])
    df["Score_Aerial Power"] = _percentile_rank(df["hops_avg"])

    df["Impact Score"] = (
        df["Score_xG Threat"]    * WEIGHTS["xG Threat"]
        + df["Score_Shot Creation"] * WEIGHTS["Shot Creation"]
        + df["Score_Conversion"]   * WEIGHTS["Conversion"]
        + df["Score_Volume"]       * WEIGHTS["Volume"]
        + df["Score_Aerial Power"] * WEIGHTS["Aerial Power"]
    ).round(1)

    # Merge sub-scores
    for sub, col in [(corner_sub, "corner_score"), (fk_sub, "fk_score"), (ti_sub, "ti_score")]:
        if not sub.empty and col in sub.columns:
            df = df.merge(sub[["Team", col]].drop_duplicates("Team"), on="Team", how="left")
        else:
            df[col] = np.nan

    return df


# ── Tier ─────────────────────────────────────────────────────────────────────

def _tier(score: float) -> tuple[str, str]:
    if pd.isna(score):   return "N/A",        "#475569"
    if score >= 80:      return "Elite",       "#22c55e"
    if score >= 65:      return "Strong",      "#3b82f6"
    if score >= 50:      return "Average",     "#f59e0b"
    if score >= 35:      return "Developing",  "#f97316"
    return                      "Weak",        "#ef4444"


# ── Sub-score badge row ───────────────────────────────────────────────────────

def _sub_score_badges(row: pd.Series) -> None:
    cols = st.columns(3)
    for col, (sp_type, (icon, colour, score_col)) in zip(cols, TYPE_META.items()):
        val = row.get(score_col, np.nan)
        tier_lbl, tier_col = _tier(val)
        val_str = f"{val:.1f}" if not pd.isna(val) else "—"
        col.markdown(
            f"""<div style="background:#161922;border:1px solid rgba(255,255,255,.1);
                border-top:2px solid {colour};border-radius:6px;
                padding:.6rem .9rem;text-align:center">
                <div style="font-size:.75rem;color:#94a3b8;margin-bottom:.15rem">{icon} {sp_type}</div>
                <div style="font-size:1.6rem;font-weight:800;color:{tier_col};line-height:1">{val_str}</div>
                <div style="font-size:.68rem;color:{tier_col};margin-top:.15rem">{tier_lbl}</div>
            </div>""",
            unsafe_allow_html=True,
        )


# ── Charts ────────────────────────────────────────────────────────────────────

def _radar_chart(component_scores: dict[str, float], team: str,
                 colour: str = "#22c55e", fill: str = "rgba(34,197,94,0.18)") -> go.Figure:
    cats = list(component_scores.keys())
    vals = list(component_scores.values())
    cats_c = cats + [cats[0]]
    vals_c = vals + [vals[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_c, theta=cats_c, fill="toself",
        fillcolor=fill, line=dict(color=colour, width=2), name=team,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=9, color="#64748b"),
                            gridcolor="rgba(255,255,255,.08)"),
            angularaxis=dict(tickfont=dict(size=11, color="#cbd5e1"),
                             gridcolor="rgba(255,255,255,.08)"),
            bgcolor="#161922",
        ),
        showlegend=False, margin=dict(l=50, r=50, t=40, b=40),
    )
    return polish_plotly_figure(fig)


def _type_radar(row: pd.Series, corner_sub: pd.DataFrame, fk_sub: pd.DataFrame,
                ti_sub: pd.DataFrame, team: str) -> go.Figure:
    """Radar showing sub-scores (xG Threat / Shot Creation / Conversion) for all 3 types."""
    cats = ["xG Threat", "Shot Creation", "Conversion"]
    traces = []
    for sp_type, (icon, colour, score_col), sub_df, pct_cols in [
        ("Corner",    TYPE_META["Corner"],    corner_sub, ("_pct_xg", "_pct_shot", "_pct_conv")),
        ("Free Kick", TYPE_META["Free Kick"], fk_sub,     ("_pct_xg", "_pct_shot", "_pct_conv")),
        ("Throw-in",  TYPE_META["Throw-in"],  ti_sub,     ("_pct_xg", "_pct_shot", "_pct_conv")),
    ]:
        trow = sub_df[sub_df["Team"] == team]
        if trow.empty:
            vals = [0, 0, 0]
        else:
            trow = trow.iloc[0]
            vals = [trow.get(p, 0) for p in pct_cols]
        cats_c = cats + [cats[0]]
        vals_c = vals + [vals[0]]
        traces.append((sp_type, icon, colour, cats_c, vals_c))

    fig = go.Figure()
    fill_map = {
        "Corner":    "rgba(34,197,94,.15)",
        "Free Kick": "rgba(59,130,246,.15)",
        "Throw-in":  "rgba(245,158,11,.15)",
    }
    for sp_type, icon, colour, cats_c, vals_c in traces:
        fig.add_trace(go.Scatterpolar(
            r=vals_c, theta=cats_c, fill="toself",
            fillcolor=fill_map[sp_type],
            line=dict(color=colour, width=2),
            name=f"{icon} {sp_type}",
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=9, color="#64748b"),
                            gridcolor="rgba(255,255,255,.08)"),
            angularaxis=dict(tickfont=dict(size=11, color="#cbd5e1"),
                             gridcolor="rgba(255,255,255,.08)"),
            bgcolor="#161922",
        ),
        legend=dict(font=dict(color="#cbd5e1")),
        margin=dict(l=50, r=50, t=40, b=40),
    )
    return polish_plotly_figure(fig)


def _league_ranking_chart(scores_df: pd.DataFrame, team: str, league: str,
                           score_col: str = "Impact Score", label: str = "Impact Score") -> go.Figure:
    df = scores_df[scores_df["League"] == league].copy() if league != "All" else scores_df.copy()
    df = df.dropna(subset=[score_col]).sort_values(score_col, ascending=True).tail(30)
    colours = ["#22c55e" if t == team else "#334155" for t in df["Team"]]
    fig = go.Figure(go.Bar(
        x=df[score_col], y=df["Team"], orientation="h",
        marker_color=colours,
        text=df[score_col].round(1), textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(tickfont=dict(size=10)),
        xaxis=dict(range=[0, 105], title=label),
        margin=dict(l=10, r=40, t=20, b=20),
        height=max(350, len(df) * 22),
    )
    return polish_plotly_figure(fig)


def _component_bar(row: pd.Series) -> go.Figure:
    components = list(WEIGHTS.keys())
    values = [row[f"Score_{c}"] for c in components]
    colours = [COMPONENT_COLOURS[c] for c in components]
    fig = go.Figure(go.Bar(
        x=components, y=values, marker_color=colours,
        text=[f"{v:.0f}" for v in values], textposition="outside",
    ))
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,.25)",
                  annotation_text="Avg (50)", annotation_position="right")
    fig.update_layout(yaxis=dict(range=[0, 110]), margin=dict(l=10, r=10, t=20, b=10))
    return polish_plotly_figure(fig)


def _scatter_score_vs_xg(scores_df: pd.DataFrame, team: str) -> go.Figure:
    df = scores_df.copy()
    fig = px.scatter(df, x="xG_per_100", y="Impact Score", hover_name="Team",
                     hover_data={"League": True, "Deliveries": True, "xG_per_100": ":.2f"},
                     color_discrete_sequence=["#334155"])
    sel = df[df["Team"] == team]
    if not sel.empty:
        fig.add_trace(go.Scatter(
            x=sel["xG_per_100"], y=sel["Impact Score"],
            mode="markers+text",
            marker=dict(color="#22c55e", size=14, line=dict(width=2, color="#fff")),
            text=[team], textposition="top center", showlegend=False,
        ))
    fig.update_layout(xaxis_title="xG per 100 deliveries", yaxis_title="Impact Score",
                      margin=dict(l=10, r=10, t=20, b=20))
    return polish_plotly_figure(fig)


def _sub_type_bar(corner_sub, fk_sub, ti_sub, team: str) -> go.Figure:
    """Grouped bar: xG Threat / Shot Creation / Conversion for each SP type."""
    metrics = ["xG Threat", "Shot Creation", "Conversion"]
    pct_cols = ["_pct_xg", "_pct_shot", "_pct_conv"]
    sp_types  = ["⚽ Corner", "🎯 Free Kick", "↗ Throw-in"]
    sub_dfs   = [corner_sub, fk_sub, ti_sub]
    colours   = ["#22c55e", "#3b82f6", "#f59e0b"]

    rows = []
    for metric, pct_col in zip(metrics, pct_cols):
        for sp_type, sub_df in zip(sp_types, sub_dfs):
            trow = sub_df[sub_df["Team"] == team]
            val = trow.iloc[0][pct_col] if not trow.empty else 0
            rows.append({"Metric": metric, "Type": sp_type, "Score": round(float(val), 1)})

    df = pd.DataFrame(rows)
    fig = px.bar(df, x="Metric", y="Score", color="Type", barmode="group",
                 color_discrete_sequence=colours)
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,.2)")
    fig.update_layout(yaxis=dict(range=[0, 110]), legend=dict(font=dict(color="#cbd5e1")),
                      margin=dict(l=10, r=10, t=20, b=10))
    return polish_plotly_figure(fig)


# ── Main render ───────────────────────────────────────────────────────────────

def render_impact() -> None:
    corners, freekicks, throwins, hops = _impact_data(DATA_VERSION, _CODE_V)

    # Compute sub-scores per type
    corner_sub = _compute_type_scores(_agg_sp(corners,   "Corner"),    "corner_score") if not corners.empty   else pd.DataFrame()
    fk_sub     = _compute_type_scores(_agg_sp(freekicks, "Free Kick"), "fk_score")     if not freekicks.empty else pd.DataFrame()
    ti_sub     = _compute_type_scores(_agg_sp(throwins,  "Throw-in"),  "ti_score")     if not throwins.empty  else pd.DataFrame()

    stats = _team_sp_stats(corners, freekicks, throwins)
    if stats.empty:
        hero_block("🏆", "Set Piece Impact Score", "No data available")
        st.warning("No set piece data found.")
        return

    scores_df = _compute_scores(stats, hops, corner_sub, fk_sub, ti_sub)

    # ── Filters ──────────────────────────────────────────────────────────
    leagues   = ["All"] + _safe_sorted(scores_df["League"])
    teams_all = _safe_sorted(scores_df["Team"])

    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    fc1, fc2 = st.columns([2, 3])
    with fc1:
        league_filter = st.selectbox("League", leagues, key="impact_league")
    with fc2:
        teams_in_scope = (
            _safe_sorted(scores_df[scores_df["League"] == league_filter]["Team"])
            if league_filter != "All" else teams_all
        )
        pre = st.session_state.get("impact_team")
        default_idx = teams_in_scope.index(pre) if pre and pre in teams_in_scope else 0
        selected_team = st.selectbox("Team", teams_in_scope, index=default_idx, key="impact_team")
    st.markdown('</div>', unsafe_allow_html=True)

    team_row = scores_df[scores_df["Team"] == selected_team]
    if team_row.empty:
        st.warning("No data for this team.")
        return
    row = team_row.iloc[0]

    score      = row["Impact Score"]
    tier_label, tier_colour = _tier(score)

    hero_block("🏆", "Set Piece Impact Score",
               f"{selected_team} · {tier_label} · {score:.1f} / 100")
    st.session_state["ctx_row_count"] = f"Impact · {selected_team} · {score:.1f}"

    # ── Header: overall badge + sub-score badges ──────────────────────────
    rank_df = scores_df.sort_values("Impact Score", ascending=False).reset_index(drop=True)
    rank_overall = int(rank_df[rank_df["Team"] == selected_team].index[0]) + 1
    league_df = scores_df[scores_df["League"] == row["League"]]
    rank_league = int(
        league_df.sort_values("Impact Score", ascending=False)
        .reset_index(drop=True)
        .pipe(lambda d: d[d["Team"] == selected_team]).index[0]
    ) + 1

    col_badge, col_sub = st.columns([1, 2])
    with col_badge:
        st.markdown(
            f"""<div style="background:#161922;border:2px solid {tier_colour};
                border-radius:10px;padding:1.2rem;text-align:center;margin-top:.3rem">
                <div style="font-size:.72rem;color:#94a3b8;margin-bottom:.2rem">Overall Impact Score</div>
                <div style="font-size:3rem;font-weight:800;color:{tier_colour};line-height:1">{score:.1f}</div>
                <div style="font-size:.85rem;color:{tier_colour};font-weight:600;margin-top:.25rem">{tier_label}</div>
                <div style="font-size:.72rem;color:#64748b;margin-top:.4rem">
                    #{rank_overall:,} overall · #{rank_league:,} in league
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col_sub:
        section_header("Sub-scores by set piece type")
        _sub_score_badges(row)
        st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Deliveries", f"{int(row['Deliveries']):,}")
        k2.metric("Shots",      f"{int(row['Shots']):,}")
        k3.metric("xG total",   f"{row['xG']:.1f}")
        k4.metric("Goals",      f"{int(row['Goals']):,}")

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab_overview, tab_sub, tab_components, tab_league, tab_compare = st.tabs([
        "Overview", "By Set Piece Type", "Component Breakdown", "League Ranking", "Compare Teams"
    ])

    # ── Overview ──────────────────────────────────────────────────────────
    with tab_overview:
        c_radar, c_bars = st.columns([1, 1])
        with c_radar:
            section_header("Strength profile (overall)")
            comp_scores = {c: row[f"Score_{c}"] for c in WEIGHTS}
            render_plotly_visual(_radar_chart(comp_scores, selected_team),
                                 "Radar Profile", "impact_radar")
        with c_bars:
            section_header("Component scores vs average (50)")
            render_plotly_visual(_component_bar(row), "Component Scores", "impact_comp_bar")

        section_header("Impact Score vs xG Threat — all teams")
        render_plotly_visual(_scatter_score_vs_xg(scores_df, selected_team),
                             "Score vs xG Scatter", "impact_scatter")

    # ── By Set Piece Type ─────────────────────────────────────────────────
    with tab_sub:
        section_header("Component scores per set piece type")
        render_plotly_visual(
            _sub_type_bar(corner_sub, fk_sub, ti_sub, selected_team),
            "Sub-type Component Bars", "impact_sub_bars",
        )

        section_header("Threat profile overlay — Corners vs Free Kicks vs Throw-ins")
        render_plotly_visual(
            _type_radar(row, corner_sub, fk_sub, ti_sub, selected_team),
            "Type Radar Overlay", "impact_type_radar",
        )

        section_header("Sub-score detail")
        sub_rows = []
        for sp_type, (icon, colour, score_col), sub_df, pct_cols in [
            ("Corner",    TYPE_META["Corner"],    corner_sub, ("_pct_xg", "_pct_shot", "_pct_conv")),
            ("Free Kick", TYPE_META["Free Kick"], fk_sub,     ("_pct_xg", "_pct_shot", "_pct_conv")),
            ("Throw-in",  TYPE_META["Throw-in"],  ti_sub,     ("_pct_xg", "_pct_shot", "_pct_conv")),
        ]:
            trow = sub_df[sub_df["Team"] == selected_team]
            if trow.empty:
                sub_rows.append({"Type": f"{icon} {sp_type}", "Sub-score": "—",
                                 "xG Threat": "—", "Shot Creation": "—", "Conversion": "—",
                                 "Deliveries": "—", "Shots": "—", "Goals": "—", "xG/100": "—"})
            else:
                tr = trow.iloc[0]
                sub_rows.append({
                    "Type":          f"{icon} {sp_type}",
                    "Sub-score":     round(tr[score_col], 1),
                    "xG Threat":     round(tr["_pct_xg"],   1),
                    "Shot Creation": round(tr["_pct_shot"],  1),
                    "Conversion":    round(tr["_pct_conv"],  1),
                    "Deliveries":    int(tr["Deliveries"]),
                    "Shots":         int(tr["Shots"]),
                    "Goals":         int(tr["Goals"]),
                    "xG/100":        round(tr["xG_per_100"], 2),
                })
        render_analyst_table(pd.DataFrame(sub_rows), height=180)

        # League ranking by sub-score
        section_header("League ranking by sub-score")
        sub_rank_type = st.radio(
            "Rank by", ["⚽ Corner", "🎯 Free Kick", "↗ Throw-in"],
            horizontal=True, key="impact_sub_rank_type",
        )
        sub_col_map = {"⚽ Corner": ("corner_score", corner_sub),
                       "🎯 Free Kick": ("fk_score", fk_sub),
                       "↗ Throw-in": ("ti_score", ti_sub)}
        sub_col, sub_src = sub_col_map[sub_rank_type]
        if not sub_src.empty and sub_col in sub_src.columns:
            league_for_sub = row["League"] if league_filter == "All" else league_filter
            sub_league = sub_src[sub_src["League"] == league_for_sub] if "League" in sub_src.columns else sub_src
            render_plotly_visual(
                _league_ranking_chart(
                    sub_league.rename(columns={sub_col: "Impact Score"}),
                    selected_team, "All", "Impact Score", sub_rank_type,
                ),
                f"{sub_rank_type} Ranking", "impact_sub_rank_chart",
            )
        else:
            st.info("No sub-score data for this type.")

    # ── Component Breakdown ───────────────────────────────────────────────
    with tab_components:
        section_header("What makes up the overall score?")
        raw_map = {"xG Threat": "xG_per_100", "Shot Creation": "Shot_per_100",
                   "Conversion": "Goals_per_shot", "Volume": "SP_per_match",
                   "Aerial Power": "hops_avg"}
        for comp, weight in WEIGHTS.items():
            comp_score = row[f"Score_{comp}"]
            colour = COMPONENT_COLOURS[comp]
            tier_c, tier_col_c = _tier(comp_score)
            raw_col = raw_map.get(comp)
            raw_val = f"{row[raw_col]:.3f}" if raw_col and raw_col in row.index else "—"
            st.markdown(
                f"""<div style="background:#161922;border:1px solid rgba(255,255,255,.08);
                    border-left:3px solid {colour};border-radius:6px;
                    padding:.75rem 1rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem">
                    <div style="min-width:160px">
                        <div style="font-weight:700;font-size:.9rem">{comp}</div>
                        <div style="font-size:.72rem;color:#64748b">weight: {int(weight*100)}%</div>
                    </div>
                    <div style="flex:1;background:rgba(255,255,255,.05);border-radius:4px;height:8px">
                        <div style="background:{colour};width:{comp_score:.0f}%;height:8px;border-radius:4px"></div>
                    </div>
                    <div style="min-width:60px;text-align:right;font-weight:700;font-size:1.1rem;color:{tier_col_c}">{comp_score:.0f}</div>
                    <div style="min-width:70px;font-size:.78rem;color:{tier_col_c}">{tier_c}</div>
                    <div style="min-width:70px;font-size:.78rem;color:#94a3b8">raw: {raw_val}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("---")
        section_header("Component descriptions")
        for comp, desc in COMPONENT_DESCRIPTIONS.items():
            st.caption(f"**{comp}** — {desc}")

    # ── League Ranking ────────────────────────────────────────────────────
    with tab_league:
        league_for_rank = row["League"] if league_filter == "All" else league_filter
        rank_by = st.radio("Rank by",
                           ["Overall", "⚽ Corners", "🎯 Free Kicks", "↗ Throw-ins"],
                           horizontal=True, key="impact_rank_by")
        rank_col_map = {
            "Overall":       ("Impact Score", scores_df),
            "⚽ Corners":    ("corner_score", scores_df),
            "🎯 Free Kicks": ("fk_score",     scores_df),
            "↗ Throw-ins":  ("ti_score",     scores_df),
        }
        rank_col, rank_src = rank_col_map[rank_by]
        section_header(f"Rankings by {rank_by} — {league_for_rank}")
        render_plotly_visual(
            _league_ranking_chart(rank_src, selected_team, league_for_rank, rank_col, rank_by),
            f"{rank_by} Ranking", "impact_league_rank",
        )

        section_header("Full table")
        display_df = scores_df.copy()
        if league_filter != "All":
            display_df = display_df[display_df["League"] == league_filter]
        display_df = display_df.sort_values("Impact Score", ascending=False).reset_index(drop=True)
        display_df["Rank"] = range(1, len(display_df) + 1)
        display_df["Tier"] = display_df["Impact Score"].apply(lambda s: _tier(s)[0])
        for c in ["xG", "xG_per_100", "Shot_per_100", "Goals_per_shot", "SP_per_match",
                  "corner_score", "fk_score", "ti_score"]:
            if c in display_df.columns:
                display_df[c] = display_df[c].round(2)
        show = display_df.rename(columns={
            "xG_per_100": "xG/100", "Shot_per_100": "Shots/100",
            "Goals_per_shot": "Goals/Shot", "SP_per_match": "SP/Match",
            "corner_score": "⚽ Corner", "fk_score": "🎯 FK", "ti_score": "↗ TI",
        })
        cols_order = ["Rank", "Team", "League", "Impact Score", "Tier",
                      "⚽ Corner", "🎯 FK", "↗ TI",
                      "Deliveries", "Shots", "Goals", "xG",
                      "xG/100", "Shots/100", "Goals/Shot", "SP/Match"]
        show = show[[c for c in cols_order if c in show.columns]]
        render_analyst_table(show, height=500)

    # ── Compare Teams ─────────────────────────────────────────────────────
    with tab_compare:
        teams_for_cmp = teams_in_scope if league_filter != "All" else teams_all
        cmp_team = st.selectbox(
            "Compare with",
            [t for t in teams_for_cmp if t != selected_team],
            key="impact_cmp_team",
        )
        row_b = scores_df[scores_df["Team"] == cmp_team]
        if row_b.empty:
            st.info("No data for comparison team.")
        else:
            row_b = row_b.iloc[0]
            score_b   = row_b["Impact Score"]
            tier_b, col_b = _tier(score_b)

            # Overall badge pair
            ca, cb = st.columns(2)
            with ca:
                st.markdown(
                    f'<div style="background:#161922;border:2px solid {tier_colour};border-radius:8px;'
                    f'padding:1rem;text-align:center"><div style="font-size:2rem;font-weight:800;color:{tier_colour}">'
                    f'{score:.1f}</div><div style="font-weight:600">{selected_team}</div>'
                    f'<div style="font-size:.8rem;color:{tier_colour}">{tier_label}</div></div>',
                    unsafe_allow_html=True,
                )
            with cb:
                st.markdown(
                    f'<div style="background:#161922;border:2px solid {col_b};border-radius:8px;'
                    f'padding:1rem;text-align:center"><div style="font-size:2rem;font-weight:800;color:{col_b}">'
                    f'{score_b:.1f}</div><div style="font-weight:600">{cmp_team}</div>'
                    f'<div style="font-size:.8rem;color:{col_b}">{tier_b}</div></div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            # Sub-score comparison
            section_header("Sub-scores by type")
            ss_rows = []
            for sp_type, (icon, colour, score_col) in TYPE_META.items():
                va = row.get(score_col, np.nan)
                vb = row_b.get(score_col, np.nan)
                ss_rows.append({
                    "Type": f"{icon} {sp_type}",
                    selected_team: round(float(va), 1) if not pd.isna(va) else "—",
                    cmp_team:      round(float(vb), 1) if not pd.isna(vb) else "—",
                })
            render_analyst_table(pd.DataFrame(ss_rows), height=160)

            # Overall component comparison
            section_header("Overall component scores")
            cmp_rows = [
                {"Component": c, selected_team: round(row[f"Score_{c}"], 1),
                 cmp_team: round(row_b[f"Score_{c}"], 1)}
                for c in WEIGHTS
            ]
            cmp_df = pd.DataFrame(cmp_rows)
            render_analyst_table(cmp_df, height=240)

            melted = cmp_df.melt(id_vars="Component", var_name="Team", value_name="Score")
            fig_cmp = px.bar(melted, x="Component", y="Score", color="Team", barmode="group",
                             color_discrete_sequence=["#22c55e", "#3b82f6"])
            fig_cmp.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,.2)")
            fig_cmp.update_layout(yaxis=dict(range=[0, 110]),
                                  legend=dict(font=dict(color="#cbd5e1")))
            render_plotly_visual(polish_plotly_figure(fig_cmp), "Component Comparison", "impact_cmp_bar")

            # Dual radar overlay
            section_header("Radar overlay")
            comp_a = {c: row[f"Score_{c}"]   for c in WEIGHTS}
            comp_b = {c: row_b[f"Score_{c}"] for c in WEIGHTS}
            cats = list(WEIGHTS.keys())
            cats_c = cats + [cats[0]]
            fig_ov = go.Figure()
            fig_ov.add_trace(go.Scatterpolar(
                r=[comp_a[c] for c in cats_c], theta=cats_c, fill="toself",
                fillcolor="rgba(34,197,94,.15)", line=dict(color="#22c55e", width=2),
                name=selected_team,
            ))
            fig_ov.add_trace(go.Scatterpolar(
                r=[comp_b[c] for c in cats_c], theta=cats_c, fill="toself",
                fillcolor="rgba(59,130,246,.15)", line=dict(color="#3b82f6", width=2),
                name=cmp_team,
            ))
            fig_ov.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100],
                                    tickfont=dict(size=9, color="#64748b"),
                                    gridcolor="rgba(255,255,255,.08)"),
                    angularaxis=dict(tickfont=dict(size=11, color="#cbd5e1"),
                                     gridcolor="rgba(255,255,255,.08)"),
                    bgcolor="#161922",
                ),
                legend=dict(font=dict(color="#cbd5e1")),
                margin=dict(l=50, r=50, t=40, b=40),
            )
            render_plotly_visual(polish_plotly_figure(fig_ov), "Radar Overlay", "impact_radar_cmp")
