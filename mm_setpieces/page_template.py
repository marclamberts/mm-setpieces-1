
from __future__ import annotations
from pathlib import Path
import pandas as pd
import streamlit as st

_TEMPLATE_FILE = Path(__file__).resolve()
_UTILS_FILE = _TEMPLATE_FILE.with_name("utils.py")
_TEMPLATE_GLOBALS = globals()
_TEMPLATE_GLOBALS["__file__"] = str(_UTILS_FILE)
exec(_UTILS_FILE.read_text(), _TEMPLATE_GLOBALS)
_TEMPLATE_GLOBALS["__file__"] = str(_TEMPLATE_FILE)

def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])

@st.cache_data(show_spinner=False)
def _cached_report_pdf(df: pd.DataFrame, label: str, opponent: str) -> bytes:
    return prematch_report_pdf_bytes(df, label, opponent)

def _filter_page_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    teams = ["All"] + _safe_sorted(df["Team"]) if "Team" in df.columns else ["All"]
    leagues = ["All"] + _safe_sorted(df["League"]) if "League" in df.columns else ["All"]
    sides = ["All"] + _safe_sorted(df["side"]) if "side" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    techniques = _safe_sorted(df["Technique"]) if "Technique" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shot_outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    team = st.sidebar.selectbox("Team", teams)
    league = st.sidebar.selectbox("League", leagues)
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], horizontal=False)
    side = st.sidebar.radio("Side", sides, horizontal=False)
    time_in_game = st.sidebar.selectbox("Time in the game", periods)

    minute_min = 0
    minute_max = 95
    if "minute" in df.columns and not df["minute"].dropna().empty:
        minute_values = pd.to_numeric(df["minute"], errors="coerce").dropna()
        if not minute_values.empty:
            minute_min = int(min(0, minute_values.min()))
            minute_max = max(95, int(minute_values.max()))
    minute_range = st.sidebar.slider("Minute range", minute_min, minute_max, (minute_min, minute_max))
    taker_filter = st.sidebar.multiselect("Taker", takers)
    technique_filter = st.sidebar.multiselect("Delivery technique", techniques)
    height_filter = st.sidebar.multiselect("Delivery height", heights)
    shot_outcome_filter = st.sidebar.multiselect("Shot outcome", shot_outcomes)
    only_shots = st.sidebar.checkbox(f"Only {label.lower()} ending with a shot", value=False)

    filtered = df.copy()
    if team != "All" and "Team" in filtered.columns:
        filtered = filtered[filtered["Team"] == team]
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"] == league]
    if sample == "Last 10 games" and "match_rank" in filtered.columns:
        filtered = filtered[filtered["match_rank"] <= 10]
    if side != "All" and "side" in filtered.columns:
        filtered = filtered[filtered["side"] == side]
    if time_in_game != "All" and "game_period" in filtered.columns:
        filtered = filtered[filtered["game_period"] == time_in_game]
    if "minute" in filtered.columns:
        filtered = filtered[pd.to_numeric(filtered["minute"], errors="coerce").between(minute_range[0], minute_range[1])]

    if taker_filter and "Taker" in filtered.columns:
        filtered = filtered[filtered["Taker"].isin(taker_filter)]
    if technique_filter and "Technique" in filtered.columns:
        filtered = filtered[filtered["Technique"].isin(technique_filter)]
    if height_filter and "Delivery height" in filtered.columns:
        filtered = filtered[filtered["Delivery height"].isin(height_filter)]
    if shot_outcome_filter and "Shot outcome" in filtered.columns:
        filtered = filtered[filtered["Shot outcome"].isin(shot_outcome_filter)]
    if only_shots and "is_shot" in filtered.columns:
        filtered = filtered[filtered["is_shot"]]

    return filtered

