"""Match Prep section — full pre-match brief for a selected fixture."""
from __future__ import annotations

import streamlit as st
import pandas as pd

from mm_setpieces_1.utils import (
    DATA_VERSION,
    load_prepared_sp_data,
    load_prepared_freekick_brief_data,
    render_analyst_table,
    hero_block,
    section_header,
    kpi_row,
    render_export_controls,
    generate_set_piece_insights,
    polish_plotly_figure,
    set_piece_kpi_values,
    build_taker_leaderboard,
    build_shooter_leaderboard,
    build_pattern_library,
    freekick_sequence_summary,
    freekick_zone_summary,
    freekick_taker_summary,
    throwin_sequence_summary,
    throwin_zone_summary,
    throwin_taker_summary,
    mplsoccer_delivery_figure,
    mplsoccer_shot_figure,
    freekick_origin_map_figure,
    throwin_delivery_map_figure,
    shotmap_figure,
    starting_location_map_figure,
    prematch_report_pdf_bytes,
)

from sections._shared import (
    _safe_sorted,
    _fmt_num,
    _set_piece_team_options,
    _apply_team_perspective,
    _with_match_names,
    load_hops_data,
    bar_chart,
    histogram_chart,
    render_plotly_visual,
    render_mpl_visual,
    _cached_report_pdf,
)


# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _all_sp_data(_data_version: str = DATA_VERSION):
    corners = _with_match_names(load_prepared_sp_data("Corners", _data_version))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_data_version))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _data_version))
    hops = load_hops_data(_data_version)
    return corners, freekicks, throwins, hops


# ── Helpers ──────────────────────────────────────────────────────────────────

def _team_filter(df: pd.DataFrame, team: str) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns or not team:
        return df
    return df[df["Team"].astype(str).eq(team)].copy()


def _all_teams(corners, freekicks, throwins) -> list[str]:
    teams: set[str] = set()
    for df in [corners, freekicks, throwins]:
        if "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    return sorted(t for t in teams if t.strip())


def _kpi_strip(df: pd.DataFrame) -> None:
    kpi = set_piece_kpi_values(df)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Set pieces", f"{kpi['restarts']:,}")
    c2.metric("Shots", f"{kpi['shots']:,}")
    c3.metric("Goals", f"{kpi['goals']:,}")
    c4.metric("xG", f"{kpi['total_xg']:.2f}")
    c5.metric("Shot rate %", f"{kpi['shot_rate']:.1f}")
    c6.metric("xG / 100", f"{kpi['xg_per_100']:.2f}")


def _phase_brief(label: str, df: pd.DataFrame, show_pitch: bool = True) -> None:
    """Compact brief for one set-piece phase."""
    if df.empty:
        st.info(f"No {label} data for this team.")
        return

    section_header(label)
    _kpi_strip(df)

    insights = generate_set_piece_insights(df, label)
    if insights:
        ins_cols = st.columns(min(3, len(insights[:3])))
        for i, insight in enumerate(insights[:3]):
            with ins_cols[i]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

    if show_pitch:
        pc1, pc2 = st.columns(2)
        with pc1:
            if label == "Corners":
                render_mpl_visual(mplsoccer_delivery_figure(df, label), f"{label} delivery", f"mp_{label.lower()}_delivery")
            elif label == "Freekicks":
                render_mpl_visual(freekick_origin_map_figure(df), f"{label} origins", f"mp_{label.lower()}_origin")
            elif label == "Throw-ins":
                render_mpl_visual(throwin_delivery_map_figure(df), f"{label} deliveries", f"mp_{label.lower()}_delivery")
        with pc2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(df, f"{label} shots")),
                f"{label} shots", f"mp_{label.lower()}_shots",
            )

    if label == "Corners":
        role_l, role_r = st.columns(2)
        with role_l:
            st.caption("Top takers")
            render_analyst_table(build_taker_leaderboard(df).head(8), height=260)
        with role_r:
            st.caption("Top shooters")
            render_analyst_table(build_shooter_leaderboard(df).head(8), height=260)
        st.caption("Top patterns")
        render_analyst_table(build_pattern_library(df).head(10), height=260)

    elif label == "Freekicks":
        seqs = freekick_sequence_summary(df)
        zone_l, zone_r = st.columns(2)
        with zone_l:
            st.caption("Zone breakdown")
            render_analyst_table(freekick_zone_summary(df).head(8), height=260)
        with zone_r:
            st.caption("Priority sequences")
            cols = ["Zone", "Channel", "Actions", "Shots", "Goals", "Total xG", "Shot outcome"]
            render_analyst_table(seqs[[c for c in cols if c in seqs.columns]].head(8), height=260)
        st.caption("Takers")
        render_analyst_table(freekick_taker_summary(df).head(8), height=260)

    elif label == "Throw-ins":
        seqs = throwin_sequence_summary(df)
        zone_l, zone_r = st.columns(2)
        with zone_l:
            st.caption("Zone breakdown")
            render_analyst_table(throwin_zone_summary(df).head(8), height=260)
        with zone_r:
            st.caption("Priority sequences")
            cols = ["Zone", "Side", "Box entry", "Shots", "Goals", "Total xG", "Shot outcome"]
            render_analyst_table(seqs[[c for c in cols if c in seqs.columns]].head(8), height=260)
        st.caption("Throwers")
        render_analyst_table(throwin_taker_summary(df).head(8), height=260)


