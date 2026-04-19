
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = Path(__file__).resolve().parent / 'SWE SP.xlsx'
CORNERS_FILE = Path(__file__).resolve().parent / 'Allsvenskan - Corners 2025.xlsx'
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

    df['League'] = df['League'] if 'League' in df.columns else 'Allsvenskan'
    if 'timestamp' in df.columns:
        df['minute'] = pd.to_numeric(df['timestamp'].astype(str).str.slice(0, 2), errors='coerce').fillna(0).astype(int)
    else:
        df['minute'] = pd.to_numeric(df.get('Minute', 0), errors='coerce').fillna(0).astype(int)
    df['game_period'] = pd.cut(
        df['minute'],
        bins=[-1, 15, 30, 45, 60, 75, 200],
        labels=['0-15', '16-30', '31-45', '46-60', '61-75', '76+'],
    ).astype(str)
    if 'location.pass' in df.columns:
        df['side'] = np.where(df['location.pass'].astype(str).str.split(',').str[1].astype(float) <= SIDE_SPLIT, 'Left', 'Right')
        pass_xy = df['location.pass'].astype(str).str.split(',', expand=True)
        df['pass_x'] = pd.to_numeric(pass_xy[0], errors='coerce')
        df['pass_y'] = pd.to_numeric(pass_xy[1], errors='coerce')
    else:
        df['side'] = 'Unknown'
        df['pass_x'] = np.nan
        df['pass_y'] = np.nan
    df['is_goal'] = df['shot.outcome.name'].fillna('').eq('Goal') if 'shot.outcome.name' in df.columns else False
    df['xg'] = pd.to_numeric(df.get('shot.statsbomb_xg', 0), errors='coerce').fillna(0)
    df['shot_x'] = pd.to_numeric(df.get('shot_x'), errors='coerce')
    df['shot_y'] = pd.to_numeric(df.get('shot_y'), errors='coerce')

    team_col = 'team.name' if 'team.name' in df.columns else 'pass_team_name'
    latest_match_rank = (
        df[[team_col, 'match_id']]
        .drop_duplicates()
        .sort_values([team_col, 'match_id'], ascending=[True, False])
    )
    latest_match_rank['match_rank'] = latest_match_rank.groupby(team_col).cumcount() + 1
    df = df.merge(latest_match_rank, on=[team_col, 'match_id'], how='left')

    return df


@st.cache_data(show_spinner=False)
def load_corner_data() -> pd.DataFrame:
    df = pd.read_excel(CORNERS_FILE)
    df['League'] = 'Allsvenskan'
    df['Team'] = df['pass_team_name']
    df['minute'] = pd.to_numeric(df['Minute'], errors='coerce').fillna(0).astype(int)
    df['second'] = pd.to_numeric(df['Second'], errors='coerce').fillna(0).astype(int)
    df['game_period'] = pd.cut(
        df['minute'],
        bins=[-1, 15, 30, 45, 60, 75, 200],
        labels=['0-15', '16-30', '31-45', '46-60', '61-75', '76+'],
    ).astype(str)
    df['side'] = np.where(pd.to_numeric(df['pass_location_y'], errors='coerce') >= SIDE_SPLIT, 'Left', 'Right')
    df['is_shot'] = df['shot_location_x'].notna() & df['shot_location_y'].notna()
    df['is_goal'] = df['shot.outcome.name'].fillna('').eq('Goal')
    df['xg'] = pd.to_numeric(df['shot.statsbomb_xg'], errors='coerce').fillna(0)
    df['delivery_end_x'] = pd.to_numeric(df['pass_end_location_x'], errors='coerce')
    df['delivery_end_y'] = pd.to_numeric(df['pass_end_location_y'], errors='coerce')
    df['shot_x'] = pd.to_numeric(df['shot_location_x'], errors='coerce')
    df['shot_y'] = pd.to_numeric(df['shot_location_y'], errors='coerce')
    df['inswing_outswing'] = df['pass.technique.name'].fillna('Unknown')
    df['delivery_type'] = df['pass.height.name'].fillna('Unknown')
    df['delivery_outcome'] = df['SP_outcome'].fillna('Unknown')
    latest_match_rank = (
        df[['Team', 'match_id']]
        .drop_duplicates()
        .sort_values(['Team', 'match_id'], ascending=[True, False])
    )
    latest_match_rank['match_rank'] = latest_match_rank.groupby('Team').cumcount() + 1
    df = df.merge(latest_match_rank, on=['Team', 'match_id'], how='left')
    return df


