"""Delay Analysis section."""
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
    simple_view_radio,
)


def render_delay() -> None:
    book = _load_delay_workbook()
    events = _clean_delay_events(book.get("All_Corners", pd.DataFrame()))
    summary = book.get("Summary", pd.DataFrame()).copy()
    diagnostics = book.get("Diagnostics", pd.DataFrame()).copy()
    skipped = book.get("Skipped_Files", pd.DataFrame()).copy()

    hero_block("Timing", "Delay Analysis", "Simple corner timing checks.")
    if events.empty:
        st.warning("No delay events were found. Place a corner_delays*.xlsx file in the Data/ folder.")
        return

    leagues = ["All"] + sorted(events["League"].dropna().astype(str).unique().tolist()) if "League" in events.columns else ["All"]
    matches = ["All"] + sorted(events["match"].dropna().astype(str).unique().tolist()) if "match" in events.columns else ["All"]
    periods = ["All"] + sorted(events["period"].dropna().astype(int).astype(str).unique().tolist()) if "period" in events.columns else ["All"]
    out_types = ["All"] + sorted(events["out_event_type"].dropna().astype(str).unique().tolist()) if "out_event_type" in events.columns else ["All"]

    league = _league_selectbox("League", leagues, key="delay_league")
    match = st.sidebar.selectbox("Match", matches, key="delay_match")
    period = "All"
    out_type = "All"
    with st.sidebar.expander("More filters", expanded=False):
        period = st.selectbox("Period", periods, key="delay_period")
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

    full_delay_range = None
    delay_range = None
    if not filtered.empty and "delay_sec" in filtered.columns:
        lo = float(filtered["delay_sec"].min())
        hi = float(filtered["delay_sec"].max())
        full_delay_range = (lo, hi)
        with st.sidebar.expander("Delay range", expanded=False):
            delay_range = st.slider("Seconds", min_value=lo, max_value=hi, value=(lo, hi), key="delay_range")
        filtered = filtered[filtered["delay_sec"].between(delay_range[0], delay_range[1])].copy()

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
    c5.metric("90th percentile", f"{p90_delay:.1f}s")

    view = simple_view_radio("delay_view", ["Summary", "Charts", "Audit", "Rows"])
    if view == "Summary":
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
            .reset_index()
            .sort_values(["Corners", "Avg_Delay"], ascending=False)
        )
        out_summary[["Avg_Delay", "Median_Delay"]] = out_summary[["Avg_Delay", "Median_Delay"]].round(1)
        match_delay = (
            filtered.groupby("match", dropna=False)
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"),
                 Median_Delay=("delay_sec", "median"), Max_Delay=("delay_sec", "max"))
            .reset_index()
            .sort_values(["Avg_Delay", "Corners"], ascending=False)
        )
        match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]] = match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]].round(1)

        insight_cols = st.columns(3)
        with insight_cols[0]:
            top_band = band_summary.sort_values("Corners", ascending=False).iloc[0]["Delay band"] if not band_summary.empty else "Unknown"
            st.markdown(f"<div class='mm-insight-card'>Most common delay band: <strong>{top_band}</strong>.</div>", unsafe_allow_html=True)
        with insight_cols[1]:
            top_exit = out_summary.iloc[0]["out_event_type"] if not out_summary.empty else "Unknown"
            st.markdown(f"<div class='mm-insight-card'>Most common exit event: <strong>{top_exit}</strong>.</div>", unsafe_allow_html=True)
        with insight_cols[2]:
            slowest = match_delay.iloc[0]["match"] if not match_delay.empty else "Unknown"
            st.markdown(f"<div class='mm-insight-card'>Slowest average match in filter: <strong>{slowest}</strong>.</div>", unsafe_allow_html=True)

        left, right = st.columns(2)
        with left:
            section_header("Delay Bands", "How long corners take before the matched exit event")
            render_analyst_table(band_summary, height=310)
        with right:
            section_header("Exit Profile", "Matched event type following the corner")
            render_analyst_table(out_summary, height=310)
        section_header("Slowest Match Profiles", "Highest average delay in the active filter")
        render_analyst_table(match_delay.head(30), height=430)

    elif view == "Charts":
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Delay Evidence")
            fig = histogram_chart(filtered, "delay_sec", nbins=24)
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Delay seconds", yaxis_title="Corners")
            render_plotly_visual(polish_plotly_figure(fig), "Delay evidence", "delay_evidence_png")
        with chart_right:
            section_header("Exit Event Evidence")
            box = box_chart(filtered, x="out_event_type", y="delay_sec")
            box.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title_text="", xaxis_title="", yaxis_title="Delay seconds")
            render_plotly_visual(polish_plotly_figure(box), "Delay exit event evidence", "delay_exit_event_evidence_png")

        section_header("Match Comparison", "Average delay by match")
        avg_by_match = filtered.groupby("match", dropna=False)["delay_sec"].mean().reset_index(name="Avg delay").sort_values("Avg delay", ascending=False).head(20)
        match_fig = bar_chart(avg_by_match.sort_values("Avg delay"), x="Avg delay", y="match", orientation="h")
        match_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Average delay (s)", yaxis_title="")
        render_plotly_visual(polish_plotly_figure(match_fig), "Delay match comparison", "delay_match_comparison_png")

    elif view == "Audit":
        section_header("Workbook Summary Sheet", "Match-level extraction performance")
        if not summary.empty:
            summary_view = summary.copy()
            for col in ["avg_delay_sec", "median_delay_sec", "min_delay_sec", "max_delay_sec"]:
                if col in summary_view.columns:
                    summary_view[col] = pd.to_numeric(summary_view[col], errors="coerce").round(1)
            render_analyst_table(
                summary_view.sort_values("avg_delay_sec", ascending=False) if "avg_delay_sec" in summary_view.columns else summary_view,
                height=420,
            )
        else:
            st.info("No Summary sheet found.")
        section_header("Diagnostics Sheet", "Coverage checks from source event files")
        if not diagnostics.empty:
            render_analyst_table(diagnostics, height=360)
        else:
            st.info("No Diagnostics sheet found.")
        if not skipped.empty:
            section_header("Skipped Files", "Files not included in the timing extraction")
            render_analyst_table(skipped, height=260)

    elif view == "Rows":
        section_header("Rows", f"{len(filtered):,} rows")
        display_cols = [c for c in [
            "match", "period", "out_event_type", "out_value", "gk_outcome",
            "out_time_mmss", "corner_time_mmss", "delay_sec", "Delay band",
            "corner_event_index", "out_event_index",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=620)
