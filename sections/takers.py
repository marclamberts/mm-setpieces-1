"""Set Piece Takers — player-level delivery and shot-assist analysis."""
from __future__ import annotations

import streamlit as st
import pandas as pd
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

_CODE_V = "takers_v1"


@st.cache_data(show_spinner=False)
def _takers_data(_dv: str = DATA_VERSION, _cv: str = _CODE_V):
    corners   = _with_match_names(load_prepared_sp_data("Corners",   _dv))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(  _dv))
    throwins  = _with_match_names(load_prepared_sp_data("Throw ins", _dv))
    return corners, freekicks, throwins


def _tag_type(df: pd.DataFrame, sp_type: str) -> pd.DataFrame:
    out = df.copy()
    out["SP_Type"] = sp_type
    return out


def _build_combined(corners, freekicks, throwins) -> pd.DataFrame:
    pieces = []
    keep = ["Taker", "Team", "League", "SP_Type", "is_shot", "is_goal", "xg", "pass_x", "pass_y"]
    for df, label in [(corners, "Corner"), (freekicks, "Free Kick"), (throwins, "Throw-in")]:
        if df.empty:
            continue
        tmp = _tag_type(df, label)
        cols = [c for c in keep if c in tmp.columns]
        pieces.append(tmp[cols])
    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


def _taker_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Taker" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby(["Taker", "Team", "SP_Type"], dropna=False)
    tbl = grp.agg(
        Deliveries=("Taker", "count"),
        Shots=("is_shot", "sum"),
        Goals=("is_goal", "sum"),
        xG=("xg", "sum"),
    ).reset_index()
    tbl["Shot %"]    = (tbl["Shots"]  / tbl["Deliveries"] * 100).round(1)
    tbl["xG / 100"]  = (tbl["xG"]     / tbl["Deliveries"] * 100).round(2)
    tbl["xG"]        = tbl["xG"].round(2)
    tbl = tbl.sort_values("Deliveries", ascending=False).reset_index(drop=True)
    return tbl