def render_page(label: str) -> None:
    st.set_page_config(
        page_title=f"Michael Mackin Set Piece | {label}",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_app_style()
    render_sidebar_menu(label)

    raw = load_sp_data(label)
    if raw.empty:
        hero_block(
            "Set piece analysis",
            label,
            "No source rows were found for this page in the bundled workbook(s).",
        )
        return

    df = prepare_sp_dataframe(raw, label=label)
    df = filter_by_sp_type(df, label)
    filtered = _filter_page_data(df, label)
    filtered = filter_by_sp_type(filtered, label)

    hero_block(
        "Set-piece intelligence",
        label,
        "Scout team patterns, taker roles, shot output, and match-level set-piece value from the connected event workbooks.",
    )

    nav_left, nav_mid, nav_right = st.columns([0.9, 1.1, 1.1])
    with nav_left:
        if st.button("Back to Home", use_container_width=True):
            st.switch_page("app.py")
    with nav_mid:
        st.download_button(
            "Export filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name=f"{label.lower().replace(' ', '_')}_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with nav_right:
        st.download_button(
            "Export filtered Excel",
            data=dataframe_to_excel_bytes(filtered, sheet_name=label[:31] or "Data"),
            file_name=f"{label.lower().replace(' ', '_')}_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if label == "Corners":
        st.caption("Corners use Data/Allsvenskan - Corners 2025.xlsx and Data/CZ - Corners 2025-2026.csv.")
    else:
        st.caption(f"{label} use Data/SWE SP.xlsx and Data/Czech SP.xlsx filtered by SP_Type/play pattern.")

    kpi_row(filtered)
    info_panel(filtered)

    overview_tab, visuals_tab, report_tab, data_tab = st.tabs(["Briefing", "Pitch Evidence", "PDF Brief", "Event Log"])

    with overview_tab:
        summary, technique_mix, outcome_mix = build_summary_tables(filtered)

        section_header("Scouting Brief", "Team output, delivery mix, and outcome mix")
        c1, c2, c3 = st.columns([1.35, 1, 1])
        with c1:
            st.markdown('<div class="mm-table-note">Ranked by total xG, goals, and shot volume.</div>', unsafe_allow_html=True)
            render_analyst_table(summary, height=320)
        with c2:
            st.markdown('<div class="mm-table-note">Most common delivery type combinations.</div>', unsafe_allow_html=True)
            render_analyst_table(technique_mix.head(20), height=320)
        with c3:
            st.markdown('<div class="mm-table-note">Delivery and shot result combinations.</div>', unsafe_allow_html=True)
            render_analyst_table(outcome_mix.head(20), height=320)

        section_header("Staff Notes", "Automatic coaching notes from the current filter")
        insights = generate_set_piece_insights(filtered, label)
        insight_cols = st.columns(2)
        for idx, insight in enumerate(insights):
            with insight_cols[idx % 2]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

        section_header("Quick Reads", "Fast visual summaries for the active filter")
        qr1, qr2, qr3 = st.columns(3)
        with qr1:
            st.plotly_chart(
                categorical_breakdown_figure(filtered, "Taker", "Top takers", top_n=8, color="#c1121f"),
                use_container_width=True,
                key=f"{label.lower()}_quick_top_takers",
            )
        with qr2:
            st.plotly_chart(
                categorical_breakdown_figure(filtered, "Shot outcome", "Shot outcomes", top_n=8, color="#1d4ed8"),
                use_container_width=True,
                key=f"{label.lower()}_quick_shot_outcomes",
            )
        with qr3:
            st.plotly_chart(
                minute_distribution_figure(filtered, "Minute distribution"),
                use_container_width=True,
                key=f"{label.lower()}_quick_minute_distribution",
            )

        section_header("Scouting Boards", "Workbook-derived rankings and tactical pattern reads")
        teams_tab, takers_tab, shooters_tab, patterns_tab, matches_tab = st.tabs(
            ["Team Threat", "Takers", "Shot Targets", "Patterns", "Match Log"]
        )
        with teams_tab:
            render_analyst_table(build_team_leaderboard(filtered), height=430)
        with takers_tab:
            render_analyst_table(build_taker_leaderboard(filtered), height=430)
        with shooters_tab:
            render_analyst_table(build_shooter_leaderboard(filtered), height=430)
        with patterns_tab:
            st.markdown(
                '<div class="mm-table-note">Pattern rows combine team, side, technique, height, target zone, and outcome.</div>',
                unsafe_allow_html=True,
            )
            render_analyst_table(build_pattern_library(filtered), height=430)
        with matches_tab:
            render_analyst_table(build_match_log(filtered), height=430)

        section_header("Roles & Archetypes", "Condensed scouting labels for preparation")
        role_left, role_right = st.columns(2)
        with role_left:
            render_analyst_table(build_role_archetypes(filtered, label).head(15), height=360)
        with role_right:
            render_analyst_table(build_team_archetypes(filtered).head(15), height=360)

    with visuals_tab:
        section_header("Interactive Pitch Evidence", "Shot locations and delivery/start locations")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                polish_plotly_figure(shotmap_figure(filtered, f"{label} shotmap · vertical half pitch")),
                use_container_width=True,
                key=f"{label.lower()}_shotmap",
            )
        with right:
            if label == "Corners":
                st.plotly_chart(
                    polish_plotly_figure(delivery_map_figure(filtered, f"{label} delivery map · vertical half pitch")),
                    use_container_width=True,
                    key=f"{label.lower()}_delivery_map",
                )
            else:
                st.plotly_chart(
                    polish_plotly_figure(starting_location_map_figure(filtered, f"{label} starting location map · vertical half pitch")),
                    use_container_width=True,
                    key=f"{label.lower()}_starting_location_map",
                )

        section_header("Static Report Visuals", "Matplotlib / mplsoccer pitch views")
        mpl_left, mpl_right = st.columns(2)
        with mpl_left:
            st.pyplot(mplsoccer_delivery_figure(filtered, label), use_container_width=True)
        with mpl_right:
            st.pyplot(mplsoccer_shot_figure(filtered, label), use_container_width=True)

    with report_tab:
        section_header("Pre-Match PDF", "Download a staff briefing from the current filters")
        report_left, report_right = st.columns([1, 1.2])
        with report_left:
            opponent = st.text_input("Opponent / report label", value="")
            st.caption("The PDF uses the active sidebar filters, role classifications, archetypes, insights, and mplsoccer visuals.")
        with report_right:
            pdf_bytes = _cached_report_pdf(filtered, label, opponent.strip())
            safe_name = (opponent.strip() or label).lower().replace(" ", "_").replace("/", "-")
            st.download_button(
                "Download pre-match PDF",
                data=pdf_bytes,
                file_name=f"{safe_name}_set_piece_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    with data_tab:
        section_header("Event Log", f"{len(filtered):,} workbook rows in the current filter")
        display_cols = [c for c in [
            "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
            "Defensive_setup", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob",
            "OPS_Opponent_Rating", "timestamp"
        ] if c in filtered.columns]
        with st.expander("Event-level rows", expanded=True):
            render_analyst_table(filtered[display_cols], height=620)
