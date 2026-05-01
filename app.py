from __future__ import annotations

from html import escape
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from mm_setpieces.utils import *
from mm_setpieces.utils import _read_excel_if_exists, _with_league


APP_SECTIONS = ["Home", "Corners", "Freekicks", "Throw-ins", "HOPS", "Delay Analysis"]
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "setplaypro-logo.jpg"
FILTER_PREFIXES = {
    "Corners": "corners",
    "Freekicks": "freekicks",
    "Throw-ins": "throwins",
    "HOPS": "hops",
    "Delay Analysis": "delay",
}


st.set_page_config(
    page_title="Michael Mackin Set Piece",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_app_style()


def _safe_sorted(values: pd.Series) -> list[str]:
    return sorted([str(v) for v in values.dropna().astype(str).unique().tolist() if str(v).strip()])


@st.cache_data(show_spinner=False)
def _cached_report_pdf(df: pd.DataFrame, label: str, opponent: str) -> bytes:
    return prematch_report_pdf_bytes(df, label, opponent)


@st.cache_data(show_spinner=False)
def load_hops_data(_data_version: str = DATA_VERSION) -> pd.DataFrame:
    sources = [
        _with_league(_read_excel_if_exists("SWE HOPS.xlsx"), "Allsvenskan"),
        _with_league(_read_excel_if_exists("GER HOPS.xlsx"), "Bundesliga"),
        _with_league(_read_excel_if_exists("CZ HOPS.xlsx"), "Czech First League"),
        _with_league(_read_excel_if_exists("duel_hops_rating_summary.xlsx"), "Unknown"),
    ]
    sources = [source for source in sources if not source.empty]
    if not sources:
        return pd.DataFrame(columns=["Player", "Team", "League", "Rating", "Percentile", "Tier"])

    df = pd.concat(sources, ignore_index=True, sort=False)
    df["Player"] = df["Player"].fillna("Unknown")
    df["Team"] = df["Team"].fillna("Unknown")
    df["League"] = df["League"].fillna("Unknown")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df = df.dropna(subset=["Rating"]).copy()
    df["Percentile"] = (df["Rating"].rank(pct=True) * 100).round(1)
    df["Tier"] = pd.cut(
        df["Percentile"],
        bins=[-0.1, 50, 75, 90, 100],
        labels=["Depth", "Rotation", "Strong", "Elite"],
    ).astype(str)
    return df.sort_values("Rating", ascending=False)


@st.cache_data(show_spinner=False)
def load_delay_workbook() -> dict[str, pd.DataFrame]:
    return _read_excel_if_exists("corner_delays (1).xlsx", sheet_name=None)


@st.cache_data(show_spinner=False)
def _clean_delay_events(df: pd.DataFrame) -> pd.DataFrame:
    clean = df.copy()
    if "League" not in clean.columns:
        clean["League"] = "Unknown"
    else:
        clean["League"] = clean["League"].fillna("Unknown")
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


def _fmt_num(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        value = 0
    return f"{value:,.{digits}f}"


def _mode_text(series: pd.Series) -> str:
    values = series.dropna().astype(str)
    values = values[values.str.strip().ne("") & values.str.lower().ne("unknown")]
    if values.empty:
        return "Unknown"
    return values.value_counts().index[0]


def _phase_snapshot(df: pd.DataFrame, phase: str, team: str) -> dict[str, object]:
    if df.empty or "Team" not in df.columns:
        return {"Phase": phase, "Rows": 0, "Set pieces": 0, "Shots": 0, "Goals": 0, "xG": 0.0, "xG / 100": 0.0, "xG / shot": 0.0, "Top taker": "Unknown", "Top shooter": "Unknown", "Shot rate %": 0.0, "Goal conv %": 0.0}
    part = df[df["Team"].astype(str).eq(team)].copy()
    if part.empty:
        return {"Phase": phase, "Rows": 0, "Set pieces": 0, "Shots": 0, "Goals": 0, "xG": 0.0, "xG / 100": 0.0, "xG / shot": 0.0, "Top taker": "Unknown", "Top shooter": "Unknown", "Shot rate %": 0.0, "Goal conv %": 0.0}

    if "possession" in part.columns:
        set_pieces = int(part["possession"].nunique())
        shot_part = part[part["is_shot"]] if "is_shot" in part.columns else part.iloc[0:0]
        goal_part = part[part["is_goal"]] if "is_goal" in part.columns else part.iloc[0:0]
        shots = int(shot_part["possession"].nunique()) if not shot_part.empty else 0
        goals = int(goal_part["possession"].nunique()) if not goal_part.empty else 0
    else:
        set_pieces = int(len(part))
        shots = int(part["is_shot"].sum()) if "is_shot" in part.columns else 0
        goals = int(part["is_goal"].sum()) if "is_goal" in part.columns else 0

    if set(["possession", "shot_x", "shot_y", "xg"]).issubset(part.columns):
        xg_rows = part[part["shot_x"].notna()][["possession", "shot_x", "shot_y", "xg"]].drop_duplicates()
        total_xg = float(xg_rows["xg"].fillna(0).sum()) if not xg_rows.empty else 0.0
    else:
        total_xg = float(part["xg"].fillna(0).sum()) if "xg" in part.columns else 0.0

    return {
        "Phase": phase,
        "Rows": int(len(part)),
        "Set pieces": set_pieces,
        "Shots": shots,
        "Goals": goals,
        "xG": round(total_xg, 2),
        "xG / 100": round((total_xg / set_pieces * 100) if set_pieces else 0, 2),
        "xG / shot": round((total_xg / shots) if shots else 0, 3),
        "Top taker": _mode_text(part["Taker"]) if "Taker" in part.columns else "Unknown",
        "Top shooter": _mode_text(part["Shooter"]) if "Shooter" in part.columns else "Unknown",
        "Shot rate %": round((shots / set_pieces * 100) if set_pieces else 0, 1),
        "Goal conv %": round((goals / shots * 100) if shots else 0, 1),
    }


@st.cache_data(show_spinner=False)
def command_center_data(_data_version: str = DATA_VERSION) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    corners = load_prepared_sp_data("Corners")
    freekicks = load_prepared_sp_data("Freekicks")
    throwins = load_prepared_sp_data("Throw ins")
    hops = load_hops_data()
    return corners, freekicks, throwins, hops


def _team_options(corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, hops: pd.DataFrame) -> list[str]:
    teams: set[str] = set()
    for df in [corners, freekicks, throwins, hops]:
        if not df.empty and "Team" in df.columns:
            teams.update(str(v) for v in df["Team"].dropna().unique() if str(v).strip() and str(v) != "Unknown")
    return sorted(teams)


def team_snapshot_table(team: str, corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame) -> pd.DataFrame:
    rows = [
        _phase_snapshot(corners, "Corners", team),
        _phase_snapshot(freekicks, "Freekicks", team),
        _phase_snapshot(throwins, "Throw-ins", team),
    ]
    return pd.DataFrame(rows)


def search_people(query: str, corners: pd.DataFrame, freekicks: pd.DataFrame, throwins: pd.DataFrame, hops: pd.DataFrame) -> pd.DataFrame:
    query = query.strip().lower()
    if len(query) < 2:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for phase, df in [("Corners", corners), ("Freekicks", freekicks), ("Throw-ins", throwins)]:
        if df.empty:
            continue
        for role, col in [("Taker", "Taker"), ("Shooter", "Shooter")]:
            if col not in df.columns:
                continue
            matches = df[df[col].fillna("").astype(str).str.lower().str.contains(query, regex=False)]
            if matches.empty:
                continue
            grouped = (
                matches.groupby([col, "Team"], dropna=False)
                .agg(Rows=(col, "size"), xG=("xg", "sum") if "xg" in matches.columns else (col, "size"))
                .reset_index()
                .sort_values(["Rows", "xG"], ascending=False)
                .head(6)
            )
            for _, row in grouped.iterrows():
                rows.append({
                    "Name": row[col],
                    "Team": row["Team"],
                    "Role": role,
                    "Dataset": phase,
                    "Rows": int(row["Rows"]),
                    "xG": round(float(row["xG"]), 2),
                })

    if not hops.empty and "Player" in hops.columns:
        h = hops[hops["Player"].fillna("").astype(str).str.lower().str.contains(query, regex=False)]
        for _, row in h.head(10).iterrows():
            rows.append({
                "Name": row["Player"],
                "Team": row.get("Team", "Unknown"),
                "Role": "HOPS profile",
                "Dataset": "HOPS",
                "Rows": 1,
                "xG": np.nan,
                "Rating": round(float(row.get("Rating", 0)), 3),
                "Tier": row.get("Tier", ""),
            })

    return pd.DataFrame(rows)


def selected_team_staff_read(team: str, snapshot: pd.DataFrame, hops: pd.DataFrame) -> tuple[str, str, str]:
    if snapshot.empty or snapshot["Set pieces"].sum() == 0:
        phase_read = "No restart volume found"
        role_read = "No taker data found"
    else:
        best_phase = snapshot.sort_values(["xG", "Shots", "Set pieces"], ascending=False).iloc[0]
        phase_read = f"{best_phase['Phase']} lead the threat profile: {_fmt_num(float(best_phase['xG']), 2)} xG from {int(best_phase['Shots'])} shots."
        takers = snapshot["Top taker"].dropna().astype(str)
        takers = takers[takers.ne("Unknown")]
        role_read = f"Primary repeat name: {takers.value_counts().index[0]}." if not takers.empty else "No clear repeat taker yet."

    if not hops.empty and "Team" in hops.columns:
        team_hops = hops[hops["Team"].astype(str).eq(team)].sort_values("Rating", ascending=False)
        if not team_hops.empty:
            top = team_hops.iloc[0]
            hops_read = f"{top['Player']} is the top HOPS profile ({float(top['Rating']):.3f}, {top.get('Tier', 'rated')})."
        else:
            hops_read = "No HOPS profile found for this team."
    else:
        hops_read = "No HOPS profile found for this team."

    return phase_read, role_read, hops_read


def set_section(section: str) -> None:
    st.session_state["pending_section"] = section
    st.rerun()


def reset_current_filters(section: str) -> None:
    prefix = FILTER_PREFIXES.get(section)
    if prefix is None:
        return
    for key in list(st.session_state.keys()):
        if key.startswith(f"{prefix}_"):
            del st.session_state[key]
    st.rerun()


def render_single_app_sidebar() -> str:
    if "pending_section" in st.session_state:
        st.session_state["section_select"] = st.session_state.pop("pending_section")
    if "section" not in st.session_state:
        st.session_state["section"] = "Home"

    st.sidebar.markdown("### Desk")
    section = st.sidebar.radio(
        "Choose view",
        APP_SECTIONS,
        index=APP_SECTIONS.index(st.session_state.get("section_select", st.session_state["section"])),
        key="section_select",
        label_visibility="collapsed",
    )
    st.session_state["section"] = section
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {section} filters")
    if section != "Home":
        if st.sidebar.button("Reset filters", key=f"reset_{section}", use_container_width=True):
            reset_current_filters(section)
    return section


def render_landing() -> None:
    st.markdown(
        """
        <style>
            :root {
                --mm-landing-logo: min(340px, 66vw);
            }
            html,
            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            .main {
                background: #ffffff !important;
                overflow: hidden !important;
            }
            header[data-testid="stHeader"],
            [data-testid="stDecoration"],
            footer,
            #MainMenu {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
            }
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            .block-container {
                width: 100vw !important;
                max-width: 100vw !important;
                height: 100vh !important;
                min-height: 100vh !important;
                padding: 0 !important;
                padding-bottom: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                gap: .9rem !important;
                background: #ffffff !important;
                overflow: hidden !important;
            }
            .block-container > div {
                width: min(380px, 76vw) !important;
            }
            div[data-testid="stImage"] {
                width: var(--mm-landing-logo) !important;
                max-width: var(--mm-landing-logo) !important;
                margin: 0 auto !important;
                background: transparent !important;
                border: 0 !important;
                padding: 0 !important;
                box-shadow: none !important;
            }
            div[data-testid="stImage"] img {
                width: var(--mm-landing-logo) !important;
                max-width: var(--mm-landing-logo) !important;
                height: auto !important;
                display: block !important;
            }
            div.stButton {
                width: min(260px, 68vw) !important;
                margin: 0 auto !important;
            }
            div.stButton > button {
                min-height: 2.75rem !important;
                box-shadow: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mm-landing-shell">', unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=340)
    else:
        st.markdown('<div class="mm-landing-wordmark"><span>SetPlay</span><strong>Pro</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="mm-landing-action">', unsafe_allow_html=True)
    if st.button("Continue to playform", key="continue_to_playform", use_container_width=True):
        st.session_state["show_playform"] = True
        st.session_state["section"] = "Home"
        st.session_state["section_select"] = "Home"
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_plotly_visual(fig, label: str, key: str) -> None:
    if PLOTLY_AVAILABLE:
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "modeBarButtonsToRemove": ["toImage"]})
    else:
        st.image(plotly_figure_png_bytes(fig), use_container_width=True)
    render_plotly_png_download(fig, label, key)


def render_mpl_visual(fig, label: str, key: str) -> None:
    st.pyplot(fig, use_container_width=True)
    render_matplotlib_png_download(fig, label, key)


def _plot_colors() -> list[str]:
    return ["#111827", "#c1121f", "#1d4ed8", "#15803d", "#b45309", "#7c3aed", "#64748b"]


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", color: str | None = None, orientation: str = "v", barmode: str = "relative") -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    groups = [(None, df)] if not color or color not in df.columns else list(df.groupby(color, dropna=False))
    for idx, (name, part) in enumerate(groups):
        trace_name = str(name) if name is not None else y
        if orientation == "h":
            fig.add_bar(x=part[x], y=part[y], name=trace_name, orientation="h", marker_color=colors[idx % len(colors)])
        else:
            fig.add_bar(x=part[x], y=part[y], name=trace_name, marker_color=colors[idx % len(colors)])
    fig.update_layout(title=title, barmode=barmode, legend_title_text="", xaxis_title=x, yaxis_title=y)
    return fig


def histogram_chart(df: pd.DataFrame, column: str, title: str = "", color: str | None = None, nbins: int = 20) -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    groups = [(None, df)] if not color or color not in df.columns else list(df.groupby(color, dropna=False))
    for idx, (name, part) in enumerate(groups):
        fig.add_histogram(x=part[column], nbinsx=nbins, name=str(name) if name is not None else column, marker_color=colors[idx % len(colors)])
    fig.update_layout(title=title, barmode="overlay", legend_title_text="", xaxis_title=column, yaxis_title="Count")
    fig.update_traces(opacity=0.82)
    return fig


def box_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> go.Figure:
    fig = go.Figure()
    colors = _plot_colors()
    for idx, (name, part) in enumerate(df.groupby(x, dropna=False)):
        fig.add_box(y=part[y], name=str(name), marker_color=colors[idx % len(colors)], boxmean=True)
    fig.update_layout(title=title, legend_title_text="", xaxis_title=x, yaxis_title=y, showlegend=False)
    return fig


def render_home() -> None:
    corners, freekicks, throwins, hops = command_center_data()
    teams = _team_options(corners, freekicks, throwins, hops)

    hero_block(
        "Michael Mackin · Scouting Department",
        "Set-piece opposition desk",
        "A match-prep workspace for restart threats, player roles, duel profiles, timing clues, and report-ready tactical evidence.",
    )

    st.markdown(
        """
        <div class="mm-scout-shell">
            <div class="mm-command-panel">
                <div class="mm-command-title">Match Prep Flow</div>
                <div class="mm-command-row">
                    <div class="mm-command-label">1 · Load</div>
                    <div class="mm-command-value">Open a restart desk and narrow the opponent, phase, takers, outcome, and game-state filters.</div>
                </div>
                <div class="mm-command-row">
                    <div class="mm-command-label">2 · Read</div>
                    <div class="mm-command-value">Start with the insight cards, origin maps, role tables, and possession-level sequence rankings.</div>
                </div>
                <div class="mm-command-row">
                    <div class="mm-command-label">3 · Brief</div>
                    <div class="mm-command-value">Use the report tab to export the active view into a pre-match PDF with maps and scouting labels.</div>
                </div>
            </div>
            <div class="mm-command-panel">
                <div class="mm-command-title">Scouting Outputs</div>
                <div class="mm-command-row">
                    <div class="mm-command-label">Roles</div>
                    <div class="mm-command-value">Takers, shooters, throwers, targets, delivery profiles, and duel specialists.</div>
                </div>
                <div class="mm-command-row">
                    <div class="mm-command-label">Threats</div>
                    <div class="mm-command-value">Shot value, origin zones, channel bias, final-third pressure, and delay behaviour.</div>
                </div>
                <div class="mm-command-row">
                    <div class="mm-command-label">Reports</div>
                    <div class="mm-command-value">PDF briefings, mplsoccer pitch visuals, and exportable analyst tables.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mm-feature-strip">
            <div class="mm-feature-pill">
                <div class="mm-feature-value">5 workbooks</div>
                <div class="mm-feature-label">Live scouting sources</div>
            </div>
            <div class="mm-feature-pill">
                <div class="mm-feature-value">Sequence level</div>
                <div class="mm-feature-label">Possession evidence</div>
            </div>
            <div class="mm-feature-pill">
                <div class="mm-feature-value">Roles + archetypes</div>
                <div class="mm-feature-label">Player ID</div>
            </div>
            <div class="mm-feature-pill">
                <div class="mm-feature-value">On-demand export</div>
                <div class="mm-feature-label">Faster reruns</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header("Command Center", "Fast team view, comparison, and player search")
    if teams:
        default_team = teams[0]
        command_left, command_right = st.columns([1.05, .95])
        with command_left:
            selected_team = st.selectbox("Team snapshot", teams, index=teams.index(default_team), key="home_team_snapshot")
            snapshot = team_snapshot_table(selected_team, corners, freekicks, throwins)
            total_set_pieces = int(snapshot["Set pieces"].sum())
            total_shots = int(snapshot["Shots"].sum())
            total_goals = int(snapshot["Goals"].sum())
            total_xg = float(snapshot["xG"].sum())
            xg_per_100 = (total_xg / total_set_pieces * 100) if total_set_pieces else 0
            shot_rate = (total_shots / total_set_pieces * 100) if total_set_pieces else 0
            phase_read, role_read, hops_read = selected_team_staff_read(selected_team, snapshot, hops)
            st.markdown(
                f"""
                <div class="mm-panel">
                    <div class="mm-panel-title">{selected_team}</div>
                    <div class="mm-panel-copy">All restart phases in one staff-ready snapshot.</div>
                    <div class="mm-stat-grid">
                        <div class="mm-stat-card">
                            <div class="mm-stat-label">Set pieces</div>
                            <div class="mm-stat-value">{total_set_pieces:,}</div>
                        </div>
                        <div class="mm-stat-card is-red">
                            <div class="mm-stat-label">Shots</div>
                            <div class="mm-stat-value">{total_shots:,}</div>
                        </div>
                        <div class="mm-stat-card">
                            <div class="mm-stat-label">Goals</div>
                            <div class="mm-stat-value">{total_goals:,}</div>
                        </div>
                        <div class="mm-stat-card is-red">
                            <div class="mm-stat-label">Total xG</div>
                            <div class="mm-stat-value">{_fmt_num(total_xg, 2)}</div>
                        </div>
                        <div class="mm-stat-card">
                            <div class="mm-stat-label">xG / 100</div>
                            <div class="mm-stat-value">{_fmt_num(xg_per_100, 2)}</div>
                        </div>
                        <div class="mm-stat-card is-red">
                            <div class="mm-stat-label">Shot rate</div>
                            <div class="mm-stat-value">{_fmt_num(shot_rate, 1)}%</div>
                        </div>
                    </div>
                    <div class="mm-profile-strip">
                        <div class="mm-profile-card">
                            <div class="mm-profile-title">Threat Read</div>
                            <div class="mm-profile-copy">{escape(phase_read)}</div>
                        </div>
                        <div class="mm-profile-card">
                            <div class="mm-profile-title">Role Read</div>
                            <div class="mm-profile-copy">{escape(role_read)}</div>
                        </div>
                        <div class="mm-profile-card">
                            <div class="mm-profile-title">Duel Read</div>
                            <div class="mm-profile-copy">{escape(hops_read)}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_analyst_table(snapshot, height=210)

        with command_right:
            compare_team = st.selectbox("Compare with", teams, index=min(1, len(teams) - 1), key="home_compare_team")
            comparison = pd.concat(
                [
                    team_snapshot_table(selected_team, corners, freekicks, throwins).assign(Team=selected_team),
                    team_snapshot_table(compare_team, corners, freekicks, throwins).assign(Team=compare_team),
                ],
                ignore_index=True,
            )
            fig = bar_chart(comparison, x="Phase", y="xG", color="Team", barmode="group")
            fig.update_layout(height=345, margin=dict(l=10, r=10, t=35, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "Home team comparison", "home_team_comparison_png")

        search_query = st.text_input("Search player, taker, shooter, or HOPS profile", key="home_people_search", placeholder="Type at least 2 characters")
        search_results = search_people(search_query, corners, freekicks, throwins, hops)
        if not search_results.empty:
            section_header("Search Results", "Across restarts and HOPS")
            render_analyst_table(search_results, height=260)
    else:
        st.info("No team names were found in the bundled data.")

    section_header("Opposition Restart Desks", "Primary event analysis")
    cards = [
        (
            "Corners",
            "Corner delivery dossier",
            "Rank teams, takers, target zones, shot value, second-ball patterns, and match-ready delivery maps.",
            "Data/Allsvenskan - Corners 2025.xlsx + Data/CZ - Corners 2025-2026.csv",
        ),
        (
            "Freekicks",
            "Dead-ball origin dossier",
            "Free-kick origins, channel threat, taker tendencies, shooter value, and possession-level outcomes.",
            "Data/SWE SP.xlsx + Data/Czech SP.xlsx · From Free Kick",
        ),
        (
            "Throw-ins",
            "Touchline restart dossier",
            "Territory, side bias, pressure profile, thrower output, and shot creation from throw-in sequences.",
            "Data/SWE SP.xlsx + Data/Czech SP.xlsx · From Throw In",
        ),
    ]

    for col, (title, kicker, copy, source) in zip(st.columns(3), cards):
        with col:
            st.markdown(
                f"""
                <div class="mm-nav-card">
                    <div class="mm-card-kicker">Desk · {kicker}</div>
                    <div class="mm-nav-title">{title}</div>
                    <div class="mm-nav-copy">{copy}</div>
                    <div class="mm-tiny">{source}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open {title}", key=f"home_open_{title}"):
                set_section(title)

    section_header("Specialist Scouting Modules", "Player rating model and timing audit")
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            """
            <div class="mm-nav-card">
                <div class="mm-card-kicker">Module · Duel model</div>
                <div class="mm-nav-title">HOPS</div>
                <div class="mm-nav-copy">Aerial/duel strength by player and team, with percentiles, tiers, elite profiles, and weak-side risk checks.</div>
                <div class="mm-tiny">Data/SWE HOPS.xlsx + Data/CZ HOPS.xlsx</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open HOPS", key="home_open_hops"):
            set_section("HOPS")

    with s2:
        st.markdown(
            """
            <div class="mm-nav-card">
                <div class="mm-card-kicker">Module · Timing model</div>
                <div class="mm-nav-title">Delay Analysis</div>
                <div class="mm-nav-copy">Corner timing audit with delay bands, exit events, slow match profiles, and extraction reliability checks.</div>
                <div class="mm-tiny">Data/corner_delays (1).xlsx</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Delay Analysis", key="home_open_delay"):
            set_section("Delay Analysis")


def filter_sp_page_data(df: pd.DataFrame, label: str, key_prefix: str) -> tuple[pd.DataFrame, list[tuple[str, object]]]:
    teams = ["All"] + _safe_sorted(df["Team"]) if "Team" in df.columns else ["All"]
    leagues = ["All"] + _safe_sorted(df["League"]) if "League" in df.columns else ["All"]
    sides = ["All"] + _safe_sorted(df["side"]) if "side" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    techniques = _safe_sorted(df["Technique"]) if "Technique" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shot_outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    team = st.sidebar.selectbox("Team", teams, key=f"{key_prefix}_team")
    league = st.sidebar.selectbox("League", leagues, key=f"{key_prefix}_league")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key=f"{key_prefix}_sample")
    side = st.sidebar.radio("Side", sides, key=f"{key_prefix}_side")
    time_in_game = st.sidebar.selectbox("Time in the game", periods, key=f"{key_prefix}_period")

    minute_min = 0
    minute_max = 95
    if "minute" in df.columns and not df["minute"].dropna().empty:
        minute_values = pd.to_numeric(df["minute"], errors="coerce").dropna()
        if not minute_values.empty:
            minute_min = int(min(0, minute_values.min()))
            minute_max = max(95, int(minute_values.max()))
    minute_range = st.sidebar.slider("Minute range", minute_min, minute_max, (minute_min, minute_max), key=f"{key_prefix}_minutes")
    taker_filter = st.sidebar.multiselect("Taker", takers, key=f"{key_prefix}_taker")
    technique_filter = st.sidebar.multiselect("Delivery technique", techniques, key=f"{key_prefix}_technique")
    height_filter = st.sidebar.multiselect("Delivery height", heights, key=f"{key_prefix}_height")
    shot_outcome_filter = st.sidebar.multiselect("Shot outcome", shot_outcomes, key=f"{key_prefix}_outcome")
    only_shots = st.sidebar.checkbox(f"Only {label.lower()} ending with a shot", value=False, key=f"{key_prefix}_shots_only")

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

    filters = [
        ("Team", team),
        ("League", league),
        ("Sample", sample),
        ("Side", side),
        ("Period", time_in_game),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Taker", taker_filter),
        ("Technique", technique_filter),
        ("Height", height_filter),
        ("Shot outcome", shot_outcome_filter),
        ("Shot only", "Yes" if only_shots else "All"),
    ]
    return filtered, filters


def render_corners() -> None:
    label = "Corners"
    df = load_prepared_sp_data(label)
    hero_block(
        "Set-piece intelligence",
        label,
        "Scout team patterns, taker roles, shot output, and match-level set-piece value from the connected event workbooks.",
    )
    if df.empty:
        st.warning("No corner rows were found in the bundled workbook(s).")
        return

    render_workflow_rail()
    filtered, filters = filter_sp_page_data(df, label, "corners")
    render_export_controls(filtered, label, label)
    st.caption("Corners use Data/Allsvenskan - Corners 2025.xlsx and Data/CZ - Corners 2025-2026.csv.")
    render_filter_summary(label, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()

    kpi_row(filtered)
    info_panel(filtered)
    view = st.radio("View", ["Briefing", "Pitch Evidence", "PDF Brief", "Event Log"], horizontal=True, key="corners_view")

    if view == "Briefing":
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
        insight_cols = st.columns(2)
        for idx, insight in enumerate(generate_set_piece_insights(filtered, label)):
            with insight_cols[idx % 2]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)

        section_header("Quick Reads", "Fast visual summaries for the active filter")
        qr1, qr2, qr3 = st.columns(3)
        with qr1:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Taker", "Top takers", top_n=8, color="#c1121f"), "Corners top takers", "corners_top_takers_png")
        with qr2:
            render_plotly_visual(categorical_breakdown_figure(filtered, "Shot outcome", "Shot outcomes", top_n=8, color="#1d4ed8"), "Corners shot outcomes", "corners_shot_outcomes_png")
        with qr3:
            render_plotly_visual(minute_distribution_figure(filtered, "Minute distribution"), "Corners minute distribution", "corners_minute_distribution_png")

        section_header("Scouting Boards", "Workbook-derived rankings and tactical pattern reads")
        board_view = st.radio("Scouting board", ["Team Threat", "Takers", "Shot Targets", "Patterns", "Match Log"], horizontal=True, key="corners_board")
        if board_view == "Team Threat":
            render_analyst_table(build_team_leaderboard(filtered), height=430)
        elif board_view == "Takers":
            render_analyst_table(build_taker_leaderboard(filtered), height=430)
        elif board_view == "Shot Targets":
            render_analyst_table(build_shooter_leaderboard(filtered), height=430)
        elif board_view == "Patterns":
            st.markdown('<div class="mm-table-note">Pattern rows combine team, side, technique, height, target zone, and outcome.</div>', unsafe_allow_html=True)
            render_analyst_table(build_pattern_library(filtered), height=430)
        elif board_view == "Match Log":
            render_analyst_table(build_match_log(filtered), height=430)

        section_header("Roles & Archetypes", "Condensed scouting labels for preparation")
        role_left, role_right = st.columns(2)
        with role_left:
            render_analyst_table(build_role_archetypes(filtered, label).head(15), height=360)
        with role_right:
            render_analyst_table(build_team_archetypes(filtered).head(15), height=360)

    elif view == "Pitch Evidence":
        visual_view = st.radio("Pitch visual", ["Interactive maps", "Report visuals"], horizontal=True, key="corners_visual")
        if visual_view == "Interactive maps":
            left, right = st.columns(2)
            with left:
                render_plotly_visual(polish_plotly_figure(shotmap_figure(filtered, f"{label} shotmap · vertical half pitch")), "Corners shotmap", "corners_shotmap_png")
            with right:
                render_plotly_visual(polish_plotly_figure(delivery_map_figure(filtered, f"{label} delivery map · vertical half pitch")), "Corners delivery map", "corners_delivery_map_png")
        else:
            left, right = st.columns(2)
            with left:
                render_mpl_visual(mplsoccer_delivery_figure(filtered, label), "Corners report delivery map", "corners_report_delivery_map_png")
            with right:
                render_mpl_visual(mplsoccer_shot_figure(filtered, label), "Corners report shot map", "corners_report_shot_map_png")

    elif view == "PDF Brief":
        section_header("Pre-Match PDF", "Download a staff briefing from the current filters")
        report_left, report_right = st.columns([1, 1.2])
        with report_left:
            opponent = st.text_input("Opponent / report label", value="", key="corners_pdf_label")
            st.caption("The PDF uses the active sidebar filters, role classifications, archetypes, insights, and mplsoccer visuals.")
        with report_right:
            safe_name = (opponent.strip() or label).lower().replace(" ", "_").replace("/", "-")
            st.markdown('<div class="mm-table-note">PDF generation is prepared on demand because pitch images are heavier than tables.</div>', unsafe_allow_html=True)
            if st.checkbox("Prepare PDF brief", key="corners_prepare_pdf"):
                st.download_button("Download pre-match PDF", data=_cached_report_pdf(filtered, label, opponent.strip()), file_name=f"{safe_name}_set_piece_report.pdf", mime="application/pdf", use_container_width=True)

    elif view == "Event Log":
        section_header("Event Log", f"{len(filtered):,} workbook rows in the current filter")
        display_cols = [c for c in [
            "Match", "Team", "SP_Type", "Taker", "Shooter", "side", "minute", "second",
            "Technique", "Delivery height", "Shot outcome", "xg", "Delivery outcome",
            "Defensive_setup", "Occupation_Rating", "Proximity_Rating", "Duel_Win_Prob",
            "OPS_Opponent_Rating", "timestamp",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=620)


def render_sequence_page(label: str) -> None:
    is_freekick = label == "Freekicks"
    readable = "Freekicks" if is_freekick else "Throw-ins"
    df = load_prepared_sp_data("Freekicks" if is_freekick else "Throw ins")
    hero_block(
        "Dead-ball intelligence" if is_freekick else "Touchline restart intelligence",
        readable,
        "Specialist view for free-kick origins, delivery profiles, takers, shooters, and possession-level shot value."
        if is_freekick else
        "Specialist view for throw-in territory, touchline pressure, taker profiles, shot creation, and possession-level output.",
    )
    if df.empty:
        st.warning(f"No {readable.lower()} rows were found in Data/SWE SP.xlsx or Data/Czech SP.xlsx.")
        return

    render_workflow_rail()
    key = "freekicks" if is_freekick else "throwins"
    leagues = ["All"] + _safe_sorted(df["League"]) if "League" in df.columns else ["All"]
    teams = ["All"] + _safe_sorted(df["Team"]) if "Team" in df.columns else ["All"]
    periods = ["All"] + _safe_sorted(df["game_period"]) if "game_period" in df.columns else ["All"]
    takers = _safe_sorted(df["Taker"]) if "Taker" in df.columns else []
    shooters = _safe_sorted(df["Shooter"]) if "Shooter" in df.columns else []
    heights = _safe_sorted(df["Delivery height"]) if "Delivery height" in df.columns else []
    outcomes = _safe_sorted(df["Shot outcome"]) if "Shot outcome" in df.columns else []

    league = st.sidebar.selectbox("League", leagues, key=f"{key}_league")
    team = st.sidebar.selectbox("Team", teams, key=f"{key}_team")
    period = st.sidebar.selectbox("Game period", periods, key=f"{key}_period")
    sample = st.sidebar.radio("Sample", ["Total", "Last 10 games"], key=f"{key}_sample")
    minute_min = int(pd.to_numeric(df["minute"], errors="coerce").fillna(0).min()) if "minute" in df.columns else 0
    minute_max = max(95, int(pd.to_numeric(df["minute"], errors="coerce").fillna(95).max())) if "minute" in df.columns else 95
    minute_range = st.sidebar.slider("Minute range", minute_min, minute_max, (minute_min, minute_max), key=f"{key}_minutes")
    taker_filter = st.sidebar.multiselect("Initial / sequence taker" if is_freekick else "Thrower / sequence starter", takers, key=f"{key}_taker")
    shooter_filter = st.sidebar.multiselect("Shooter", shooters, key=f"{key}_shooter")
    height_filter = st.sidebar.multiselect("Pass height" if is_freekick else "Initial pass height", heights, key=f"{key}_height")
    outcome_filter = st.sidebar.multiselect("Shot outcome", outcomes, key=f"{key}_outcome")

    filtered = df.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].eq(league)].copy()
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

    sequences = freekick_sequence_summary(filtered) if is_freekick else throwin_sequence_summary(filtered)
    filters = [
        ("League", league), ("Team", team), ("Period", period), ("Sample", sample),
        ("Minutes", f"{minute_range[0]}-{minute_range[1]}" if minute_range != (minute_min, minute_max) else "All"),
        ("Taker" if is_freekick else "Thrower", taker_filter), ("Shooter", shooter_filter),
        ("Height", height_filter), ("Shot outcome", outcome_filter),
    ]

    render_export_controls(filtered, key, readable)
    st.caption(
        "Source: Data/SWE SP.xlsx and Data/Czech SP.xlsx filtered to From Free Kick. Sequence tables group rows by match_id, possession, and team."
        if is_freekick else
        "Source: Data/SWE SP.xlsx and Data/Czech SP.xlsx filtered to From Throw In. Sequence tables group rows by match_id, possession, and team."
    )
    render_filter_summary(readable, len(df), len(filtered), filters)
    if filtered.empty:
        render_empty_filter_state()

    kpi_row(filtered)
    seq_count = int(len(sequences))
    avg_actions = float(sequences["Actions"].mean()) if not sequences.empty else 0.0
    third_metric = float((sequences["Zone"].eq("Direct threat" if is_freekick else "Final-third pressure")).mean() * 100) if not sequences.empty else 0.0
    profile_metric = float((sequences["Zone"].eq("Wide delivery")).mean() * 100) if is_freekick and not sequences.empty else float((sequences["Profile"].eq("Long throw threat")).mean() * 100) if not is_freekick and not sequences.empty else 0.0
    best_seq_xg = float(sequences["Total xG"].max()) if not sequences.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("FK sequences" if is_freekick else "Throw-in sequences", seq_count)
    c2.metric("Avg actions", f"{avg_actions:.1f}")
    c3.metric("Direct threat share" if is_freekick else "Final-third share", f"{third_metric:.1f}%")
    c4.metric("Wide delivery share" if is_freekick else "Long throw share", f"{profile_metric:.1f}%")
    st.metric("Best sequence xG", f"{best_seq_xg:.3f}")

    view = st.radio("View", ["Briefing", "Origins", "Roles", "Pitch Evidence", "Event Log"], horizontal=True, key=f"{key}_view")
    if view == "Briefing":
        insights = generate_set_piece_insights(filtered, readable)
        if not sequences.empty:
            top_zone = sequences["Zone"].value_counts().head(1)
            if not top_zone.empty:
                insights.insert(0, f"Most common {'origin profile' if is_freekick else 'territory'} is {top_zone.index[0].lower()} ({top_zone.iloc[0]} sequences).")

        top_left, top_right = st.columns([0.9, 1.35])
        with top_left:
            section_header(f"{readable} Brief", "Highest-signal notes")
            for insight in insights[:5]:
                st.markdown(f"<div class='mm-insight-card'>{insight}</div>", unsafe_allow_html=True)
        with top_right:
            section_header("Origin Map", "Starting points sized by sequence xG")
            render_analyst_table((freekick_zone_summary(filtered) if is_freekick else throwin_zone_summary(filtered)).head(12), height=310)

        left, right = st.columns([1.1, 1])
        with left:
            section_header("Origin Threat Board" if is_freekick else "Territory Threat Board", "Sequence value by restart location")
            render_analyst_table(freekick_zone_summary(filtered) if is_freekick else throwin_zone_summary(filtered), height=390)
        with right:
            section_header("Priority Sequences", f"Best possession-level {readable.lower()} outcomes")
            base_cols = [
                "Match", "Team", "Minute", "Zone", "Channel" if is_freekick else "Side",
                "Initial taker", "Initial height", "Actions", "Shots", "Goals", "Total xG",
                "Best shooter", "Best shot xG", "Shot outcome",
            ]
            if not is_freekick:
                base_cols.insert(5, "Profile")
            display = sequences[[c for c in base_cols if c in sequences.columns]] if not sequences.empty else sequences
            render_analyst_table(display.head(30), height=390)

    elif view == "Origins":
        left, right = st.columns([1.55, 1])
        with left:
            section_header("Origin Map", f"{readable} starting points sized by possession xG")
            fig = freekick_origin_map_figure(filtered) if is_freekick else throwin_origin_map_figure(filtered)
            render_plotly_visual(polish_plotly_figure(fig), f"{readable} origin map", f"{key}_origin_map_png")
        with right:
            mix_col = "Zone"
            section_header("Zone Mix" if is_freekick else "Territory Mix", "Volume by restart territory")
            zone_mix = sequences.groupby(mix_col, dropna=False).size().reset_index(name="Sequences") if not sequences.empty else pd.DataFrame()
            if not zone_mix.empty:
                fig = bar_chart(zone_mix.sort_values("Sequences", ascending=False), x=mix_col, y="Sequences", color=mix_col)
                fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                render_plotly_visual(polish_plotly_figure(fig), f"{readable} zone mix", f"{key}_zone_mix_png")
            section_header("Channel Mix" if is_freekick else "Profile Mix", "How teams use the restart")
            group_col = "Channel" if is_freekick else "Profile"
            group_mix = sequences.groupby(group_col, dropna=False).size().reset_index(name="Sequences") if not sequences.empty else pd.DataFrame()
            if not group_mix.empty:
                fig = bar_chart(group_mix.sort_values("Sequences", ascending=False), x=group_col, y="Sequences", color=group_col)
                fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                render_plotly_visual(polish_plotly_figure(fig), f"{readable} channel profile mix", f"{key}_channel_profile_mix_png")

    elif view == "Roles":
        left, right = st.columns(2)
        with left:
            section_header("Taker Roles" if is_freekick else "Thrower Roles", "Sequences started, value created, and preferred zones")
            render_analyst_table(freekick_taker_summary(filtered) if is_freekick else throwin_taker_summary(filtered), height=620)
        with right:
            section_header("Shot Targets", f"Shooters reached through {readable.lower()} possessions")
            render_analyst_table(freekick_shooter_summary(filtered) if is_freekick else throwin_shooter_summary(filtered), height=620)

    elif view == "Pitch Evidence":
        visual_view = st.radio("Pitch visual", ["Interactive maps", "Report shot view"], horizontal=True, key=f"{key}_visual")
        if visual_view == "Interactive maps":
            left, right = st.columns(2)
            with left:
                section_header("Start Locations", f"Where {readable.lower()} possessions begin")
                render_plotly_visual(polish_plotly_figure(starting_location_map_figure(filtered, f"{readable} start locations")), f"{readable} start locations", f"{key}_start_locations_png")
            with right:
                section_header("Shot Map", f"Shot quality generated from {readable.lower()}")
                render_plotly_visual(polish_plotly_figure(shotmap_figure(filtered, f"{readable} shot map")), f"{readable} shot map", f"{key}_shot_map_png")
        else:
            section_header("Report Shot View", "Static mplsoccer shot-quality figure")
            render_mpl_visual(mplsoccer_shot_figure(filtered, readable), f"{readable} report shot view", f"{key}_report_shot_view_png")

    elif view == "Event Log":
        section_header("Sequence Log", "One row per match_id + possession + team")
        render_analyst_table(sequences, height=430)
        with st.expander("Event-level rows", expanded=False):
            display_cols = [c for c in [
                "Match", "Team", "Taker", "Shooter", "minute", "second", "pass_x", "pass_y",
                "Delivery height", "Shot outcome", "xg", "Occupation_Rating", "Proximity_Rating",
                "Duel_Win_Prob", "OPS_Opponent_Rating", "timestamp",
            ] if c in filtered.columns]
            render_analyst_table(filtered[display_cols], height=620)


def render_hops() -> None:
    df = load_hops_data()
    hero_block("Duel intelligence", "HOPS", "Player and team duel profiles from the HOPS workbook, ranked by rating, percentile, and squad-level depth.")
    if df.empty:
        st.warning("No HOPS rows were found in Data/SWE HOPS.xlsx or Data/CZ HOPS.xlsx.")
        return

    leagues = ["All"] + sorted(df["League"].dropna().astype(str).unique().tolist())
    teams = ["All"] + sorted(df["Team"].dropna().astype(str).unique().tolist())
    league = st.sidebar.selectbox("League", leagues, key="hops_league")
    team = st.sidebar.selectbox("Team", teams, key="hops_team")
    top_n = st.sidebar.slider("Show top / bottom players", min_value=5, max_value=30, value=10, key="hops_top_n")

    filtered = df.copy()
    if league != "All":
        filtered = filtered[filtered["League"] == league].copy()
    if team != "All":
        filtered = filtered[filtered["Team"] == team].copy()

    render_export_controls(filtered, "hops", "HOPS")
    render_filter_summary("HOPS", len(df), len(filtered), [("League", league), ("Team", team), ("Rows", f"Top/bottom {top_n}")])
    if filtered.empty:
        render_empty_filter_state()

    player_count = int(filtered["Player"].nunique())
    team_count = int(filtered["Team"].nunique())
    avg_rating = float(filtered["Rating"].mean()) if not filtered.empty else 0.0
    best_rating = float(filtered["Rating"].max()) if not filtered.empty else 0.0
    elite_count = int((filtered["Tier"] == "Elite").sum()) if "Tier" in filtered.columns else 0
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Players", player_count)
    c2.metric("Teams", team_count)
    c3.metric("Average rating", f"{avg_rating:.3f}")
    c4.metric("Best rating", f"{best_rating:.3f}")
    c5.metric("Elite profiles", elite_count)

    team_summary = (
        filtered.groupby(["League", "Team"], dropna=False)
        .agg(
            Players=("Player", "nunique"),
            Avg_Rating=("Rating", "mean"),
            Median_Rating=("Rating", "median"),
            Best_Rating=("Rating", "max"),
            Elite=("Tier", lambda s: int((s == "Elite").sum())),
            Strong_Plus=("Tier", lambda s: int(s.isin(["Strong", "Elite"]).sum())),
        )
        .reset_index()
    )
    team_summary["Avg_Rating"] = team_summary["Avg_Rating"].round(3)
    team_summary["Median_Rating"] = team_summary["Median_Rating"].round(3)
    team_summary["Best_Rating"] = team_summary["Best_Rating"].round(3)
    team_summary = team_summary.sort_values(["Avg_Rating", "Elite", "Strong_Plus"], ascending=False)
    top_players = filtered.nlargest(top_n, "Rating")[["Player", "Team", "League", "Rating", "Percentile", "Tier"]].copy()
    bottom_players = filtered.nsmallest(top_n, "Rating")[["Player", "Team", "League", "Rating", "Percentile", "Tier"]].copy()

    view = st.radio("View", ["Briefing", "Duel Evidence", "Player Log"], horizontal=True, key="hops_view")
    if view == "Briefing":
        left, right = st.columns([1.15, 1])
        with left:
            section_header("Team Duel Board", "Average rating and high-end profiles by squad")
            render_analyst_table(team_summary, height=410)
        with right:
            section_header("Priority Profiles", f"Best {len(top_players)} in filter")
            render_analyst_table(top_players, height=410)
        section_header("Risk Check", "Lowest ratings in the active filter")
        render_analyst_table(bottom_players, height=330)

    elif view == "Duel Evidence":
        chart_left, chart_right = st.columns(2)
        with chart_left:
            section_header("Top Rating Evidence")
            chart_df = filtered.nlargest(min(15, len(filtered)), "Rating").sort_values("Rating")
            fig = bar_chart(chart_df, x="Rating", y="Player", color="Team", orientation="h")
            fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(fig), "HOPS top rating evidence", "hops_top_rating_evidence_png")
        with chart_right:
            section_header("Rating Distribution")
            hist = histogram_chart(filtered, "Rating", color="Tier", nbins=20)
            hist.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="")
            render_plotly_visual(polish_plotly_figure(hist), "HOPS rating distribution", "hops_rating_distribution_png")

    elif view == "Player Log":
        section_header("Player Log", f"{len(filtered):,} players")
        render_analyst_table(filtered.sort_values("Rating", ascending=False)[["Player", "Team", "League", "Rating", "Percentile", "Tier"]], height=620)


