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


def _phase_brief(label: str, df: pd.DataFrame, show_pitch: bool = True, slug: str = "my") -> None:
    """Compact brief for one set-piece phase. slug disambiguates widget keys between team/opponent."""
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

    key_prefix = f"mp_{slug}_{label.lower()}"
    if show_pitch:
        pc1, pc2 = st.columns(2)
        with pc1:
            if label == "Corners":
                render_mpl_visual(mplsoccer_delivery_figure(df, label), f"{label} delivery", f"{key_prefix}_delivery")
            elif label == "Freekicks":
                render_mpl_visual(freekick_origin_map_figure(df), f"{label} origins", f"{key_prefix}_origin")
            elif label == "Throw-ins":
                render_mpl_visual(throwin_delivery_map_figure(df), f"{label} deliveries", f"{key_prefix}_delivery")
        with pc2:
            render_plotly_visual(
                polish_plotly_figure(shotmap_figure(df, f"{label} shots")),
                f"{label} shots", f"{key_prefix}_shots",
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


def _threat_score(kpi: dict, all_xg_per_100: float) -> float:
    """Normalise xG/100 against dataset average. 100 = average, >100 = above average."""
    base = kpi["xg_per_100"]
    if all_xg_per_100 <= 0:
        return 50.0
    return min(200.0, round(base / all_xg_per_100 * 100, 1))


def _score_badge(score: float) -> str:
    if score >= 140:
        return f"<span style='color:#ef4444;font-weight:800'>{score:.0f}</span> <span style='color:#ef4444;font-size:.72rem'>HIGH THREAT</span>"
    if score >= 100:
        return f"<span style='color:#f59e0b;font-weight:800'>{score:.0f}</span> <span style='color:#f59e0b;font-size:.72rem'>ABOVE AVERAGE</span>"
    if score >= 60:
        return f"<span style='color:#9ca3af;font-weight:800'>{score:.0f}</span> <span style='color:#9ca3af;font-size:.72rem'>AVERAGE</span>"
    return f"<span style='color:#22c55e;font-weight:800'>{score:.0f}</span> <span style='color:#22c55e;font-size:.72rem'>LOW THREAT</span>"


def _alert_bullets(team: str, kpi: dict, hops_df: pd.DataFrame,
                   corners_df: pd.DataFrame, fks_df: pd.DataFrame) -> list[str]:
    alerts: list[str] = []

    # Aerial threats from HOPS
    if not hops_df.empty and "Player" in hops_df.columns:
        elite = hops_df[hops_df.get("Tier", pd.Series(dtype=str)).astype(str).eq("Elite")] if "Tier" in hops_df.columns else hops_df.nlargest(3, "Rating")
        if elite.empty:
            elite = hops_df.nlargest(3, "Rating")
        for _, row in elite.head(3).iterrows():
            alerts.append(
                f"⚠️ <strong>{row['Player']}</strong> — elite aerial threat "
                f"(HOPS {row['Rating']:.3f}, {row.get('Percentile', 0):.0f}th percentile). Mark at every corner."
            )

    # Corner delivery bias
    if not corners_df.empty and "Delivery height" in corners_df.columns:
        top_del = corners_df["Delivery height"].value_counts()
        if not top_del.empty:
            pct = top_del.iloc[0] / len(corners_df) * 100
            if pct >= 55:
                alerts.append(
                    f"📌 <strong>{pct:.0f}% of corners</strong> are delivered as "
                    f"<strong>{top_del.index[0].lower()}</strong> balls — set defensive shape accordingly."
                )

    # Corner side bias
    if not corners_df.empty and "side" in corners_df.columns:
        side_counts = corners_df["side"].value_counts()
        if not side_counts.empty and side_counts.iloc[0] / len(corners_df) >= 0.60:
            alerts.append(
                f"📌 <strong>{side_counts.iloc[0] / len(corners_df) * 100:.0f}% of corners</strong> come from the "
                f"<strong>{side_counts.index[0]}</strong> — overload that side."
            )

    # FK threat zone
    if not fks_df.empty and "Zone" in fks_df.columns:
        fk_zone = fks_df["Zone"].value_counts()
        if not fk_zone.empty:
            alerts.append(
                f"🎯 Main FK threat zone: <strong>{fk_zone.index[0]}</strong> "
                f"({fk_zone.iloc[0] / len(fks_df) * 100:.0f}% of free kicks)."
            )

    # Shot rate warning
    if kpi["shot_rate"] >= 20:
        alerts.append(
            f"🔴 High shot rate — <strong>{kpi['shot_rate']:.1f}%</strong> of their set pieces generate a shot "
            f"(dataset average ~12%). Disciplined defensive structure essential."
        )
    elif kpi["shot_rate"] >= 14:
        alerts.append(
            f"🟡 Above-average shot rate — <strong>{kpi['shot_rate']:.1f}%</strong> from set pieces."
        )

    # Top corner taker
    if kpi["top_taker"] not in {"Unknown", ""}:
        alerts.append(
            f"👟 Primary corner taker: <strong>{kpi['top_taker']}</strong>. "
            "Track position after the team wins a corner."
        )

    return alerts[:6]


def _render_overview(my_team: str, opponent: str,
                     my_corners, my_fks, my_tis,
                     opp_corners, opp_fks, opp_tis,
                     all_corners, all_fks, all_tis,
                     hops: pd.DataFrame) -> None:
    # Dataset average xG/100 for normalisation
    all_sp = pd.concat([all_corners, all_fks, all_tis], ignore_index=True)
    all_kpi = set_piece_kpi_values(all_sp)
    avg_xg_100 = float(all_kpi["xg_per_100"]) if all_kpi["xg_per_100"] else 1.0

    my_sp  = pd.concat([my_corners,  my_fks,  my_tis],  ignore_index=True)
    opp_sp = pd.concat([opp_corners, opp_fks, opp_tis], ignore_index=True)
    my_kpi  = set_piece_kpi_values(my_sp)
    opp_kpi = set_piece_kpi_values(opp_sp)

    my_score  = _threat_score(my_kpi,  avg_xg_100)
    opp_score = _threat_score(opp_kpi, avg_xg_100)

    opp_hops = hops[hops["Team"].astype(str).eq(opponent)].sort_values("Rating", ascending=False) if not hops.empty and "Team" in hops.columns else pd.DataFrame()

    # ── Threat duel banner ────────────────────────────────────────────
    section_header("Set-piece threat index", "xG per 100 set pieces, normalised — 100 = dataset average")
    left, mid, right = st.columns([5, 2, 5])
    with left:
        st.markdown(
            f"""<div style="background:#161922;border:1px solid rgba(255,255,255,0.08);
                border-top:2px solid #22c55e;border-radius:6px;padding:.9rem 1rem;text-align:center">
                <div style="color:#6b7280;font-size:.6rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:.13em;margin-bottom:.3rem">Our attacking threat</div>
                <div style="font-size:2.4rem;font-weight:900;color:#fff;letter-spacing:-.04em;line-height:1">
                    {_score_badge(my_score)}</div>
                <div style="color:#9ca3af;font-size:.75rem;margin-top:.4rem">
                    {my_kpi['restarts']:,} set pieces · {my_kpi['shots']} shots · {my_kpi['total_xg']:.2f} xG
                </div></div>""",
            unsafe_allow_html=True,
        )
    with mid:
        st.markdown(
            "<div style='text-align:center;padding-top:1.8rem;color:#4b5563;font-size:1.1rem;font-weight:700'>vs</div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""<div style="background:#161922;border:1px solid rgba(255,255,255,0.08);
                border-top:2px solid #ef4444;border-radius:6px;padding:.9rem 1rem;text-align:center">
                <div style="color:#6b7280;font-size:.6rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:.13em;margin-bottom:.3rem">Their attacking threat</div>
                <div style="font-size:2.4rem;font-weight:900;color:#fff;letter-spacing:-.04em;line-height:1">
                    {_score_badge(opp_score)}</div>
                <div style="color:#9ca3af;font-size:.75rem;margin-top:.4rem">
                    {opp_kpi['restarts']:,} set pieces · {opp_kpi['shots']} shots · {opp_kpi['total_xg']:.2f} xG
                </div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Side-by-side KPI comparison ───────────────────────────────────
    section_header("Head-to-head set-piece stats")
    metrics = [
        ("Set pieces", f"{my_kpi['restarts']:,}", f"{opp_kpi['restarts']:,}"),
        ("Shots", f"{my_kpi['shots']:,}", f"{opp_kpi['shots']:,}"),
        ("Goals", f"{my_kpi['goals']:,}", f"{opp_kpi['goals']:,}"),
        ("xG total", f"{my_kpi['total_xg']:.2f}", f"{opp_kpi['total_xg']:.2f}"),
        ("Shot rate %", f"{my_kpi['shot_rate']:.1f}", f"{opp_kpi['shot_rate']:.1f}"),
        ("xG / 100", f"{my_kpi['xg_per_100']:.2f}", f"{opp_kpi['xg_per_100']:.2f}"),
    ]
    hdr, col_my, col_opp = st.columns([2, 1, 1])
    hdr.markdown(f"<span style='color:#6b7280;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em'>Metric</span>", unsafe_allow_html=True)
    col_my.markdown(f"<span style='color:#22c55e;font-size:.68rem;font-weight:700'>{my_team}</span>", unsafe_allow_html=True)
    col_opp.markdown(f"<span style='color:#ef4444;font-size:.68rem;font-weight:700'>{opponent}</span>", unsafe_allow_html=True)
    for label, my_val, opp_val in metrics:
        try:
            my_f  = float(my_val.replace(",", "").replace("%", ""))
            opp_f = float(opp_val.replace(",", "").replace("%", ""))
            my_bold  = "font-weight:700;color:#fff" if my_f >= opp_f else "color:#9ca3af"
            opp_bold = "font-weight:700;color:#fff" if opp_f >= my_f else "color:#9ca3af"
        except Exception:
            my_bold = opp_bold = "color:#9ca3af"
        r, c1, c2 = st.columns([2, 1, 1])
        r.markdown(f"<span style='color:#6b7280;font-size:.82rem'>{label}</span>", unsafe_allow_html=True)
        c1.markdown(f"<span style='{my_bold};font-size:.88rem'>{my_val}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span style='{opp_bold};font-size:.88rem'>{opp_val}</span>", unsafe_allow_html=True)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # ── Opponent alerts ───────────────────────────────────────────────
    section_header(f"Scouting alerts — {opponent}", "Auto-generated from their set-piece data")
    alerts = _alert_bullets(opponent, opp_kpi, opp_hops, opp_corners, opp_fks)
    if alerts:
        for alert in alerts:
            st.markdown(
                f"<div class='mm-insight-card' style='margin-bottom:.4rem'>{alert}</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Not enough opponent data to generate alerts.")

    # ── Top aerial threats watchlist ──────────────────────────────────
    if not opp_hops.empty:
        section_header(f"Aerial threat watchlist — {opponent}", "Players to mark at corners and free kicks")
        top_threats = opp_hops.head(8)[["Player", "Rating", "Percentile", "Tier"]].copy()
        render_analyst_table(top_threats, height=260)


# ── Main render ──────────────────────────────────────────────────────────────

def render_match_prep() -> None:
    corners, freekicks, throwins, hops = _all_sp_data(DATA_VERSION)
    teams = _all_teams(corners, freekicks, throwins)
    if not teams:
        st.warning("No team data found. Check that the SP data files are loaded correctly.")
        return

    # ── Team selectors ──────────────────────────────────────────────────────
    st.markdown('<div class="mm-filter-panel"><div class="mm-filter-panel-label">Select teams</div>', unsafe_allow_html=True)
    col_my, col_opp = st.columns(2)
    my_team = col_my.selectbox("Your team", teams, key="mp_my_team")
    opp_options = [t for t in teams if t != my_team]
    opponent = col_opp.selectbox("Opponent", opp_options, key="mp_opponent") if opp_options else None
    st.markdown('</div>', unsafe_allow_html=True)

    if not opponent:
        st.info("Add more teams to compare.")
        return

    hero_block("Match Prep", f"{my_team} vs {opponent}", "Attacking and defensive set-piece profiles, key personnel, tactical patterns, and PDF export.")

    # ── Data subsets ─────────────────────────────────────────────────────────
    my_corners = _team_filter(corners, my_team)
    my_fks = _team_filter(freekicks, my_team)
    my_tis = _team_filter(throwins, my_team)

    opp_corners = _team_filter(corners, opponent)
    opp_fks = _team_filter(freekicks, opponent)
    opp_tis = _team_filter(throwins, opponent)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_overview, tab_attack, tab_defend, tab_personnel, tab_export = st.tabs([
        "🎯 Overview", "⚔️ Our attack", f"🛡️ Their attack ({opponent})", "👤 Personnel", "📋 Export"
    ])

    # ── Overview ──────────────────────────────────────────────────────────────
    with tab_overview:
        _render_overview(my_team, opponent,
                         my_corners, my_fks, my_tis,
                         opp_corners, opp_fks, opp_tis,
                         corners, freekicks, throwins, hops)

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
        _phase_brief("Corners", my_corners, slug="my")
        st.divider()
        _phase_brief("Freekicks", my_fks, slug="my")
        st.divider()
        _phase_brief("Throw-ins", my_tis, slug="my")

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
        _phase_brief("Corners", opp_corners, slug="opp")
        st.divider()
        _phase_brief("Freekicks", opp_fks, slug="opp")
        st.divider()
        _phase_brief("Throw-ins", opp_tis, slug="opp")

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
