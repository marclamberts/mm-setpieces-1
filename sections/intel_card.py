"""Opposition Intelligence Card — pre-match brief generator."""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mm_setpieces_1.utils import (
    DATA_VERSION,
    hero_block,
    load_prepared_freekick_brief_data,
    load_prepared_sp_data,
    polish_plotly_figure,
    render_analyst_table,
    section_header,
)
from sections._shared import (
    _apply_team_perspective,
    _safe_sorted,
    _with_match_names,
    load_hops_data,
    render_plotly_visual,
)

_CODE_V = "intel_card_v1"

OUTCOME_COLOURS = {
    "Goal": "#ef4444",
    "Saved": "#f59e0b",
    "Off T": "#94a3b8",
    "Blocked": "#94a3b8",
    "Wayward": "#94a3b8",
    "Post": "#94a3b8",
    "No shot": "#334155",
}


@st.cache_data(show_spinner="Loading data…")
def _load(_dv: str = DATA_VERSION, _cv: str = _CODE_V):
    corners = _with_match_names(load_prepared_sp_data("Corners", _dv))
    freekicks = _with_match_names(load_prepared_freekick_brief_data(_dv))
    throwins = _with_match_names(load_prepared_sp_data("Throw ins", _dv))
    hops = load_hops_data(_dv)
    return corners, freekicks, throwins, hops


def _all_teams(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame) -> list[str]:
    teams: set[str] = set()
    for df in [corners, freekicks, throwins]:
        if "Team" in df.columns:
            teams.update(df["Team"].dropna().astype(str).unique())
    return sorted(t for t in teams if t.strip())


def _team_sp(df: pd.DataFrame, team: str) -> pd.DataFrame:
    if df.empty or "Team" not in df.columns:
        return pd.DataFrame()
    return df[df["Team"].astype(str).eq(team)].copy()


def _sp_kpis(df: pd.DataFrame) -> dict:
    n = max(len(df), 1)
    shots = int(df["is_shot"].sum()) if "is_shot" in df.columns else 0
    goals = int(df["is_goal"].sum()) if "is_goal" in df.columns else 0
    xg = float(df["xg"].fillna(0).sum()) if "xg" in df.columns else 0.0
    return {
        "deliveries": len(df),
        "shots": shots,
        "goals": goals,
        "xg": round(xg, 2),
        "xg_per_100": round(xg / n * 100, 2),
        "shot_rate": round(shots / n * 100, 2),
    }


