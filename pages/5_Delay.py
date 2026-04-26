from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import dataframe_to_excel_bytes, hero_block, inject_app_style, polish_plotly_figure, render_analyst_table, section_header

st.set_page_config(page_title="Michael Mackin Set Piece | Delay Analysis", page_icon="⚽", layout="wide")
inject_app_style()


@st.cache_data(show_spinner=False)
def load_delay_workbook() -> dict[str, pd.DataFrame]:
    return pd.read_excel("corner_delays (1).xlsx", sheet_name=None)


def _clean_delay_events(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
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


book = load_delay_workbook()
events = _clean_delay_events(book.get("All_Corners", pd.DataFrame()))
summary = book.get("Summary", pd.DataFrame()).copy()
diagnostics = book.get("Diagnostics", pd.DataFrame()).copy()
skipped = book.get("Skipped_Files", pd.DataFrame()).copy()

hero_block(
    "Corner timing intelligence",
    "Delay Analysis",
    "Workbook-level timing audit for corners: matched clearances/exits, delay bands, match reliability, and diagnostic coverage.",
)

if events.empty:
    st.warning("No delay events were found in corner_delays (1).xlsx.")
else:
    st.sidebar.header("Delay filters")
    matches = ["All"] + sorted(events["match"].dropna().astype(str).unique().tolist()) if "match" in events.columns else ["All"]
    periods = ["All"] + sorted(events["period"].dropna().astype(int).astype(str).unique().tolist()) if "period" in events.columns else ["All"]
    out_types = ["All"] + sorted(events["out_event_type"].dropna().astype(str).unique().tolist()) if "out_event_type" in events.columns else ["All"]

    with st.sidebar.expander("Scope", expanded=True):
        match = st.selectbox("Match", matches)
        period = st.selectbox("Period", periods)
    with st.sidebar.expander("Event filters", expanded=True):
        out_type = st.selectbox("Exit event", out_types)

    filtered = events.copy()
    if match != "All" and "match" in filtered.columns:
        filtered = filtered[filtered["match"].astype(str).eq(match)].copy()
    if period != "All" and "period" in filtered.columns:
        filtered = filtered[filtered["period"].astype("Int64").astype(str).eq(period)].copy()
    if out_type != "All" and "out_event_type" in filtered.columns:
        filtered = filtered[filtered["out_event_type"].astype(str).eq(out_type)].copy()

    if not filtered.empty and "delay_sec" in filtered.columns:
        lo = float(filtered["delay_sec"].min())
        hi = float(filtered["delay_sec"].max())
        with st.sidebar.expander("Timing window", expanded=True):
            delay_range = st.slider("Delay range (seconds)", min_value=lo, max_value=hi, value=(lo, hi))
        filtered = filtered[filtered["delay_sec"].between(delay_range[0], delay_range[1])].copy()

    nav_left, nav_mid, nav_right = st.columns([0.9, 1.1, 1.1])
    with nav_left:
        if st.button("Back to Home", use_container_width=True):
            st.switch_page("app.py")
    with nav_mid:
        st.download_button(
            "Export filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="delay_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with nav_right:
        st.download_button(
            "Export filtered Excel",
            data=dataframe_to_excel_bytes(filtered, sheet_name="Delay"),
            file_name="delay_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    total_events = int(len(filtered))
    matches_count = int(filtered["match"].nunique()) if "match" in filtered.columns else 0
    avg_delay = float(filtered["delay_sec"].mean()) if "delay_sec" in filtered.columns and not filtered.empty else 0.0
    median_delay = float(filtered["delay_sec"].median()) if "delay_sec" in filtered.columns and not filtered.empty else 0.0
    p90_delay = float(filtered["delay_sec"].quantile(0.9)) if "delay_sec" in filtered.columns and not filtered.empty else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Matched corners", total_events)
    c2.metric("Matches", matches_count)
    c3.metric("Avg delay", f"{avg_delay:.1f}s")
    c4.metric("Median delay", f"{median_delay:.1f}s")
    c5.metric("90th percentile", f"{p90_delay:.1f}s")

    if filtered.empty:
        st.warning("No rows match the active delay filters.")
        st.stop()

    overview_tab, charts_tab, audit_tab, data_tab = st.tabs(["Briefing", "Timing Evidence", "Audit", "Event Log"])

    with overview_tab:
        band_summary = (
            filtered.groupby("Delay band", dropna=False)
            .agg(
                Corners=("delay_sec", "size"),
                Avg_Delay=("delay_sec", "mean"),
                Median_Delay=("delay_sec", "median"),
                Min_Delay=("delay_sec", "min"),
                Max_Delay=("delay_sec", "max"),
            )
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
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"), Median_Delay=("delay_sec", "median"), Max_Delay=("delay_sec", "max"))
            .reset_index()
            .sort_values(["Avg_Delay", "Corners"], ascending=False)
        )
        match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]] = match_delay[["Avg_Delay", "Median_Delay", "Max_Delay"]].round(1)

        insight_cols = st.columns(3)
        top_band = str(band_summary.sort_values("Corners", ascending=False).iloc[0]["Delay band"]) if not band_summary.empty else "Unknown"
        top_exit = str(out_summary.iloc[0]["out_event_type"]) if not out_summary.empty else "Unknown"
        slow_match = str(match_delay.iloc[0]["match"]) if not match_delay.empty else "Unknown"

        with insight_cols[0]:
            st.markdown(
                f"<div class='mm-insight-card'>Most common delay band: <strong>{top_band}</strong>.</div>",
                unsafe_allow_html=True,
            )
        with insight_cols[1]:
            st.markdown(
                f"<div class='mm-insight-card'>Most common exit event: <strong>{top_exit}</strong>.</div>",
                unsafe_allow_html=True,
            )
        with insight_cols[2]:
            st.markdown(
                f"<div class='mm-insight-card'>Slowest average match in filter: <strong>{slow_match}</strong>.</div>",
                unsafe_allow_html=True,
            )

        left, right = st.columns([1, 1])
        with left:
            section_header("Delay Bands", "How long corners take before the matched exit event")
            render_analyst_table(band_summary, height=310)
        with right:
            section_header("Exit Profile", "Matched event type following the corner")
            render_analyst_table(out_summary, height=310)

        section_header("Slowest Match Profiles", "Highest average delay in the active filter")
        render_analyst_table(match_delay.head(30), height=430)

    with charts_tab:
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Delay Evidence")
            fig = px.histogram(filtered, x="delay_sec", nbins=24, color_discrete_sequence=["#111827"])
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Delay seconds", yaxis_title="Corners")
            st.plotly_chart(polish_plotly_figure(fig), use_container_width=True)
        with chart_right:
            section_header("Exit Event Evidence")
            box = px.box(filtered, x="out_event_type", y="delay_sec", color="out_event_type", color_discrete_sequence=["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309"])
            box.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend_title_text="", xaxis_title="", yaxis_title="Delay seconds")
            st.plotly_chart(polish_plotly_figure(box), use_container_width=True)

        section_header("Match Comparison", "Average delay by match")
        avg_by_match = (
            filtered.groupby("match", dropna=False)["delay_sec"]
            .mean()
            .reset_index(name="Avg delay")
            .sort_values("Avg delay", ascending=False)
            .head(20)
        )
        match_fig = px.bar(
            avg_by_match.sort_values("Avg delay"),
            x="Avg delay",
            y="match",
            orientation="h",
            color_discrete_sequence=["#c1121f"],
        )
        match_fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False, xaxis_title="Average delay (s)", yaxis_title="")
        st.plotly_chart(polish_plotly_figure(match_fig), use_container_width=True)

    with audit_tab:
        section_header("Workbook Summary Sheet", "Match-level extraction performance")
        if not summary.empty:
            summary_view = summary.copy()
            for col in ["avg_delay_sec", "median_delay_sec", "min_delay_sec", "max_delay_sec"]:
                if col in summary_view.columns:
                    summary_view[col] = pd.to_numeric(summary_view[col], errors="coerce").round(1)
            render_analyst_table(summary_view.sort_values("avg_delay_sec", ascending=False) if "avg_delay_sec" in summary_view.columns else summary_view, height=420)
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

    with data_tab:
        section_header("Matched Corner Event Log", f"{len(filtered):,} rows in the active filter")
        display_cols = [
            c for c in [
                "match", "period", "out_event_type", "out_value", "gk_outcome",
                "out_time_mmss", "corner_time_mmss", "delay_sec", "Delay band",
                "corner_event_index", "out_event_index",
            ]
            if c in filtered.columns
        ]
        render_analyst_table(filtered[display_cols], height=620)
