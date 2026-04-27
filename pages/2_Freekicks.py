from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

_PAGE_FILE = Path(__file__).resolve()
_UTILS_FILE = _PAGE_FILE.parents[1] / "mm_setpieces" / "utils.py"
_PAGE_GLOBALS = globals()
_PAGE_GLOBALS["__file__"] = str(_UTILS_FILE)
exec(_UTILS_FILE.read_text(), _PAGE_GLOBALS)
_PAGE_GLOBALS["__file__"] = str(_PAGE_FILE)


st.set_page_config(
    page_title="Michael Mackin Set Piece | Freekicks",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_app_style()
render_sidebar_menu("Freekicks")


def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])


raw = load_sp_data("Freekicks")
df = filter_by_sp_type(prepare_sp_dataframe(raw, label="Freekicks"), "Freekicks")

hero_block(
    "Dead-ball intelligence",
    "Freekicks",
    "Specialist view for free-kick origins, delivery profiles, takers, shooters, and possession-level shot value.",
)

if df.empty:
    st.warning("No freekick rows were found in Data/SWE SP.xlsx or Data/Czech SP.xlsx.")
    st.stop()

teams = ["All"] + _safe_sorted(df["Team"]) if "Team" in df.columns else ["All"]
periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
shooters = _safe_sorted(df["Shooter"]) if "Shooter" in df.columns else []
heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

team = st.sidebar.selectbox("Team", teams)
period = st.sidebar.selectbox("Game period", periods)
sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], horizontal=False)
minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min()) if "minute" in df.columns else 0
minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max())) if "minute" in df.columns else 95
minute_range = st.sidebar.slider("Minute range", minute_min, minute_max, (minute_min, minute_max))
taker_filter = st.sidebar.multiselect("Initial / sequence taker", takers)
shooter_filter = st.sidebar.multiselect("Shooter", shooters)
height_filter = st.sidebar.multiselect("Pass height", heights)
outcome_filter = st.sidebar.multiselect("Shot outcome", outcomes)

filtered = df.copy()
if team != "All" and "Team" in filtered.columns:
    filtered = filtered[filtered["Team"].eq(team)].copy()
if period != "All" and "game_period" in filtered.columns:
    filtered = filtered[filtered["game_period"].eq(period)].copy()
if sample == "Last 10 games" and "match_rank" in filtered.columns:
    filtered = filtered[filtered["match_rank"] <= 10].copy()
if "minute" in filtered.columns:
    filtered = filtered[pd.to_numeric(filtered["minute"], errors="coerce").between(minute_range[0], minute_range[1])].copy()
if taker_filter and "Taker" in filtered.columns:
    filtered = filtered[filtered["Taker"].isin(taker_filter)].copy()
if shooter_filter and "Shooter" in filtered.columns:
    filtered = filtered[filtered["Shooter"].isin(shooter_filter)].copy()
if height_filter and "Delivery height" in filtered.columns:
    filtered = filtered[filtered["Delivery height"].isin(height_filter)].copy()
if outcome_filter and "Shot outcome" in filtered.columns:
    filtered = filtered[filtered["Shot outcome"].isin(outcome_filter)].copy()

sequences = freekick_sequence_summary(filtered)

st.caption("Source: Data/SWE SP.xlsx and Data/Czech SP.xlsx filtered to From Free Kick. Sequence tables group rows by match_id, possession, and team.")
kpi_row(filtered)

seq_count = int(len(sequences))
avg_actions = float(sequences["Actions"].mean()) if not sequences.empty else 0.0
direct_share = float((sequences["Zone"] == "Direct threat").mean() * 100) if not sequences.empty else 0.0
wide_share = float((sequences["Zone"] == "Wide delivery").mean() * 100) if not sequences.empty else 0.0
best_seq_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("FK sequences", seq_count)
c2.metric("Avg actions", f"{avg_actions:.1f}")
c3.metric("Direct threat share", f"{direct_share:.1f}%")
c4.metric("Best sequence xG", f"{best_seq_xg:.3f}")

overview_tab, origin_tab, people_tab, visuals_tab, data_tab = st.tabs(
    ["Briefing", "Origins", "Roles", "Pitch Evidence", "Event Log"]
)

