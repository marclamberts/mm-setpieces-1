"""Delay Analysis section — tabbed layout."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    render_analyst_table,
    hero_block,
    section_header,
    render_export_controls,
    render_filter_summary,
    render_empty_filter_state,
    polish_plotly_figure,
)

from sections._shared import (
    _league_selectbox,
    _load_delay_workbook,
    _clean_delay_events,
    histogram_chart,
    box_chart,
    bar_chart,
    render_plotly_visual,
)


def render_delay() -> None:
    book = _load_delay_workbook()
    events = _clean_delay_events(book.get("All_Corners", pd.DataFrame()))
    summary_sheet = book.get("Summary", pd.DataFrame()).copy()
    diagnostics = book.get("Diagnostics", pd.DataFrame()).copy()
    skipped = book.get("Skipped_Files", pd.DataFrame()).copy()

    if events.empty:
        st.warning("No delay events found. Place a `corner_delays*.xlsx` file in the Data/ folder.")
        return

    leagues = ["All"] + sorted(events["League"].dropna().astype(str).unique().tolist()) if "League" in events.columns else ["All"]
    matches = ["All"] + sorted(events["match"].dropna().astype(str).unique().tolist()) if "match" in events.columns else ["All"]
    periods = ["All"] + sorted(events["period"].dropna().astype(int).astype(str).unique().tolist()) if "period" in events.columns else ["All"]
    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Filters</div>', unsafe_allow_html=True)
    out_types = ["All"] + sorted(events["out_event_type"].dropna().astype(str).unique().tolist()) if "out_event_type" in events.columns else ["All"]

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        league = _league_selectbox("League", leagues, key="delay_league")
    with fc2:
        match = st.selectbox("Match", matches, key="delay_match")
    with fc3:
        period = st.selectbox("Period", periods, key="delay_period")
    with fc4:
        out_type = st.selectbox("Exit event", out_types, key="delay_exit")

    filtered = events.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].astype(str).eq(league)].copy()
    if match != "All" and "match" in filtered.columns:
        filtered = filtered[filtered["match"].astype(str).eq(match)].copy()
    if period != "All" and "period" in filtered.columns:
        filtered = filtered[filtered["period"].astype("Int64").astype(str).eq(period)].copy()
    if out_type != "All" and "out_event_type" in filtered.columns:
        filtered = filtered[filtered["out_event_type"].astype(str).eq(out_type)].copy()

    full_delay_range = None; delay_range = None
    if not filtered.empty and "delay_sec" in filtered.columns:
        lo = float(filtered["delay_sec"].min())
        hi = float(filtered["delay_sec"].max())
        full_delay_range = (lo, hi)
        delay_range = st.slider("Delay range (seconds)", min_value=lo, max_value=hi, value=(lo, hi), key="delay_range")
        filtered = filtered[filtered["delay_sec"].between(delay_range[0], delay_range[1])].copy()
    st.markdown('</div>', unsafe_allow_html=True)

    scope_parts = [p for p in [match if match != "All" else None, league if league != "All" else None] if p]
    scope_str = " · ".join(scope_parts) if scope_parts else "All matches"
    hero_block("Timing", "Delay Analysis", f"{scope_str} · {len(filtered):,} events")

    render_export_controls(filtered, "delay", "Delay")
    filters = [
        ("League", league), ("Match", match), ("Period", period), ("Exit", out_type),
        ("Delay", f"{delay_range[0]:.1f}-{delay_range[1]:.1f}s" if delay_range and delay_range != full_delay_range else "All"),
    ]
    render_filter_summary("Delay Analysis", len(events), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()
        return

    total_events = int(len(filtered))
    matches_count = int(filtered["match"].nunique()) if "match" in filtered.columns else 0
    avg_delay = float(filtered["delay_sec"].mean()) if "delay_sec" in filtered.columns else 0.0
    median_delay = float(filtered["delay_sec"].median()) if "delay_sec" in filtered.columns else 0.0
    p90_delay = float(filtered["delay_sec"].quantile(0.9)) if "delay_sec" in filtered.columns else 0.0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Matched corners", total_events)
    c2.metric("Matches", matches_count)
    c3.metric("Avg delay", f"{avg_delay:.1f}s")
    c4.metric("Median delay", f"{median_delay:.1f}s")
    c5.metric("90th pct", f"{p90_delay:.1f}s")

    tab_summary, tab_charts, tab_match, tab_audit, tab_rows = st.tabs([
        "📊 Summary", "📈 Charts", "🏟️ Match view", "🔍 Audit", "🗃️ Rows"
    ])

    # ── Summary ───────────────────────────────────────────────────────────────
    with tab_summary:
        band_summary = (
            filtered.groupby("Delay band", dropna=False)
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"),
                 Median_Delay=("delay_sec", "median"), Min_Delay=("delay_sec", "min"), Max_Delay=("delay_sec", "max"))
            .reset_index()
        )
        for col in ["Avg_Delay", "Median_Delay", "Min_Delay", "Max_Delay"]:
            if col in band_summary.columns:
                band_summary[col] = band_summary[col].round(1)

        out_summary = (
            filtered.groupby("out_event_type", dropna=False)
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"), Median_Delay=("delay_sec", "median"))
            .reset_index().sort_values(["Corners", "Avg_Delay"], ascending=False)
        )
        out_summary[["Avg_Delay", "Median_Delay"]] = out_summary[["Avg_Delay", "Median_Delay"]].round(1)

        if not band_summary.empty:
            top_band = band_summary.sort_values("Corners", ascending=False).iloc[0]["Delay band"]
            st.markdown(f"<div class='mm-insight-card'>Most common delay band: <strong>{top_band}</strong></div>", unsafe_allow_html=True)
        if not out_summary.empty:
            st.markdown(f"<div class='mm-insight-card'>Most common exit event: <strong>{out_summary.iloc[0]['out_event_type']}</strong></div>", unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            section_header("Delay bands", "Distribution across time windows")
            render_analyst_table(band_summary, height=320, invert_cols=["Avg_Delay", "Median_Delay", "Min_Delay", "Max_Delay"])
        with right:
            section_header("Exit profile", "What event follows the corner")
            render_analyst_table(out_summary, height=320, invert_cols=["Avg_Delay", "Median_Delay"])

    # ── Charts ────────────────────────────────────────────────────────────────
    with tab_charts:
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Delay distribution")
            fig = histogram_chart(filtered, "delay_sec", nbins=28)
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Delay (s)", yaxis_title="Corners")
            render_plotly_visual(polish_plotly_figure(fig), "Delay distribution", "delay_hist_png")
        with chart_right:
            section_header("Delay by exit event")
            box = box_chart(filtered, x="out_event_type", y="delay_sec")
            box.update_layout(margin=dict(l=10, r=10, t=30, b=10), xaxis_title="", yaxis_title="Delay (s)")
            render_plotly_visual(polish_plotly_figure(box), "Delay by exit event", "delay_box_png")

        if "Delay band" in filtered.columns:
            section_header("Band breakdown")
            band_fig = bar_chart(
                filtered.groupby("Delay band", dropna=False).size().reset_index(name="Corners"),
                x="Delay band", y="Corners", color="Delay band",
            )
            band_fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            render_plotly_visual(polish_plotly_figure(band_fig), "Delay bands chart", "delay_band_chart_png")

    # ── Match view ────────────────────────────────────────────────────────────
    with tab_match:
        section_header("Per-match averages", "Slowest matches in the filter")
        match_delay = (
            filtered.groupby("match", dropna=False)
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"),
                 Median_Delay=("delay_sec", "median"), Max_Delay=("delay_sec", "max"))
            .reset_index().sort_values(["Avg_Delay", "Corners"], ascending=False)
        )
        match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]] = match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]].round(1)
        if not match_delay.empty:
            st.markdown(f"<div class='mm-insight-card'>Slowest match: <strong>{match_delay.iloc[0]['match']}</strong> — avg {match_delay.iloc[0]['Avg_Delay']:.1f}s</div>", unsafe_allow_html=True)
        render_analyst_table(match_delay.head(35), height=460, invert_cols=["Avg_Delay", "Median_Delay", "Max_Delay"])

        avg_by_match = match_delay.sort_values("Avg_Delay").tail(20)
        match_fig = bar_chart(avg_by_match, x="Avg_Delay", y="match", orientation="h")
        match_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Avg delay (s)", yaxis_title="")
        render_plotly_visual(polish_plotly_figure(match_fig), "Delay match comparison", "delay_match_comparison_png")

    # ── Audit ─────────────────────────────────────────────────────────────────
    with tab_audit:
        section_header("Workbook summary", "Match-level extraction coverage")
        if not summary_sheet.empty:
            sv = summary_sheet.copy()
            for col in ["avg_delay_sec", "median_delay_sec", "min_delay_sec", "max_delay_sec"]:
                if col in sv.columns:
                    sv[col] = pd.to_numeric(sv[col], errors="coerce").round(1)
            render_analyst_table(sv.sort_values("avg_delay_sec", ascending=False) if "avg_delay_sec" in sv.columns else sv, height=440)
        else:
            st.info("No Summary sheet found in workbook.")
        section_header("Diagnostics")
        if not diagnostics.empty:
            render_analyst_table(diagnostics, height=360)
        else:
            st.info("No Diagnostics sheet found.")
        if not skipped.empty:
            section_header("Skipped files")
            render_analyst_table(skipped, height=260)

    # ── Rows ──────────────────────────────────────────────────────────────────
    with tab_rows:
        section_header("Raw rows", f"{len(filtered):,} events")
        display_cols = [c for c in [
            "match", "period", "out_event_type", "out_value", "gk_outcome",
            "out_time_mmss", "corner_time_mmss", "delay_sec", "Delay band",
            "corner_event_index", "out_event_index",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=640)
