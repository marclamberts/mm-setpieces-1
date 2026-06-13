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
    render_export_controls,
)

from sections._shared import (
    _safe_sorted,
    _with_match_names,
    load_hops_data,
    render_plotly_visual,
    render_mpl_visual,
    set_section,
)

_CODE_V = "takers_v1"


@st.cache_data(show_spinner="Loading data…")
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
            render_plotly_visual(polish_plotly_figure(fig), "xG / 100 by Taker", "takers_xg100_bar")

    # ── Taker Profile ─────────────────────────────────────────────────────
    with tab_profile:
        corners_raw, freekicks_raw, throwins_raw = _takers_data(DATA_VERSION, _CODE_V)
        hops = load_hops_data(DATA_VERSION)

        taker_names = _safe_sorted(tbl["Taker"])
        if not taker_names:
            st.info("No takers available.")
        else:
            selected_taker = st.selectbox("Select taker", taker_names, key="takers_profile_name")
            taker_rows = filtered[filtered["Taker"] == selected_taker]
            taker_stats = tbl[tbl["Taker"] == selected_taker]

            # Team + HOPS badge
            taker_team = taker_stats["Team"].iloc[0] if not taker_stats.empty and "Team" in taker_stats.columns else ""
            hops_row = hops[hops["Player"].astype(str).eq(selected_taker)] if not hops.empty and "Player" in hops.columns else pd.DataFrame()

            header_col, badge_col = st.columns([3, 1])
            with header_col:
                st.markdown(
                    f"<div style='font-size:1.5rem;font-weight:800;color:#fff;margin-bottom:.1rem'>{selected_taker}</div>"
                    f"<div style='font-size:.82rem;color:#94a3b8'>{taker_team}</div>",
                    unsafe_allow_html=True,
                )
            with badge_col:
                if not hops_row.empty:
                    hr = hops_row.iloc[0]
                    tier_colors = {"Elite": "#22c55e", "Strong": "#3b82f6", "Rotation": "#f59e0b", "Depth": "#94a3b8"}
                    tc = tier_colors.get(str(hr.get("Tier", "")), "#94a3b8")
                    st.markdown(
                        f"<div style='background:#161922;border:1px solid {tc};border-radius:6px;"
                        f"padding:.5rem .8rem;text-align:center'>"
                        f"<div style='font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em'>HOPS</div>"
                        f"<div style='font-size:1.3rem;font-weight:800;color:{tc}'>{float(hr['Rating']):.3f}</div>"
                        f"<div style='font-size:.65rem;color:{tc}'>{hr.get('Tier','')}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            # KPI strip
            if not taker_stats.empty:
                agg = taker_stats.agg({"Deliveries": "sum", "Shots": "sum", "Goals": "sum", "xG": "sum"}).to_dict()
                dels = max(int(agg["Deliveries"]), 1)
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("Deliveries", f"{dels:,}")
                k2.metric("Shots",      int(agg["Shots"]))
                k3.metric("Goals",      int(agg["Goals"]))
                k4.metric("xG",         f"{agg['xG']:.2f}")
                k5.metric("xG / 100",   f"{agg['xG'] / dels * 100:.2f}")
                k6.metric("Shot %",     f"{agg['Shots'] / dels * 100:.1f}%")

            # Pitch delivery map + type breakdown side by side
            pm_col, tb_col = st.columns([1, 1])
            with pm_col:
                section_header("Delivery start locations")
                if "pass_x" in taker_rows.columns and "pass_y" in taker_rows.columns:
                    import matplotlib.pyplot as plt
                    from mplsoccer import Pitch as MplPitch
                    pos_df = taker_rows[["pass_x", "pass_y", "SP_Type"]].dropna()
                    pos_df["pass_x"] = pd.to_numeric(pos_df["pass_x"], errors="coerce")
                    pos_df["pass_y"] = pd.to_numeric(pos_df["pass_y"], errors="coerce")
                    pos_df = pos_df.dropna()
                    if not pos_df.empty:
                        mfig, max_ = plt.subplots(figsize=(6, 4))
                        mfig.patch.set_facecolor("#161922")
                        mp = MplPitch(pitch_type="statsbomb", pitch_color="#1a2438", line_color="#4b5563", linewidth=1.2)
                        mp.draw(ax=max_)
                        color_map = {"Corner": "#22c55e", "Free Kick": "#3b82f6", "Throw-in": "#f59e0b"}
                        for sp, grp in pos_df.groupby("SP_Type", dropna=False):
                            mp.scatter(grp["pass_x"], grp["pass_y"], ax=max_,
                                       s=40, color=color_map.get(str(sp), "#94a3b8"),
                                       alpha=0.75, label=str(sp), zorder=4)
                        max_.legend(loc="lower right", fontsize=7, framealpha=0,
                                    labelcolor="white")
                        mfig.tight_layout(pad=0.3)
                        render_mpl_visual(mfig, "Delivery start map", "takers_profile_pitch")
                else:
                    st.info("No pass location data available.")

            with tb_col:
                section_header("Deliveries by type")
                type_grp = taker_rows.groupby("SP_Type", dropna=False).agg(
                    Deliveries=("Taker", "count"),
                    Shots=("is_shot", "sum"),
                    Goals=("is_goal", "sum"),
                    xG=("xg", "sum"),
                ).reset_index()
                type_grp["xG"] = type_grp["xG"].round(2)
                type_grp["xG / 100"] = (type_grp["xG"] / type_grp["Deliveries"].clip(lower=1) * 100).round(2)
                render_analyst_table(type_grp, height=200)

                section_header("Jump to detailed analysis")
                jt1, jt2 = st.columns(2)
                if jt1.button(f"⚽ Corners — {taker_team}", key="takers_jump_corners", use_container_width=True):
                    set_section("Corners", team=taker_team if taker_team else None)
                if jt2.button(f"🎯 Free Kicks — {taker_team}", key="takers_jump_fk", use_container_width=True):
                    set_section("Freekicks", team=taker_team if taker_team else None)

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
        render_plotly_visual(polish_plotly_figure(fig3), "Taker Comparison", "takers_cmp_bar")
