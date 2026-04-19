import streamlit as st

st.set_page_config(page_title='Michael Mackin Set Piece', page_icon='⚽', layout='wide')

st.title('Michael Mackin Set Piece')
st.subheader('Set-piece landing page')
st.write(
    'Use the buttons below to explore Corners, Freekicks, and Throw ins. '
    'Each section includes general information, shotmaps, and delivery visuals with filters in the left sidebar.'
)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button('Corners', use_container_width=True):
        st.switch_page('pages/1_Corners.py')
with col2:
    if st.button('Freekicks', use_container_width=True):
        st.switch_page('pages/2_Freekicks.py')
with col3:
    if st.button('Throw ins', use_container_width=True):
        st.switch_page('pages/3_Throw_ins.py')

st.markdown('---')
st.markdown(
    '''
    ### What you can filter
    - Team
    - League
    - Total or last 10 games
    - Left or right side
    - Time in the game
    '''
)
