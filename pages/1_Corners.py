import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

st.set_page_config(layout="wide")

st.title("Corners Analysis (StatsBomb 120x80 - Half Pitch)")

@st.cache_data
def load_data():
    return pd.read_excel("Allsvenskan - Corners 2025.xlsx")

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

team = st.sidebar.selectbox("Team", ["All"] + sorted(df['team'].dropna().unique()))
side = st.sidebar.selectbox("Side", ["All", "Left", "Right"])
only_shots = st.sidebar.checkbox("Only corners ending in shot")

if team != "All":
    df = df[df['team'] == team]

if side != "All" and 'side' in df.columns:
    df = df[df['side'] == side]

if only_shots:
    df = df[df['shot_outcome'].notna()]

# Ensure attacking half (StatsBomb uses 120 length)
df = df[df['x'] >= 60]

st.subheader("Shotmap")

shots = df[df['shot_outcome'].notna()]
shots = shots[shots['shot_location_x'] >= 60]

pitch = VerticalPitch(
    pitch_type='statsbomb',
    pitch_length=120,
    pitch_width=80,
    half=True,
    pitch_color='white',
    line_color='#333333'
)

fig, ax = pitch.draw(figsize=(5.5, 7.5))

if not shots.empty:
    pitch.scatter(
        shots['shot_location_x'],
        shots['shot_location_y'],
        s=shots['shot_statsbomb_xg'].fillna(0.05) * 800,
        c='#e63946',
        edgecolors='black',
        ax=ax,
        alpha=0.85
    )

st.pyplot(fig)

st.subheader("Delivery Map")

fig2, ax2 = pitch.draw(figsize=(5.5, 7.5))

if {'x','y','end_x','end_y'}.issubset(df.columns):
    pitch.arrows(
        df['x'], df['y'],
        df['end_x'], df['end_y'],
        width=2,
        color='#457b9d',
        alpha=0.6,
        ax=ax2
    )

st.pyplot(fig2)

st.subheader("Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Corners", len(df))

with col2:
    st.metric("Shots from Corners", len(shots))