def _top_takers(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    if df.empty or "Taker" not in df.columns:
        return pd.DataFrame()
    grp = df.groupby("Taker", dropna=False).agg(
        Deliveries=("Taker", "count"),
        xG=("xg", "sum") if "xg" in df.columns else ("Taker", "count"),
    ).reset_index()
    grp["xG/100"] = (grp["xG"] / grp["Deliveries"].clip(lower=1) * 100).round(2)
    return grp.sort_values("Deliveries", ascending=False).head(n)


def _top_hops(hops: pd.DataFrame, team: str, n: int = 3) -> pd.DataFrame:
    if hops.empty or "Team" not in hops.columns:
        return pd.DataFrame()
    sub = hops[hops["Team"].astype(str).eq(team)].sort_values("Rating", ascending=False)
    return sub[["Player", "Rating", "Percentile", "Tier"]].head(n)


def _corner_preferences(corners: pd.DataFrame, team: str) -> dict:
    sub = _team_sp(corners, team)
    if sub.empty:
        return {}
    result: dict[str, object] = {}
    if "Technique" in sub.columns:
        vc = sub["Technique"].value_counts()
        result["top_technique"] = vc.index[0] if not vc.empty else "Unknown"
        result["technique_pct"] = round(vc.iloc[0] / len(sub) * 100, 1) if not vc.empty else 0.0
    if "side" in sub.columns:
        sc = sub["side"].value_counts()
        result["top_side"] = sc.index[0] if not sc.empty else "Unknown"
        result["side_pct"] = round(sc.iloc[0] / len(sub) * 100, 1) if not sc.empty else 0.0
    if "Delivery height" in sub.columns:
        hc = sub["Delivery height"].value_counts()
        result["top_height"] = hc.index[0] if not hc.empty else "Unknown"
    return result


def _defensive_vulnerability(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, team: str) -> dict:
    worst_type = "None"
    worst_xg100 = 0.0
    for label, df in [("Corners", corners), ("FKs", freekicks), ("Throw-ins", throwins)]:
        sub = _apply_team_perspective(df, team, "Against")
        if sub.empty:
            continue
        n = max(len(sub), 1)
        xg = float(sub["xg"].fillna(0).sum()) if "xg" in sub.columns else 0.0
        x100 = xg / n * 100
        if x100 > worst_xg100:
            worst_xg100 = x100
            worst_type = label
    return {"worst_type": worst_type, "worst_xg100": round(worst_xg100, 2)}


def _recent_form(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, team: str, n: int = 5) -> pd.DataFrame:
    frames = []
    for df in [corners, freekicks, throwins]:
        sub = _team_sp(df, team)
        if not sub.empty and "match_rank" in sub.columns:
            frames.append(sub)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "match_rank" not in combined.columns:
        return pd.DataFrame()
    top_ranks = sorted(combined["match_rank"].dropna().unique(), reverse=True)[:n]
    rows = []
    for rank in sorted(top_ranks):
        part = combined[combined["match_rank"] == rank]
        match_name = part["Match"].iloc[0] if "Match" in part.columns and not part.empty else str(rank)
        xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0
        rows.append({"Match": match_name, "xG from SP": round(xg, 2), "Shots": shots, "Goals": goals})
    return pd.DataFrame(rows)


def _team_tier(hops: pd.DataFrame, team: str) -> str:
    if hops.empty or "Team" not in hops.columns:
        return "Unknown"
    sub = hops[hops["Team"].astype(str).eq(team)]
    if sub.empty or "Percentile" not in sub.columns:
        return "Unknown"
    avg_pct = float(sub["Percentile"].mean())
    if avg_pct >= 80:
        return "Elite"
    if avg_pct >= 65:
        return "Strong"
    if avg_pct >= 50:
        return "Average"
    if avg_pct >= 35:
        return "Developing"
    return "Weak"


TIER_COLOURS = {
    "Elite": "#ef4444",
    "Strong": "#f59e0b",
    "Average": "#3b82f6",
    "Developing": "#94a3b8",
    "Weak": "#64748b",
    "Unknown": "#334155",
}


def _tier_badge(tier: str) -> str:
    colour = TIER_COLOURS.get(tier, "#334155")
    return (
        f"<span style='background:{colour};color:#fff;padding:.2rem .6rem;"
        f"border-radius:4px;font-size:.75rem;font-weight:700;letter-spacing:.06em'>{tier}</span>"
    )


# ---------------------------------------------------------------------------
# PDF generation (matplotlib-based, simple)
# ---------------------------------------------------------------------------

def _generate_pdf(
    opponent: str,
    tier: str,
    kpis_corner: dict,
    kpis_fk: dict,
    kpis_ti: dict,
    takers_df: pd.DataFrame,
    hops_df: pd.DataFrame,
    preferences: dict,
    vulnerability: dict,
    recent: pd.DataFrame,
) -> bytes:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
    except ImportError:
        return b""

    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        ax.text(0.5, 0.88, "Opposition Intelligence Card", ha="center", va="center",
                fontsize=22, fontweight="bold", color="#111827",
                transform=ax.transAxes)
        ax.text(0.5, 0.80, opponent, ha="center", va="center",
                fontsize=32, fontweight="bold", color="#1d4ed8",
                transform=ax.transAxes)
        ax.text(0.5, 0.73, f"Tier: {tier}", ha="center", va="center",
                fontsize=14, color=TIER_COLOURS.get(tier, "#334155"),
                transform=ax.transAxes)
        ax.text(0.5, 0.67, f"Generated: {date.today().strftime('%d %b %Y')}", ha="center", va="center",
                fontsize=11, color="#6b7280", transform=ax.transAxes)

        lines = [
            f"Corners — xG/100: {kpis_corner['xg_per_100']:.2f}  |  Shot rate: {kpis_corner['shot_rate']:.1f}%  |  xG: {kpis_corner['xg']:.2f}",
            f"Free Kicks — xG/100: {kpis_fk['xg_per_100']:.2f}  |  Shot rate: {kpis_fk['shot_rate']:.1f}%  |  xG: {kpis_fk['xg']:.2f}",
            f"Throw-ins — xG/100: {kpis_ti['xg_per_100']:.2f}  |  Shot rate: {kpis_ti['shot_rate']:.1f}%  |  xG: {kpis_ti['xg']:.2f}",
        ]
        for i, line in enumerate(lines):
            ax.text(0.5, 0.56 - i * 0.06, line, ha="center", va="center",
                    fontsize=10, color="#374151", transform=ax.transAxes)

        if preferences:
            pref_lines = []
            if "top_technique" in preferences:
                pref_lines.append(f"Main corner technique: {preferences['top_technique']} ({preferences.get('technique_pct', 0):.0f}%)")
            if "top_side" in preferences:
                pref_lines.append(f"Preferred side: {preferences['top_side']} ({preferences.get('side_pct', 0):.0f}%)")
            if "top_height" in preferences:
                pref_lines.append(f"Most common height: {preferences['top_height']}")
            ax.text(0.5, 0.36, "Corner Preferences", ha="center", fontsize=12, fontweight="bold",
                    color="#111827", transform=ax.transAxes)
            for i, line in enumerate(pref_lines):
                ax.text(0.5, 0.30 - i * 0.05, line, ha="center", fontsize=10,
                        color="#374151", transform=ax.transAxes)

        ax.text(0.5, 0.14, f"Defensive vulnerability: most exposed to {vulnerability.get('worst_type', 'N/A')} "
                f"({vulnerability.get('worst_xg100', 0):.2f} xG/100 conceded)",
                ha="center", fontsize=10, color="#ef4444", transform=ax.transAxes)

        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # Attack summary bar chart page
        fig2, ax2 = plt.subplots(figsize=(8.5, 5))
        types = ["Corners", "Free Kicks", "Throw-ins"]
        xg_100s = [kpis_corner["xg_per_100"], kpis_fk["xg_per_100"], kpis_ti["xg_per_100"]]
        colours = ["#3b82f6", "#22c55e", "#f59e0b"]
        bars = ax2.bar(types, xg_100s, color=colours, width=0.5)
        for bar, val in zip(bars, xg_100s):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                     f"{val:.2f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
        ax2.set_title(f"{opponent} — xG / 100 by Set Piece Type", fontsize=14, fontweight="bold")
        ax2.set_ylabel("xG / 100 deliveries")
        ax2.set_ylim(0, max(xg_100s + [1.0]) * 1.3)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        fig2.tight_layout()
        pdf.savefig(fig2)
        plt.close(fig2)

        # Recent form table page
        if not recent.empty:
            fig3, ax3 = plt.subplots(figsize=(8.5, max(4, len(recent) * 0.5 + 1.5)))
            ax3.axis("off")
            ax3.set_title(f"{opponent} — Recent Form (last {len(recent)} matches)", fontsize=13, fontweight="bold")
            table_data = [recent.columns.tolist()] + recent.values.tolist()
            tbl = ax3.table(cellText=table_data[1:], colLabels=table_data[0],
                            loc="center", cellLoc="center")
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            tbl.scale(1.2, 1.5)
            fig3.tight_layout()
            pdf.savefig(fig3)
            plt.close(fig3)

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_intel_card() -> None:
    hero_block("🗂", "Opposition Intelligence Card", "Pre-match scouting brief")
    st.session_state["ctx_row_count"] = "Intel Card"

    try:
        corners, freekicks, throwins, hops = _load()
    except Exception as exc:
        st.error(f"Failed to load data: {exc}")
        return

    all_teams = _all_teams(corners, freekicks, throwins)

    if not all_teams:
        st.warning("No team data found. Check that set piece data files are loaded correctly.")
        return

    with st.container():
        fc1, fc2 = st.columns(2)
        with fc1:
            my_team = st.selectbox("Your team", all_teams, key="intel_my_team")
        with fc2:
            opp_options = [t for t in all_teams if t != my_team]
            opponent = st.selectbox("Opponent", opp_options if opp_options else all_teams, key="intel_opponent") if opp_options else None

    if not opponent:
        st.info("At least two teams are required. Check your data files contain multiple teams.")
        return
    st.session_state["ctx_row_count"] = f"Intel Card · {opponent}"

    # Compute all stats
    opp_corners = _team_sp(corners, opponent)
    opp_fks = _team_sp(freekicks, opponent)
    opp_tis = _team_sp(throwins, opponent)

    kpis_corner = _sp_kpis(opp_corners)
    kpis_fk = _sp_kpis(opp_fks)
    kpis_ti = _sp_kpis(opp_tis)

    combined_opp = pd.concat([df for df in [opp_corners, opp_fks, opp_tis] if not df.empty],
                              ignore_index=True, sort=False)
    kpis_all = _sp_kpis(combined_opp)

    takers_df = _top_takers(opp_corners, n=3)
    hops_df = _top_hops(hops, opponent, n=3)
    preferences = _corner_preferences(corners, opponent)
    vulnerability = _defensive_vulnerability(corners, freekicks, throwins, opponent)
    recent = _recent_form(corners, freekicks, throwins, opponent, n=5)
    tier = _team_tier(hops, opponent)

    # ── Header banner ────────────────────────────────────────────────────────
    tier_colour = TIER_COLOURS.get(tier, "#334155")
    st.markdown(
        f"""<div style="background:#161922;border:1px solid rgba(255,255,255,0.08);
            border-top:3px solid {tier_colour};border-radius:8px;padding:1.2rem 1.5rem;
            margin-bottom:1rem;display:flex;align-items:center;gap:1.2rem">
            <div>
                <div style="font-size:2rem;font-weight:900;color:#fff;letter-spacing:-.03em">{opponent}</div>
                <div style="margin-top:.3rem">{_tier_badge(tier)}</div>
            </div>
            <div style="flex:1"></div>
            <div style="text-align:right;color:#9ca3af;font-size:.82rem">
                {kpis_all['deliveries']:,} total set pieces &nbsp;·&nbsp;
                {kpis_all['shots']} shots &nbsp;·&nbsp;
                {kpis_all['xg']:.2f} xG
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Three columns: Attack / Personnel / Defence ──────────────────────────
    col_atk, col_per, col_def = st.columns(3)

    with col_atk:
        section_header("Attack Threats")
        type_data = [
            ("Corners", kpis_corner, "#3b82f6"),
            ("Free Kicks", kpis_fk, "#22c55e"),
            ("Throw-ins", kpis_ti, "#f59e0b"),
        ]
        for label, kpis, colour in type_data:
            bar_width = min(100, int(kpis["xg_per_100"] / max(kpis_all["xg_per_100"], 0.01) * 100))
            st.markdown(
                f"""<div style="margin-bottom:.6rem">
                    <div style="display:flex;justify-content:space-between;font-size:.8rem;color:#cbd5e1">
                        <span>{label}</span><span>{kpis['xg_per_100']:.2f} xG/100</span>
                    </div>
                    <div style="background:#1e293b;border-radius:3px;height:8px;margin-top:3px">
                        <div style="background:{colour};width:{bar_width}%;height:8px;border-radius:3px"></div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        if not takers_df.empty:
            st.markdown("<div style='margin-top:.8rem;font-size:.75rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em'>Top Takers</div>", unsafe_allow_html=True)
            for _, row in takers_df.iterrows():
                st.markdown(
                    f"""<div style="background:#1e293b;border-radius:5px;padding:.4rem .7rem;margin-bottom:.3rem">
                        <div style="font-weight:700;color:#fff;font-size:.88rem">{row['Taker']}</div>
                        <div style="color:#94a3b8;font-size:.75rem">{int(row['Deliveries'])} deliveries · {row['xG/100']:.2f} xG/100</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    with col_per:
        section_header("Key Personnel")
        if not hops_df.empty:
            for _, row in hops_df.iterrows():
                rating_pct = min(100, int(float(row["Rating"]) * 100))
                tier_c = TIER_COLOURS.get(str(row.get("Tier", "")), "#334155")
                st.markdown(
                    f"""<div style="background:#1e293b;border-radius:6px;padding:.6rem .8rem;margin-bottom:.5rem">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <span style="font-weight:700;color:#fff;font-size:.9rem">{row['Player']}</span>
                            <span style="background:{tier_c};color:#fff;padding:.1rem .45rem;border-radius:3px;font-size:.68rem;font-weight:700">{row.get('Tier','')}</span>
                        </div>
                        <div style="background:#334155;border-radius:3px;height:6px;margin-top:.4rem">
                            <div style="background:{tier_c};width:{rating_pct}%;height:6px;border-radius:3px"></div>
                        </div>
                        <div style="color:#94a3b8;font-size:.72rem;margin-top:.2rem">Rating: {float(row['Rating']):.3f} · {float(row.get('Percentile', 0)):.0f}th pct</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No HOPS data for this team.")

    with col_def:
        section_header("Defensive Vulnerabilities")
        def_c = _sp_kpis(_apply_team_perspective(corners, opponent, "Against"))
        def_fk = _sp_kpis(_apply_team_perspective(freekicks, opponent, "Against"))
        def_ti = _sp_kpis(_apply_team_perspective(throwins, opponent, "Against"))

        worst = vulnerability.get("worst_type", "N/A")
        worst_x = vulnerability.get("worst_xg100", 0.0)
        colour = "#ef4444" if worst_x > 3.0 else "#f59e0b" if worst_x > 1.5 else "#22c55e"
        st.markdown(
            f"""<div style="background:#1e293b;border-radius:6px;padding:.7rem;margin-bottom:.6rem">
                <div style="font-size:.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em">Most exposed to</div>
                <div style="font-size:1.4rem;font-weight:800;color:{colour}">{worst}</div>
                <div style="font-size:.8rem;color:#cbd5e1">{worst_x:.2f} xG/100 conceded</div>
            </div>""",
            unsafe_allow_html=True,
        )
        for label, kpis in [("Corners", def_c), ("FKs", def_fk), ("Throw-ins", def_ti)]:
            st.markdown(
                f"<div style='font-size:.8rem;color:#cbd5e1;margin-bottom:.2rem'>"
                f"<b>{label}</b>: {kpis['xg_per_100']:.2f} xG/100 · {kpis['shot_rate']:.1f}% shot rate"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # ── Corner Preferences ───────────────────────────────────────────────────
    section_header("Corner Preferences")
    if not opp_corners.empty:
        pref_cols = st.columns(3)
        with pref_cols[0]:
            if "Technique" in opp_corners.columns:
                tech_counts = opp_corners["Technique"].value_counts().reset_index()
                tech_counts.columns = ["Technique", "Count"]
                fig_tech = go.Figure(go.Pie(
                    labels=tech_counts["Technique"], values=tech_counts["Count"],
                    hole=0.3, marker_colors=["#3b82f6", "#22c55e", "#f59e0b", "#94a3b8"],
                ))
                fig_tech.update_layout(height=260, margin=dict(l=5, r=5, t=30, b=5),
                                       title="Technique", legend=dict(font=dict(color="#cbd5e1")))
                render_plotly_visual(polish_plotly_figure(fig_tech), "Corner technique", "intel_tech_pie")

        with pref_cols[1]:
            if "side" in opp_corners.columns:
                side_counts = opp_corners["side"].value_counts().reset_index()
                side_counts.columns = ["Side", "Count"]
                fig_side = go.Figure(go.Bar(
                    x=side_counts["Side"], y=side_counts["Count"],
                    marker_color=["#3b82f6", "#22c55e"],
                ))
                fig_side.update_layout(height=260, margin=dict(l=5, r=5, t=30, b=5),
                                       title="Side preference", xaxis_title="Side", yaxis_title="Count")
                render_plotly_visual(polish_plotly_figure(fig_side), "Side preference", "intel_side_bar")

        with pref_cols[2]:
            if "Delivery height" in opp_corners.columns:
                height_counts = opp_corners["Delivery height"].value_counts().reset_index()
                height_counts.columns = ["Height", "Count"]
                fig_height = go.Figure(go.Bar(
                    x=height_counts["Height"], y=height_counts["Count"],
                    marker_color="#f59e0b",
                ))
                fig_height.update_layout(height=260, margin=dict(l=5, r=5, t=30, b=5),
                                         title="Delivery height", xaxis_title="Height", yaxis_title="Count")
                render_plotly_visual(polish_plotly_figure(fig_height), "Delivery height", "intel_height_bar")
    else:
        st.info("No corner data for this opponent.")

    # ── Recent Form ──────────────────────────────────────────────────────────
    section_header("Recent Form", "Last 5 matches — set piece output")
    if not recent.empty:
        render_analyst_table(recent, height=240, color_cols=["xG from SP", "Shots", "Goals"])
    else:
        st.info("No recent match data found.")

    # ── PDF Download ─────────────────────────────────────────────────────────
    section_header("Download Brief")
    safe_name = f"{opponent.lower().replace(' ', '_')}_intel_card_{date.today().strftime('%Y%m%d')}.pdf"
    if st.button("Generate PDF brief", key="intel_gen_pdf"):
        with st.spinner("Building PDF…"):
            pdf_bytes = _generate_pdf(
                opponent, tier,
                kpis_corner, kpis_fk, kpis_ti,
                takers_df, hops_df, preferences, vulnerability, recent,
            )
        if pdf_bytes:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=safe_name,
                mime="application/pdf",
                use_container_width=True,
                key="intel_dl_pdf",
            )
        else:
            st.warning("PDF generation requires matplotlib. Install it to enable exports.")
