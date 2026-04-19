from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = Path(__file__).resolve().parent / 'SWE SP.xlsx'
PITCH_LENGTH = 120
PITCH_WIDTH = 80
SIDE_SPLIT = PITCH_WIDTH / 2
SP_MAP = {
    'Corners': 'From Corner',
    'Freekicks': 'From Free Kick',
    'Throw ins': 'From Throw In',
}


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE)

    # Normalize the file to the fields needed by the app.
    df['League'] = df['League'] if 'League' in df.columns else 'Allsvenskan'
    df['minute'] = df['timestamp'].astype(str).str.slice(0, 2).astype(int)
    df['game_period'] = pd.cut(
        df['minute'],
        bins=[-1, 15, 30, 45, 60, 75, 200],
        labels=['0-15', '16-30', '31-45', '46-60', '61-75', '76+'],
    ).astype(str)
    df['side'] = np.where(df['location.pass'].astype(str).str.split(',').str[1].astype(float) <= SIDE_SPLIT, 'Left', 'Right')
    df['is_goal'] = df['shot.outcome.name'].fillna('').eq('Goal')
    df['xg'] = pd.to_numeric(df['shot.statsbomb_xg'], errors='coerce').fillna(0)
    df['shot_x'] = pd.to_numeric(df['shot_x'], errors='coerce')
    df['shot_y'] = pd.to_numeric(df['shot_y'], errors='coerce')

    pass_xy = df['location.pass'].astype(str).str.split(',', expand=True)
    df['pass_x'] = pd.to_numeric(pass_xy[0], errors='coerce')
    df['pass_y'] = pd.to_numeric(pass_xy[1], errors='coerce')

    # Proxy for "last 10 games" because the source file has no match date field.
    latest_match_rank = (
        df[['team.name', 'match_id']]
        .drop_duplicates()
        .sort_values(['team.name', 'match_id'], ascending=[True, False])
    )
    latest_match_rank['match_rank'] = latest_match_rank.groupby('team.name').cumcount() + 1
    df = df.merge(latest_match_rank, on=['team.name', 'match_id'], how='left')

    return df


def sidebar_filters(df: pd.DataFrame, set_piece_label: str) -> pd.DataFrame:
    st.sidebar.header(f'{set_piece_label} filters')
    teams = ['All'] + sorted(df['team.name'].dropna().unique().tolist())
    leagues = ['All'] + sorted(df['League'].dropna().unique().tolist())

    team = st.sidebar.selectbox('Team', teams)
    league = st.sidebar.selectbox('League', leagues)
    sample = st.sidebar.radio('Sample', ['Total', 'Last 10 games'], horizontal=True)
    side = st.sidebar.radio('Side', ['All', 'Left', 'Right'], horizontal=True)
    periods = ['All'] + ['0-15', '16-30', '31-45', '46-60', '61-75', '76+']
    time_in_game = st.sidebar.selectbox('Time in the game', periods)

    filtered = df.copy()
    if team != 'All':
        filtered = filtered[filtered['team.name'] == team]
    if league != 'All':
        filtered = filtered[filtered['League'] == league]
    if sample == 'Last 10 games':
        filtered = filtered[filtered['match_rank'] <= 10]
    if side != 'All':
        filtered = filtered[filtered['side'] == side]
    if time_in_game != 'All':
        filtered = filtered[filtered['game_period'] == time_in_game]

    return filtered


def kpi_row(df: pd.DataFrame) -> None:
    matches = int(df['match_id'].nunique())
    sequences = int(df[['match_id', 'possession', 'team.name']].drop_duplicates().shape[0])
    shots = int(df[['match_id', 'possession', 'shot_x', 'shot_y']].drop_duplicates().shape[0])
    goals = int(df['is_goal'].sum())
    avg_xg = float(df['xg'].mean()) if len(df) else 0.0
    total_xg = float(df['xg'].sum())

    cols = st.columns(6)
    metrics = [
        ('Matches', matches),
        ('Sequences', sequences),
        ('Shots', shots),
        ('Goals', goals),
        ('Avg xG', f'{avg_xg:.3f}'),
        ('Total xG', f'{total_xg:.2f}'),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def draw_pitch(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(range=[0, PITCH_LENGTH], visible=False)
    fig.update_yaxes(range=[0, PITCH_WIDTH], visible=False, scaleanchor='x', scaleratio=1)
    shapes = [
        dict(type='rect', x0=0, y0=0, x1=PITCH_LENGTH, y1=PITCH_WIDTH, line=dict(width=2)),
        dict(type='rect', x0=102, y0=18, x1=120, y1=62, line=dict(width=2)),
        dict(type='rect', x0=114, y0=30, x1=120, y1=50, line=dict(width=2)),
        dict(type='line', x0=0, y0=40, x1=120, y1=40, line=dict(width=1, dash='dot')),
    ]
    fig.update_layout(
        shapes=shapes,
        margin=dict(l=10, r=10, t=40, b=10),
        height=520,
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    return fig


def shotmap_figure(df: pd.DataFrame, title: str) -> go.Figure:
    shots = df[['shot_x', 'shot_y', 'xg', 'shot.outcome.name', 'Shooter', 'team.name']].dropna(subset=['shot_x', 'shot_y']).copy()
    if shots.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return draw_pitch(fig)

    shots['Result'] = np.where(shots['shot.outcome.name'].eq('Goal'), 'Goal', 'Shot')
    fig = px.scatter(
        shots,
        x='shot_x',
        y='shot_y',
        size='xg',
        color='Result',
        hover_data={'Shooter': True, 'team.name': True, 'xg': ':.3f', 'shot_x': False, 'shot_y': False},
        title=title,
    )
    return draw_pitch(fig)


def delivery_figure(df: pd.DataFrame, title: str) -> go.Figure:
    deliveries = df[['pass_x', 'pass_y', 'pass.height.name', 'Taker', 'team.name']].dropna(subset=['pass_x', 'pass_y']).copy()
    if deliveries.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return draw_pitch(fig)

    fig = px.scatter(
        deliveries,
        x='pass_x',
        y='pass_y',
        color='pass.height.name',
        hover_data={'Taker': True, 'team.name': True, 'pass_x': False, 'pass_y': False},
        title=title,
    )
    return draw_pitch(fig)


def summary_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    team_summary = (
        df.groupby('team.name', dropna=False)
        .agg(
            Matches=('match_id', 'nunique'),
            Sequences=('possession', 'nunique'),
            Shots=('shot_x', 'count'),
            Goals=('is_goal', 'sum'),
            Total_xG=('xg', 'sum'),
            Avg_xG=('xg', 'mean'),
        )
        .reset_index()
        .rename(columns={'team.name': 'Team'})
        .sort_values(['Total_xG', 'Goals'], ascending=False)
    )

    delivery_mix = (
        df.groupby('pass.height.name', dropna=False)
        .size()
        .reset_index(name='Count')
        .rename(columns={'pass.height.name': 'Delivery type'})
        .sort_values('Count', ascending=False)
    )
    return team_summary, delivery_mix


def info_panel(df: pd.DataFrame) -> None:
    unique_teams = ', '.join(sorted(df['team.name'].dropna().unique().tolist())[:8])
    st.caption(
        'League is set to Allsvenskan by default because the uploaded file does not contain a dedicated league column. '
        '“Last 10 games” is approximated using the 10 highest match_id values for each team because no match date field is present.'
    )
    if unique_teams:
        st.write(f'Visible teams in current selection include: {unique_teams}')
