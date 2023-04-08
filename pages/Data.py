import streamlit as st
import pandas as pd
import specklepy

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

session = st.session_state
session.test = "Test"
st.write(session.access_code)