def sidebar_filters(df: pd.DataFrame, set_piece_label: str) -> pd.DataFrame:
    st.sidebar.header(f'{set_piece_label} filters')
    team_col = 'team.name' if 'team.name' in df.columns else 'Team'
    teams = ['All'] + sorted(df[team_col].dropna().unique().tolist())
    leagues = ['All'] + sorted(df['League'].dropna().unique().tolist())

    team = st.sidebar.selectbox('Team', teams)
    league = st.sidebar.selectbox('League', leagues)
    sample = st.sidebar.radio('Sample', ['Total', 'Last 10 games'], horizontal=True)
    side = st.sidebar.radio('Side', ['All', 'Left', 'Right'], horizontal=True)
    periods = ['All'] + ['0-15', '16-30', '31-45', '46-60', '61-75', '76+']
    time_in_game = st.sidebar.selectbox('Time in the game', periods)

    filtered = df.copy()
    if team != 'All':
        filtered = filtered[filtered[team_col] == team]
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
    team_col = 'team.name' if 'team.name' in df.columns else 'Team'
    shot_col = 'shot_x' if 'shot_x' in df.columns else 'shot_location_x'
    matches = int(df['match_id'].nunique())
    sequences = int(df[['match_id', 'possession', team_col]].drop_duplicates().shape[0])
    shots = int(df[shot_col].notna().sum())
    goals = int(df['is_goal'].sum()) if 'is_goal' in df.columns else 0
    avg_xg = float(df['xg'].mean()) if len(df) and 'xg' in df.columns else 0.0
    total_xg = float(df['xg'].sum()) if 'xg' in df.columns else 0.0

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


def draw_pitch(fig: go.Figure, title: str = '') -> go.Figure:
    fig.update_xaxes(range=[0, PITCH_LENGTH], visible=False)
    fig.update_yaxes(range=[0, PITCH_WIDTH], visible=False, scaleanchor='x', scaleratio=1)
    shapes = [
        dict(type='rect', x0=0, y0=0, x1=PITCH_LENGTH, y1=PITCH_WIDTH, line=dict(width=2, color='#1e293b')),
        dict(type='rect', x0=102, y0=18, x1=120, y1=62, line=dict(width=1.5, color='#1e293b')),
        dict(type='rect', x0=114, y0=30, x1=120, y1=50, line=dict(width=1.5, color='#1e293b')),
        dict(type='line', x0=108, y0=0, x1=108, y1=80, line=dict(width=1, dash='dot', color='#94a3b8')),
    ]
    fig.update_layout(
        title=title,
        shapes=shapes,
        margin=dict(l=10, r=10, t=48, b=10),
        height=520,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend_title_text='',
    )
    return fig