with overview_tab:
    top_left, top_right = st.columns([0.9, 1.35])
    with top_left:
        section_header("Freekick Brief", "Highest-signal notes")
    with top_right:
        section_header("Origin Map", "Starting points sized by sequence xG")

    insights = generate_set_piece_insights(filtered, "Freekicks")
    if not sequences.empty:
        top_zone = sequences["Zone"].value_counts().head(1)
        top_height = sequences["Initial height"].value_counts().head(1)
        if not top_zone.empty:
            insights.insert(0, f"Most common origin profile is {top_zone.index[0].lower()} ({top_zone.iloc[0]} sequences).")
        if not top_height.empty:
            insights.insert(1, f"Primary initial delivery height is {top_height.index[0]} ({top_height.iloc[0]} sequences).")

    with top_left:
        for insight in insights[:5]:
            st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)
    with top_right:
        st.plotly_chart(
            polish_plotly_figure(freekick_origin_map_figure(filtered)),
            use_container_width=True,
            key="freekicks_overview_origin_map",
        )

    left, right = st.columns([1.1, 1])
    with left:
        section_header("Origin Threat Board", "Sequence value by restart location")
        render_analyst_table(freekick_zone_summary(filtered), height=390)
    with right:
        section_header("Priority Sequences", "Best possession-level freekick outcomes")
        display = sequences[
            [
                "Match", "Team", "Minute", "Zone", "Channel", "Initial taker",
                "Initial height", "Actions", "Shots", "Goals", "Total xG",
                "Best shooter", "Best shot xG", "Shot outcome",
            ]
        ] if not sequences.empty else sequences
        render_analyst_table(display.head(30), height=390)

with origin_tab:
    left, right = st.columns([1.55, 1])
    with left:
        section_header("Origin Map", "Free-kick starting points sized by possession xG")
        st.plotly_chart(
            polish_plotly_figure(freekick_origin_map_figure(filtered)),
            use_container_width=True,
            key="freekicks_origin_tab_origin_map",
        )
    with right:
        section_header("Zone Mix", "Volume by restart territory")
        zone_mix = sequences.groupby("Zone", dropna=False).size().reset_index(name="Sequences") if not sequences.empty else pd.DataFrame()
        if not zone_mix.empty:
            fig = px.bar(zone_mix.sort_values("Sequences", ascending=False), x="Zone", y="Sequences", color="Zone", color_discrete_sequence=["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309"])
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(polish_plotly_figure(fig), use_container_width=True, key="freekicks_origin_zone_mix")
        else:
            st.info("No zone data available.")

        section_header("Channel Mix", "Central vs wide origin balance")
        channel_mix = sequences.groupby("Channel", dropna=False).size().reset_index(name="Sequences") if not sequences.empty else pd.DataFrame()
        if not channel_mix.empty:
            fig = px.bar(channel_mix.sort_values("Sequences", ascending=False), x="Channel", y="Sequences", color="Channel", color_discrete_sequence=["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309"])
            fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(polish_plotly_figure(fig), use_container_width=True, key="freekicks_origin_channel_mix")
        else:
            st.info("No channel data available.")

with people_tab:
    left, right = st.columns(2)
    with left:
        section_header("Taker Roles", "Free-kick sequences started, value created, and preferred zones")
        render_analyst_table(freekick_taker_summary(filtered), height=620)
    with right:
        section_header("Shot Targets", "Shooters receiving or taking the final freekick shot")
        render_analyst_table(freekick_shooter_summary(filtered), height=620)

with visuals_tab:
    left, right = st.columns(2)
    with left:
        section_header("Start Locations", "Where freekick possessions begin")
        st.plotly_chart(
            polish_plotly_figure(starting_location_map_figure(filtered, "Freekick start locations")),
            use_container_width=True,
            key="freekicks_visuals_start_locations",
        )
    with right:
        section_header("Shot Map", "Shot quality generated from freekicks")
        st.plotly_chart(
            polish_plotly_figure(shotmap_figure(filtered, "Freekick shot map")),
            use_container_width=True,
            key="freekicks_visuals_shot_map",
        )

    section_header("Report Shot View", "Static mplsoccer shot-quality figure")
    st.pyplot(mplsoccer_shot_figure(filtered, "Freekicks"), use_container_width=True)

with data_tab:
    section_header("Sequence Log", "One row per match_id + possession + team")
    render_analyst_table(sequences, height=430)
    with st.expander("Event-level rows", expanded=False):
        display_cols = [
            c for c in [
                "Match", "Team", "Taker", "Shooter", "minute", "second", "pass_x", "pass_y",
                "Delivery height", "Shot outcome", "xg", "Occupation_Rating", "Proximity_Rating",
                "Duel_Win_Prob", "OPS_Opponent_Rating", "timestamp",
            ]
            if c in filtered.columns
        ]
        render_analyst_table(filtered[display_cols], height=620)
