import streamlit as st

st.set_page_config(page_title='Michael Mackin Set Piece', page_icon='⚽', layout='wide')

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);
        }
        .hero-wrap {
            background: linear-gradient(135deg, #ffffff 0%, #f5f8fc 100%);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 2.4rem 2.2rem;
            box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.2rem;
        }
        .eyebrow {
            display: inline-block;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #365c8d;
            background: #eaf2fb;
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 3rem;
            line-height: 1.02;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
        }
        .hero-subtitle {
            font-size: 1.08rem;
            line-height: 1.7;
            color: #475569;
            max-width: 900px;
            margin-top: 0.9rem;
        }
        .section-label {
            font-size: 0.9rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #64748b;
            margin: 1.4rem 0 0.6rem 0;
        }
        .stat-card {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            padding: 1.2rem 1.1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            height: 100%;
        }
        .stat-kicker {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #64748b;
        }
        .stat-value {
            font-size: 1.9rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0.4rem 0 0.2rem 0;
        }
        .stat-text {
            font-size: 0.96rem;
            color: #475569;
            line-height: 1.5;
        }
        .nav-card {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            padding: 1.4rem 1.2rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
            min-height: 220px;
        }
        .nav-title {
            font-size: 1.3rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.4rem;
        }
        .nav-copy {
            color: #475569;
            line-height: 1.6;
            font-size: 0.96rem;
            margin-bottom: 1rem;
        }
        .footer-note {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            padding: 1rem 1.2rem;
            color: #475569;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        div.stButton > button {
            width: 100%;
            border-radius: 14px;
            border: 1px solid #cbd5e1;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            color: #0f172a;
            font-weight: 700;
            padding: 0.8rem 1rem;
        }
        div.stButton > button:hover {
            border-color: #94a3b8;
            color: #0f172a;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
        <div class="eyebrow">Set Piece Analysis Platform</div>
        <h1 class="hero-title">Michael Mackin Set Piece</h1>
        <p class="hero-subtitle">
            A professional set-piece dashboard for exploring attacking patterns, delivery tendencies,
            and shot outcomes across corners, freekicks, and throw ins. Use the pages below to move
            from a high-level overview into detailed visual analysis.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

stat_cols = st.columns(4)
stat_data = [
    ('Modules', '3', 'Corners, Freekicks, and Throw ins in separate analysis environments.'),
    ('Views', '3', 'General information, shotmaps, and delivery visuals on every page.'),
    ('Filters', '6', 'Team, league, sample, side, and in-game timing controls from the sidebar.'),
    ('Workflow', 'Match-ready', 'Built for quick opposition review and repeatable set-piece preparation.'),
]
for col, (label, value, text) in zip(stat_cols, stat_data):
    with col:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-kicker">{label}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-label">Choose analysis module</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-title">Corners</div>
            <div class="nav-copy">
                Review corner routines, side-specific tendencies, delivery zones, and the shot outcomes
                created from corner situations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button('Open Corners', use_container_width=True):
        st.switch_page('pages/1_Corners.py')

with col2:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-title">Freekicks</div>
            <div class="nav-copy">
                Explore direct and indirect freekick patterns, delivery quality, shot creation, and
                timing trends across filtered match samples.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button('Open Freekicks', use_container_width=True):
        st.switch_page('pages/2_Freekicks.py')

with col3:
    st.markdown(
        """
        <div class="nav-card">
            <div class="nav-title">Throw ins</div>
            <div class="nav-copy">
                Analyse throw-in territory, delivery direction, follow-up actions, and resulting shotmaps
                to spot repeatable attacking setups.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button('Open Throw ins', use_container_width=True):
        st.switch_page('pages/3_Throw_ins.py')

st.markdown('')
st.markdown(
    """
    <div class="footer-note">
        <strong>Included analysis controls:</strong> Team, League, Total or Last 10 games, Left or Right side,
        and time in the game. Each module uses the same filter logic for a consistent scouting workflow.
    </div>
    """,
    unsafe_allow_html=True,
)
