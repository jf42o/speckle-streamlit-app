import streamlit as st
from specklepy.api.credentials import get_default_account

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

#session = st.session_state
#st.write(session.test)