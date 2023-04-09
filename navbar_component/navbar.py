import streamlit as st
from streamlit.components.v1 import declare_component, html

def Navbar(access_code: str, key=None):
    component_value = html(
        """
        <div class="fixed-nav">
            <div class="left-container">
                <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
                <h1>SpeckleLit</h1>
            </div>
            <div class="center-container"></div>
            <div class="right-container">
                <div class="nav-links">
                    <a href="#" data-href="Home" class="nav-link">Home</a>
                    <a href="#" data-href="Data" class="nav-link">Data</a>
                    <a href="#" data-href="About" class="nav-link">About</a>
                </div>
            </div>
        </div>
        <script>
            function handleClick(event) {
                event.preventDefault();
                let page = event.target.getAttribute("data-href");
                Streamlit.setComponentValue(page);
            }

            const links = document.querySelectorAll(".nav-link");
            for (let i = 0; i < links.length; i++) {
                links[i].addEventListener("click", handleClick);
            }
        </script>
        """,
        width=None,
        height=None,
        scrolling=False,
        key=key,
    )
    return component_value