def shotmap_figure(df: pd.DataFrame, title: str) -> go.Figure:
    shots = df[df['shot_x'].notna() & df['shot_y'].notna()].copy()
    fig = go.Figure()
    if shots.empty:
        fig.add_annotation(text='No shots for current filter', x=60, y=40, showarrow=False, font=dict(size=18, color='#64748b'))
        return draw_pitch(fig, title)

    shots['Result'] = np.where(shots['shot.outcome.name'].eq('Goal'), 'Goal', 'Shot')
    color_map = {'Goal': '#16a34a', 'Shot': '#2563eb'}
    for result in ['Shot', 'Goal']:
        part = shots[shots['Result'] == result]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part['shot_x'],
                y=part['shot_y'],
                mode='markers',
                name=result,
                marker=dict(size=np.clip(part['xg'].fillna(0)*90 + 10, 10, 40), color=color_map[result], opacity=0.72, line=dict(width=1, color='white')),
                customdata=np.stack([
                    part['Shooter'].fillna('Unknown'),
                    part['shot.outcome.name'].fillna('Unknown'),
                    part['xg'].round(3),
                    part['Match'].fillna('Unknown')
                ], axis=1),
                hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]}<br>%{customdata[3]}<extra></extra>'
            )
        )
    return draw_pitch(fig, title)


def delivery_map_figure(df: pd.DataFrame, title: str) -> go.Figure:
    deliveries = df[df['delivery_end_x'].notna() & df['delivery_end_y'].notna()].copy()
    fig = go.Figure()
    if deliveries.empty:
        fig.add_annotation(text='No deliveries for current filter', x=60, y=40, showarrow=False, font=dict(size=18, color='#64748b'))
        return draw_pitch(fig, title)

    sample = deliveries.copy()
    if len(sample) > 300:
        sample = sample.sample(300, random_state=7)

    color_map = {'Inswinging': '#2563eb', 'Outswinging': '#f59e0b', 'Unknown': '#94a3b8'}
    for tech, part in sample.groupby('inswing_outswing'):
        color = color_map.get(tech, '#7c3aed')
        fig.add_trace(
            go.Scatter(
                x=part['delivery_end_x'],
                y=part['delivery_end_y'],
                mode='markers',
                name=tech,
                marker=dict(size=10, color=color, opacity=0.75, line=dict(width=0.5, color='white')),
                customdata=np.stack([
                    part['Taker'].fillna('Unknown'),
                    part['delivery_type'].fillna('Unknown'),
                    part['Match'].fillna('Unknown')
                ], axis=1),
                hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>'
            )
        )
        for _, row in part.iterrows():
            fig.add_annotation(
                x=row['delivery_end_x'], y=row['delivery_end_y'],
                ax=row['pass_location_x'], ay=row['pass_location_y'],
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=color,
                opacity=0.28,
            )
    return draw_pitch(fig, title)


def corner_summary_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    team_summary = (
        df.groupby('Team', dropna=False)
        .agg(
            Matches=('match_id', 'nunique'),
            Corners=('possession', 'nunique'),
            Shots=('is_shot', 'sum'),
            Goals=('is_goal', 'sum'),
            Total_xG=('xg', 'sum'),
            Avg_xG=('xg', 'mean'),
        )
        .reset_index()
        .sort_values(['Total_xG', 'Goals', 'Shots'], ascending=False)
    )
    delivery_mix = (
        df.groupby(['inswing_outswing', 'delivery_type'], dropna=False)
        .size()
        .reset_index(name='Count')
        .sort_values('Count', ascending=False)
        .rename(columns={'inswing_outswing': 'Technique', 'delivery_type': 'Height'})
    )
    outcome_mix = (
        df.groupby('delivery_outcome', dropna=False)
        .size()
        .reset_index(name='Count')
        .sort_values('Count', ascending=False)
        .rename(columns={'delivery_outcome': 'Outcome'})
    )
    return team_summary, delivery_mix, outcome_mix


def info_panel(df: pd.DataFrame) -> None:
    team_col = 'team.name' if 'team.name' in df.columns else 'Team'
    unique_teams = ', '.join(sorted(df[team_col].dropna().unique().tolist())[:8])
    st.caption(
        'League is set to Allsvenskan by default. “Last 10 games” is approximated using the 10 highest match_id values per team because no explicit match date field is present.'
    )
    if unique_teams:
        st.write(f'Visible teams in current selection include: {unique_teams}')
