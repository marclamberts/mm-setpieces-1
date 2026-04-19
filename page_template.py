from __future__ import annotations

import streamlit as st

from utils import SP_MAP, delivery_figure, info_panel, kpi_row, load_data, shotmap_figure, sidebar_filters, summary_tables


def render_page(label: str) -> None:
    st.set_page_config(page_title=f'Michael Mackin Set Piece | {label}', page_icon='⚽', layout='wide')
    df = load_data()
    page_df = df[df['SP_Type'] == SP_MAP[label]].copy()
    filtered = sidebar_filters(page_df, label)

    st.title(label)
    st.write(f'Analysis page for {label.lower()}.')
    info_panel(filtered)
    kpi_row(filtered)

    st.markdown('---')
    st.subheader('General information')
    team_summary, delivery_mix = summary_tables(filtered)
    left, right = st.columns([2, 1])
    with left:
        st.dataframe(team_summary, use_container_width=True, hide_index=True)
    with right:
        st.dataframe(delivery_mix, use_container_width=True, hide_index=True)

    st.markdown('---')
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(shotmap_figure(filtered, f'{label} shotmap'), use_container_width=True)
    with chart_right:
        st.plotly_chart(delivery_figure(filtered, f'{label} delivery map'), use_container_width=True)

    st.markdown('---')
    st.subheader('Raw events')
    display_cols = [
        'match_id', 'team.name', 'Taker', 'Shooter', 'pass.height.name',
        'shot.outcome.name', 'xg', 'side', 'game_period', 'timestamp'
    ]
    safe_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[safe_cols], use_container_width=True, hide_index=True)
