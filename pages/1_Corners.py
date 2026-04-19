
from __future__ import annotations

import streamlit as st

from utils import corner_summary_tables, delivery_map_figure, info_panel, kpi_row, load_corner_data, shotmap_figure, sidebar_filters

st.set_page_config(page_title='Michael Mackin Set Piece | Corners', page_icon='⚽', layout='wide')

st.markdown(
    """
    <style>
        .stApp {background: linear-gradient(180deg, #f8fafc 0%, #f3f6fb 100%);} 
        .page-card {
            background: rgba(255,255,255,0.96);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 22px;
            padding: 1.35rem 1.35rem 1rem 1.35rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
        }
        .mini-title {font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b;}
        .main-title {font-size: 2.3rem; font-weight: 800; color: #0f172a; margin: 0.15rem 0 0.4rem 0;}
        .copy {color: #475569; line-height: 1.6;}
    </style>
    """,
    unsafe_allow_html=True,
)

df = load_corner_data()
filtered = sidebar_filters(df, 'Corners')

st.markdown(
    """
    <div class='page-card'>
        <div class='mini-title'>Allsvenskan 2025 · Corner analysis</div>
        <div class='main-title'>Corners</div>
        <div class='copy'>
            Analyse corner volume, shot generation, delivery profiles, and final delivery locations. The visuals below are driven directly from the uploaded corners dataset.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

info_panel(filtered)
kpi_row(filtered)

team_summary, delivery_mix, outcome_mix = corner_summary_tables(filtered)

st.markdown('### General information')
left, mid, right = st.columns([1.4, 1, 1])
with left:
    st.dataframe(team_summary, use_container_width=True, hide_index=True)
with mid:
    st.dataframe(delivery_mix, use_container_width=True, hide_index=True)
with right:
    st.dataframe(outcome_mix, use_container_width=True, hide_index=True)

map_left, map_right = st.columns(2)
with map_left:
    st.plotly_chart(shotmap_figure(filtered, 'Corner shotmap'), use_container_width=True)
with map_right:
    st.plotly_chart(delivery_map_figure(filtered, 'Corner delivery map'), use_container_width=True)

st.markdown('### Event details')
display_cols = [
    'Match', 'Team', 'Taker', 'Shooter', 'side', 'minute', 'second',
    'inswing_outswing', 'delivery_type', 'shot.outcome.name', 'xg', 'delivery_outcome'
]
st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)