def render_delay() -> None:
    book = load_delay_workbook()
    events = _clean_delay_events(book.get("All_Corners", pd.DataFrame()))
    summary = book.get("Summary", pd.DataFrame()).copy()
    diagnostics = book.get("Diagnostics", pd.DataFrame()).copy()
    skipped = book.get("Skipped_Files", pd.DataFrame()).copy()

    hero_block("Corner timing intelligence", "Delay Analysis", "Workbook-level timing audit for corners: matched clearances/exits, delay bands, match reliability, and diagnostic coverage.")
    if events.empty:
        st.warning("No delay events were found in corner_delays (1).xlsx.")
        return

    leagues = ["All"] + sorted(events["League"].dropna().astype(str).unique().tolist()) if "League" in events.columns else ["All"]
    matches = ["All"] + sorted(events["match"].dropna().astype(str).unique().tolist()) if "match" in events.columns else ["All"]
    periods = ["All"] + sorted(events["period"].dropna().astype(int).astype(str).unique().tolist()) if "period" in events.columns else ["All"]
    out_types = ["All"] + sorted(events["out_event_type"].dropna().astype(str).unique().tolist()) if "out_event_type" in events.columns else ["All"]

    league = st.sidebar.selectbox("League", leagues, key="delay_league")
    match = st.sidebar.selectbox("Match", matches, key="delay_match")
    period = st.sidebar.selectbox("Period", periods, key="delay_period")
    out_type = st.sidebar.selectbox("Exit event", out_types, key="delay_exit")

    filtered = events.copy()
    if league != "All" and "League" in filtered.columns:
        filtered = filtered[filtered["League"].astype(str).eq(league)].copy()
    if match != "All" and "match" in filtered.columns:
        filtered = filtered[filtered["match"].astype(str).eq(match)].copy()
    if period != "All" and "period" in filtered.columns:
        filtered = filtered[filtered["period"].astype("Int64").astype(str).eq(period)].copy()
    if out_type != "All" and "out_event_type" in filtered.columns:
        filtered = filtered[filtered["out_event_type"].astype(str).eq(out_type)].copy()

    if not filtered.empty and "delay_sec" in filtered.columns:
        lo = float(filtered["delay_sec"].min())
        hi = float(filtered["delay_sec"].max())
        full_delay_range = (lo, hi)
        delay_range = st.sidebar.slider("Delay range (seconds)", min_value=lo, max_value=hi, value=(lo, hi), key="delay_range")
        filtered = filtered[filtered["delay_sec"].between(delay_range[0], delay_range[1])].copy()
    else:
        full_delay_range = None
        delay_range = None

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

    view = st.radio("View", ["Briefing", "Timing Evidence", "Audit", "Event Log"], horizontal=True, key="delay_view")
    if view == "Briefing":
        band_summary = (
            filtered.groupby("Delay band", dropna=False)
            .agg(Corners=("delay_sec", "size"), Avg_Delay=("delay_sec", "mean"), Median_Delay=("delay_sec", "median"), Min_Delay=("delay_sec", "min"), Max_Delay=("delay_sec", "max"))
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
        with insight_cols[0]:
            st.markdown(f"<div class='mm-insight-card'>Most common delay band: <strong>{band_summary.sort_values('Corners', ascending=False).iloc[0]['Delay band']}</strong>.</div>", unsafe_allow_html=True)
        with insight_cols[1]:
            st.markdown(f"<div class='mm-insight-card'>Most common exit event: <strong>{out_summary.iloc[0]['out_event_type']}</strong>.</div>", unsafe_allow_html=True)
        with insight_cols[2]:
            st.markdown(f"<div class='mm-insight-card'>Slowest average match in filter: <strong>{match_delay.iloc[0]['match']}</strong>.</div>", unsafe_allow_html=True)
        left, right = st.columns([1, 1])
        with left:
            section_header("Delay Bands", "How long corners take before the matched exit event")
            render_analyst_table(band_summary, height=310)
        with right:
            section_header("Exit Profile", "Matched event type following the corner")
            render_analyst_table(out_summary, height=310)
        section_header("Slowest Match Profiles", "Highest average delay in the active filter")
        render_analyst_table(match_delay.head(30), height=430)

    elif view == "Timing Evidence":
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
            render_analyst_table(summary_view.sort_values("avg_delay_sec", ascending=False) if "avg_delay_sec" in summary_view.columns else summary_view, height=420)
        else:
            st.info("No Summary sheet found.")
        section_header("Diagnostics Sheet", "Coverage checks from source event files")
        render_analyst_table(diagnostics, height=360) if not diagnostics.empty else st.info("No Diagnostics sheet found.")
        if not skipped.empty:
            section_header("Skipped Files", "Files not included in the timing extraction")
            render_analyst_table(skipped, height=260)

    elif view == "Event Log":
        section_header("Matched Corner Event Log", f"{len(filtered):,} rows in the active filter")
        display_cols = [c for c in [
            "match", "period", "out_event_type", "out_value", "gk_outcome",
            "out_time_mmss", "corner_time_mmss", "delay_sec", "Delay band",
            "corner_event_index", "out_event_index",
        ] if c in filtered.columns]
        render_analyst_table(filtered[display_cols], height=620)


if not st.session_state.get("show_playform", False):
    render_landing()
else:
    section = render_single_app_sidebar()
    if section == "Home":
        render_home()
    elif section == "Corners":
        render_corners()
    elif section == "Freekicks":
        render_sequence_page("Freekicks")
    elif section == "Throw-ins":
        render_sequence_page("Throw-ins")
    elif section == "HOPS":
        render_hops()
    elif section == "Delay Analysis":
        render_delay()
