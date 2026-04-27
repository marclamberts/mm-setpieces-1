from __future__ import annotations

from pathlib import Path
import streamlit as st

_APP_FILE = Path(__file__).resolve()
_UTILS_FILE = _APP_FILE.parent / "mm_setpieces" / "utils.py"
_APP_GLOBALS = globals()
_APP_GLOBALS["__file__"] = str(_UTILS_FILE)
exec(_UTILS_FILE.read_text(), _APP_GLOBALS)
_APP_GLOBALS["__file__"] = str(_APP_FILE)

st.set_page_config(page_title="Michael Mackin Set Piece", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")
inject_app_style()
render_sidebar_menu(
    "Home",
    [
        ("Scope", "Full set-piece desk"),
        ("Filters", "Open a page to view fixed filter values"),
    ],
)

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
            <div class="mm-feature-value">PDF brief</div>
            <div class="mm-feature-label">Staff ready</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_header("Opposition Restart Desks", "Primary event analysis")
cards = [
    (
        "Corners",
        "Corner delivery dossier",
        "Rank teams, takers, target zones, shot value, second-ball patterns, and match-ready delivery maps.",
        "Allsvenskan - Corners 2025.xlsx",
        "pages/1_Corners.py",
        "Open Corners",
    ),
    (
        "Freekicks",
        "Dead-ball origin dossier",
        "Free-kick origins, channel threat, taker tendencies, shooter value, and possession-level outcomes.",
        "SWE SP.xlsx · From Free Kick",
        "pages/2_Freekicks.py",
        "Open Freekicks",
    ),
    (
        "Throw ins",
        "Touchline restart dossier",
        "Territory, side bias, pressure profile, thrower output, and shot creation from throw-in sequences.",
        "SWE SP.xlsx · From Throw In",
        "pages/3_Throw_ins.py",
        "Open Throw ins",
    ),
]

for col, (title, kicker, copy, source, page, button) in zip(st.columns(3), cards):
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
        if st.button(button):
            st.switch_page(page)

section_header("Specialist Scouting Modules", "Player rating model and timing audit")
s1, s2 = st.columns(2)

with s1:
    st.markdown(
        """
        <div class="mm-nav-card">
            <div class="mm-card-kicker">Module · Duel model</div>
            <div class="mm-nav-title">HOPS</div>
            <div class="mm-nav-copy">Aerial/duel strength by player and team, with percentiles, tiers, elite profiles, and weak-side risk checks.</div>
            <div class="mm-tiny">duel_hops_rating_summary.xlsx</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open HOPS"):
        st.switch_page("pages/4_HOPS.py")

with s2:
    st.markdown(
        """
        <div class="mm-nav-card">
            <div class="mm-card-kicker">Module · Timing model</div>
            <div class="mm-nav-title">Delay Analysis</div>
            <div class="mm-nav-copy">Corner timing audit with delay bands, exit events, slow match profiles, and extraction reliability checks.</div>
            <div class="mm-tiny">corner_delays (1).xlsx</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Delay Analysis"):
        st.switch_page("pages/5_Delay.py")

section_header("Workflow", "How to use the app before a match")
st.markdown(
    """
    <div class="mm-workflow-grid">
        <div class="mm-workflow-card">
            <div class="mm-workflow-step">Scout</div>
            <div class="mm-workflow-title">Find the repeatable behaviour</div>
            <div class="mm-workflow-copy">Use origin maps, taker tables, and sequence rankings to separate habit from noise.</div>
        </div>
        <div class="mm-workflow-card">
            <div class="mm-workflow-step">Plan</div>
            <div class="mm-workflow-title">Convert patterns into assignments</div>
            <div class="mm-workflow-copy">Identify who delivers, who attacks, where pressure arrives, and where the second ball lands.</div>
        </div>
        <div class="mm-workflow-card">
            <div class="mm-workflow-step">Report</div>
            <div class="mm-workflow-title">Export the staff brief</div>
            <div class="mm-workflow-copy">Generate a filtered PDF with role labels, insights, and pitch visuals for the match meeting.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Data routing: Corners use Allsvenskan - Corners 2025.xlsx. Freekicks and Throw ins use SWE SP.xlsx filtered by SP_Type.")
