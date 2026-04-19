import streamlit as st

st.set_page_config(page_title="Set Piece Analysis", layout="wide")

st.title("Michael Mackin Set Piece Dashboard")

st.markdown("### Choose a category")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Corners"):
        st.switch_page("pages/1_Corners.py")

with col2:
    if st.button("Freekicks"):
        st.switch_page("pages/2_Freekicks.py")

with col3:
    if st.button("Throw ins"):
        st.switch_page("pages/3_Throw_ins.py")