def _hops_brief(team: str, hops: pd.DataFrame) -> None:
    section_header("HOPS profiles", "Heading and duel ratings for this squad")
    team_hops = hops[hops["Team"].astype(str).eq(team)].sort_values("Rating", ascending=False) if not hops.empty and "Team" in hops.columns else pd.DataFrame()
    if team_hops.empty:
        st.info("No HOPS data for this team.")
        return
    avg = float(team_hops["Rating"].mean())
    best = float(team_hops["Rating"].max())
    elite = int((team_hops["Tier"] == "Elite").sum()) if "Tier" in team_hops.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Players rated", len(team_hops))
    c2.metric("Avg rating", f"{avg:.3f}")
    c3.metric("Elite profiles", elite)
    render_analyst_table(team_hops[["Player", "Rating", "Percentile", "Tier"]].head(20), height=380)


# ── Main render ──────────────────────────────────────────────────────────────

def render_match_prep() -> None:
    hero_block(
        "Match Prep",
        "Pre-match brief",
        "Select your team and the opponent. Get attacking and defensive set-piece profiles, key personnel, and a PDF export.",
    )

    corners, freekicks, throwins, hops = _all_sp_data(DATA_VERSION)
    teams = _all_teams(corners, freekicks, throwins)
    if not teams:
        st.warning("No team data found. Check that the SP data files are loaded correctly.")
        return

    # ── Team selectors ──────────────────────────────────────────────────────
    col_my, col_opp = st.columns(2)
    my_team = col_my.selectbox("Your team", teams, key="mp_my_team")
    opp_options = [t for t in teams if t != my_team]
    opponent = col_opp.selectbox("Opponent", opp_options, key="mp_opponent") if opp_options else None

    if not opponent:
        st.info("Add more teams to compare.")
        return

    st.markdown(
        f"<div class='mm-hero' style='padding:1rem 1.4rem;margin-bottom:.8rem'>"
        f"<div class='mm-eyebrow'>Match prep</div>"
        f"<div class='mm-title' style='font-size:1.5rem'>{my_team} <span style='opacity:.55'>vs</span> {opponent}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Data subsets ─────────────────────────────────────────────────────────
    my_corners = _team_filter(corners, my_team)
    my_fks = _team_filter(freekicks, my_team)
    my_tis = _team_filter(throwins, my_team)

    opp_corners = _team_filter(corners, opponent)
    opp_fks = _team_filter(freekicks, opponent)
    opp_tis = _team_filter(throwins, opponent)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_attack, tab_defend, tab_personnel, tab_export = st.tabs([
        "⚔️ Our attack", f"🛡️ Their attack ({opponent})", "👤 Personnel", "📋 Export"
    ])

    # ── Our attack ───────────────────────────────────────────────────────────
    with tab_attack:
        section_header(f"{my_team} — attacking set pieces", "What we do when we win a set piece")

        total_kpi = set_piece_kpi_values(pd.concat([my_corners, my_fks, my_tis], ignore_index=True))
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total set pieces", f"{total_kpi['restarts']:,}")
        c2.metric("Shots", f"{total_kpi['shots']:,}")
        c3.metric("Goals", f"{total_kpi['goals']:,}")
        c4.metric("Total xG", f"{total_kpi['total_xg']:.2f}")
        c5.metric("xG / 100", f"{total_kpi['xg_per_100']:.2f}")

        st.divider()
        _phase_brief("Corners", my_corners)
        st.divider()
        _phase_brief("Freekicks", my_fks)
        st.divider()
        _phase_brief("Throw-ins", my_tis)

    # ── Opponent attack ───────────────────────────────────────────────────────
    with tab_defend:
        section_header(f"{opponent} — attacking set pieces", "What they do — what we need to defend")

        opp_total = set_piece_kpi_values(pd.concat([opp_corners, opp_fks, opp_tis], ignore_index=True))
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total set pieces", f"{opp_total['restarts']:,}")
        c2.metric("Shots", f"{opp_total['shots']:,}")
        c3.metric("Goals", f"{opp_total['goals']:,}")
        c4.metric("Total xG", f"{opp_total['total_xg']:.2f}")
        c5.metric("xG / 100", f"{opp_total['xg_per_100']:.2f}")

        st.divider()
        _phase_brief("Corners", opp_corners)
        st.divider()
        _phase_brief("Freekicks", opp_fks)
        st.divider()
        _phase_brief("Throw-ins", opp_tis)

    # ── Personnel ─────────────────────────────────────────────────────────────
    with tab_personnel:
        my_col, opp_col = st.columns(2)
        with my_col:
            section_header(f"{my_team}", "Our key players")
            _hops_brief(my_team, hops)
            st.divider()
            section_header("Our corner takers")
            render_analyst_table(build_taker_leaderboard(my_corners).head(10), height=280)
            section_header("Our FK takers")
            render_analyst_table(freekick_taker_summary(my_fks).head(10), height=280)

        with opp_col:
            section_header(f"{opponent}", "Their key players to watch")
            _hops_brief(opponent, hops)
            st.divider()
            section_header("Their corner takers")
            render_analyst_table(build_taker_leaderboard(opp_corners).head(10), height=280)
            section_header("Their FK takers")
            render_analyst_table(freekick_taker_summary(opp_fks).head(10), height=280)

    # ── Export ────────────────────────────────────────────────────────────────
    with tab_export:
        section_header("Download PDF brief")
        st.markdown(
            "The PDF report covers the **selected team's** attacking set pieces — corners, free kicks, and throw-ins — "
            "plus a personnel summary. Generate one for each team to get a complete brief."
        )

        report_for = st.radio("Generate report for", [my_team, opponent], horizontal=True, key="mp_pdf_team")
        if report_for == my_team:
            pdf_corners = my_corners
            pdf_fks = my_fks
        else:
            pdf_corners = opp_corners
            pdf_fks = opp_fks

        pdf_data = pd.concat([pdf_corners, pdf_fks], ignore_index=True)

        extra_label = st.text_input("Additional label / notes for filename", value="", key="mp_pdf_label")
        safe_name = f"{report_for.lower().replace(' ', '_')}_vs_{opponent.lower().replace(' ', '_')}"
        if extra_label.strip():
            safe_name += f"_{extra_label.strip().lower().replace(' ', '_')}"

        st.info("PDF generation may take a few seconds on large datasets.")
        st.download_button(
            f"⬇ Download {report_for} pre-match PDF",
            data=_cached_report_pdf(pdf_data, f"Match Prep — {report_for}", opponent if report_for == my_team else my_team),
            file_name=f"{safe_name}_match_prep.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.divider()
        section_header("Export raw data")
        export_choice = st.selectbox("Dataset", [
            f"{my_team} corners", f"{my_team} freekicks", f"{my_team} throw-ins",
            f"{opponent} corners", f"{opponent} freekicks", f"{opponent} throw-ins",
        ], key="mp_export_choice")
        export_map = {
            f"{my_team} corners": my_corners, f"{my_team} freekicks": my_fks, f"{my_team} throw-ins": my_tis,
            f"{opponent} corners": opp_corners, f"{opponent} freekicks": opp_fks, f"{opponent} throw-ins": opp_tis,
        }
        render_export_controls(export_map[export_choice], "match_prep", export_choice)
