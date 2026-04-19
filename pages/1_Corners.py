import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

st.set_page_config(layout="wide")
st.title("Corners Analysis")

@st.cache_data
def load_data():
    return pd.read_excel("Allsvenskan - Corners 2025.xlsx")

df = load_data()

st.sidebar.header("Filters")

team = st.sidebar.selectbox("Team", ["All"] + sorted(df['team'].dropna().unique()))
only_shots = st.sidebar.checkbox("Only corners ending in shot")

if team != "All":
    df = df[df['team'] == team]

if only_shots:
    df = df[df['shot_outcome'].notna()]

df = df[df['x'] >= 60]

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

st.subheader("Shotmap")
fig, ax = pitch.draw(figsize=(5.5,7.5))

if not shots.empty:
    pitch.scatter(
        shots['shot_location_x'],
        shots['shot_location_y'],
        s=shots['shot_statsbomb_xg'].fillna(0.05)*800,
        c='red',
        edgecolors='black',
        ax=ax
    )

st.pyplot(fig)

st.subheader("Delivery Map")
fig2, ax2 = pitch.draw(figsize=(5.5,7.5))

pitch.arrows(df['x'], df['y'], df['end_x'], df['end_y'], ax=ax2)

st.pyplot(fig2)
