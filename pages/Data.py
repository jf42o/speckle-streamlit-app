import streamlit as st
import pandas as pd
from specklepy.api.credentials import get_default_account

#PAGE CONFIG
st.set_page_config(
    page_title="Your Data",
    page_icon="📊",
    layout = "wide"
)

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

html_code = '''
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400&display=swap">

<style>
body, h1, h2, h3, h4, h5, h6, p, a {
    font-family: 'Public Sans', sans-serif;
}


.container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    flex-direction: column;
    margin-top: -300px; /* Adjust for fixed navbar height */
}

.fixed-nav {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: #1f77b4;
    padding: 5px 20px;
    z-index: 999;
    display: flex;
    align-items: center;
    height: 60px;
    justify-content: space-between;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.left-container, .center-container, .right-container {
    display: flex;
    flex: 1;
    align-items: center;
}

.left-container {
    justify-content: flex-start;
}

.center-container {
    justify-content: center;
}

.right-container {
    justify-content: flex-end;
}

.fixed-nav img {
    height: 30px;
    margin-right: 8px;
}

.fixed-nav h1 {
    color: white;
    margin: 0;
    font-size: 24px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    line-height: 30px;
}

.nav-links a {
    color: inherit;
    text-decoration: none;
    line-height: 30px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    font-size: 18px;
}

.nav-links a {
    color: inherit;
    text-decoration: none;
    line-height: 30px;
}

.nav-links a:hover {
    text-decoration: underline;
}
.centered-flex {
    display: flex;
    justify-content: center;
    flex-grow: 1;
}
.nav-links {
    display: flex;
    gap: 10px;
    color: white;
    align-items: center;
    font-size: 24px;
}
.nav-links a {
    color: inherit;
    text-decoration: none;
    line-height: 30px;
    font-size: 15px;
}
.nav-links a:hover {
    text-decoration: underline;
}
.fixed-nav img {
    height: 30px;
}
.fixed-nav h1 {
    color: white;
    margin: 0;
    font-size: 24px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    line-height: 30px;
}
.centered-flex {
    display: flex;
    justify-content: flex-start;
    flex-grow: 1;
    margin-left: 20px;
}

.custom-login-button {
    background-color: #1f77b4;
    border: none;
    color: white;
    padding: 10px 20px;
    margin-top : 30px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    font-family: 'Public Sans', sans-serif;
    margin: 10px 2px;
    cursor: pointer;
    border-radius: 5px;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23);
}

.custom-login-button img {
    height: 18px;
    vertical-align: middle;
    margin-right: 8px;
}

.custom-login-button:hover {
    background-color: #1a6498;
}

.custom-login-button:active {
    background-color: #1f77b4;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.24);
    trans
}

.middle-text-container {
    display: flex;
    justify-content: center;
    align-items: center; /* Align the text to the top */
    margin-top: 60px; /* Increase margin to 100px below navbar (60px navbar height + 100px) */
    text-align: center;
}

.middle-text {
    font-family: 'Inter', sans-serif; /* Apply the Inter font */
    font-size: 72px;
    font-weight: 900;
    color: #000;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    text-align: center;
}

.gradient-text {
    background-image: linear-gradient(to right, #0077b6, #0096c7, #00b4d8, #48cae4, #90e0ef); /* Add the gradient */
    -webkit-background-clip: text; /* Add webkit background clip to support Safari */
    background-clip: text;
    color: transparent; /* Set the color to transparent */
}
.gradient-text-streamlit {
    background-image: linear-gradient(to right, #f63366, #ff5858, #ff8373, #ffa599, #ffc9bd); /* Add the Streamlit gradient */
}

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap" rel="stylesheet">
</style>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap" rel="stylesheet">

<div class="fixed-nav">
    <div class="left-container">
        <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
        <h1>SpeckleLit</h1>
    </div>
    <div class="center-container"></div>
    <div class="right-container">
        <div class="nav-links">
            <a href="/Data" target="_self">Data</a>
            <a href="/About" target="_self">About</a>
        </div>
    </div>
</div>

'''

st.markdown(html_code, unsafe_allow_html=True)

#session = st.session_state
#session.test = "Test"
#st.write(session.access_code)
st.write(st.session_state["parsed_model_data"])