def render_takers() -> None:
    corners, freekicks, throwins = _takers_data(DATA_VERSION, _CODE_V)
    combined = _build_combined(corners, freekicks, throwins)

    if combined.empty:
        hero_block("Takers", "Set Piece Takers", "No data available")
        st.warning("No taker data found.")
        return

    # ── Filters ──────────────────────────────────────────────────────────
    leagues = ["All"] + _safe_sorted(combined["League"]) if "League" in combined.columns else ["All"]
    teams   = ["All"] + _safe_sorted(combined["Team"])   if "Team"   in combined.columns else ["All"]
    sp_types = ["All", "Corner", "Free Kick", "Throw-in"]

    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        league = st.selectbox("League", leagues, key="takers_league")
    with fc2:
        team = st.selectbox("Team",   teams,   key="takers_team")
    with fc3:
        sp_type = st.selectbox("Type", sp_types, key="takers_type")
    st.markdown('</div>', unsafe_allow_html=True)

    filtered = combined.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]
    if team != "All" and "Team" in filtered.columns:
        filtered = filtered[filtered["Team"] == team]
    if sp_type != "All":
        filtered = filtered[filtered["SP_Type"] == sp_type]

    total_takers = filtered["Taker"].nunique() if "Taker" in filtered.columns else 0
    hero_block("👤", "Set Piece Takers", f"{total_takers:,} takers · {len(filtered):,} deliveries")
    st.session_state["ctx_row_count"] = f"Takers · {total_takers:,} takers"

    tbl = _taker_table(filtered)
    if tbl.empty:
        st.info("No takers match the current filters.")
        return

    tab_board, tab_profile, tab_compare = st.tabs(["Leaderboard", "Taker Profile", "Compare"])

    # ── Leaderboard ───────────────────────────────────────────────────────
    with tab_board:
        section_header("Top takers by deliveries")
        sort_by = st.radio("Sort by", ["Deliveries", "xG", "Shots", "Shot %", "xG / 100"],
                           horizontal=True, key="takers_sort")
        show = tbl.sort_values(sort_by, ascending=False).head(50).reset_index(drop=True)
        render_analyst_table(show, height=420)

        section_header("xG / 100 deliveries")
        chart_df = tbl[tbl["Deliveries"] >= 5].nlargest(20, "xG / 100")
        if not chart_df.empty:
            fig = px.bar(chart_df, x="xG / 100", y="Taker", orientation="h",
                         color="SP_Type", text="xG / 100",
                         color_discrete_sequence=["#22c55e", "#3b82f6", "#f59e0b"])
            fig.update_traces(textposition="outside")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=True)
            render_plotly_visual(polish_plotly_figure(fig), "takers_xg100_bar")

    # ── Taker Profile ─────────────────────────────────────────────────────
    with tab_profile:
        taker_names = _safe_sorted(tbl["Taker"])
        if not taker_names:
            st.info("No takers available.")
        else:
            selected_taker = st.selectbox("Select taker", taker_names, key="takers_profile_name")
            taker_rows = filtered[filtered["Taker"] == selected_taker]
            taker_stats = tbl[tbl["Taker"] == selected_taker]

            k1, k2, k3, k4, k5 = st.columns(5)
            if not taker_stats.empty:
                row = taker_stats.iloc[0]
                k1.metric("Deliveries", int(row["Deliveries"]))
                k2.metric("Shots",      int(row["Shots"]))
                k3.metric("Goals",      int(row["Goals"]))
                k4.metric("xG",         f"{row['xG']:.2f}")
                k5.metric("xG / 100",   f"{row['xG / 100']:.2f}")

            # Delivery zone scatter
            if "pass_x" in taker_rows.columns and "pass_y" in taker_rows.columns:
                section_header("Delivery start locations")
                pos_df = taker_rows[["pass_x", "pass_y", "SP_Type"]].dropna()
                if not pos_df.empty:
                    fig2 = px.scatter(pos_df, x="pass_x", y="pass_y", color="SP_Type",
                                      color_discrete_sequence=["#22c55e", "#3b82f6", "#f59e0b"],
                                      opacity=0.7)
                    fig2.update_layout(xaxis_range=[0, 120], yaxis_range=[0, 80],
                                       xaxis_title="x", yaxis_title="y")
                    render_plotly_visual(polish_plotly_figure(fig2), "takers_delivery_scatter")

            # Type breakdown
            section_header("Deliveries by type")
            type_grp = taker_rows.groupby("SP_Type").agg(
                Deliveries=("Taker", "count"),
                Shots=("is_shot", "sum"),
                xG=("xg", "sum"),
            ).reset_index()
            type_grp["xG"] = type_grp["xG"].round(2)
            render_analyst_table(type_grp, height=150)

    # ── Compare ───────────────────────────────────────────────────────────
    with tab_compare:
        taker_names_all = _safe_sorted(tbl["Taker"])
        ca, cb = st.columns(2)
        with ca:
            taker_a = st.selectbox("Taker A", taker_names_all, key="takers_cmp_a")
        with cb:
            default_b = taker_names_all[1] if len(taker_names_all) > 1 else taker_names_all[0]
            taker_b = st.selectbox("Taker B", taker_names_all,
                                   index=taker_names_all.index(default_b),
                                   key="takers_cmp_b")

        rows_a = tbl[tbl["Taker"] == taker_a]
        rows_b = tbl[tbl["Taker"] == taker_b]

        metrics = ["Deliveries", "Shots", "Goals", "xG", "Shot %", "xG / 100"]
        cmp_rows = []
        for m in metrics:
            va = rows_a[m].sum() if not rows_a.empty else 0
            vb = rows_b[m].sum() if not rows_b.empty else 0
            cmp_rows.append({"Metric": m, taker_a: round(float(va), 2), taker_b: round(float(vb), 2)})
        cmp_df = pd.DataFrame(cmp_rows)
        render_analyst_table(cmp_df, height=280)

        fig3 = px.bar(
            cmp_df[cmp_df["Metric"].isin(["Shot %", "xG / 100"])].melt(id_vars="Metric", var_name="Taker", value_name="Value"),
            x="Metric", y="Value", color="Taker", barmode="group",
            color_discrete_sequence=["#22c55e", "#3b82f6"],
        )
        render_plotly_visual(polish_plotly_figure(fig3), "takers_cmp_bar")
