import streamlit as st
import pandas as pd
from specklepy.api.credentials import get_default_account

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

#session = st.session_state
#session.test = "Test"
#st.write(session.access_code)
st.write(st.session_state["parsed_model_data"])