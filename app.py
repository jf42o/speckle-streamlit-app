#IMPORT LIBRARIES
import requests
import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode, JsCode
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.api.resources.stream import Stream
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.other import RenderMaterial
from specklepy.api import operations
from streamlit_extras.switch_page_button import switch_page
from specklepy.api.credentials import get_default_account
from streamlit_javascript import st_javascript

#toggle between local / redirection from speckleserver to app
LOCAL = False
UPDATE = True


def getBranches(item):
	client, stream = item
	bList = client.branch.list(stream.id)
	branches = []
	for b in bList:
		branches.append(client.branch.get(stream.id, b.name))
	return branches

def getStreams(client):
    return client.stream.list()

def getCommits(branch):
    return branch.commits.items

def getObject(client, stream, commit):
    transport = ServerTransport(stream.id, client)
    last_obj_id = commit.referencedObject
    return operations.receive(obj_id=last_obj_id, remote_transport=transport)

def parse_and_update_model(commit_data, categories, params_to_search):
    result = []
    for cat in categories:
        category_elements = commit_data[cat]
        for element in category_elements:
            # Apply parameter updates
            parameters = element["parameters"].get_member_names()
            #parse metadata, so parameters that are not hidden unter the parameters Object (BUILT_IN_PARAMETERS)
            dict = {'ElementID': element["elementId"], 'ID' : element["id"], 'Familientyp' : element["type"], 'Kategorie' : element["category"], 'Ebene' : element["level"]["name"]}
            for param in params_to_search:
                dict[param] = None
                for parameter in parameters:
                    try:
                        key = element["parameters"][parameter]["name"]
                        if key == param:
                            dict[key] = element["parameters"][parameter]["value"]
                            break
                    except:
                        continue
            result.append(dict)
    return pd.DataFrame(result)

import pandas as pd

def update_speckle_model(edited_dataframe, commit_data, categories, params_to_search, upd=UPDATE):
    # Convert the edited dataframe back to a list of dictionaries
    edited_data = edited_dataframe.to_dict(orient='records')

    # Iterate through the categories and commit_data
    for cat in categories:
        category_elements = commit_data[cat]
        for element in category_elements:
            # Find the corresponding record in the edited_data
            record = next((record for record in edited_data if record['ElementID'] == element['elementId'] and record['ID'] == element['id']), None)

            if record:
                # Apply parameter updates
                parameters = element["parameters"].get_member_names()

                for param in params_to_search:
                    for parameter in parameters:
                        try:
                            key = element["parameters"][parameter]["name"]
                            if key == param:
                                # Update the parameter value in the model based on the edited dataframe
                                if upd:
                                    element["parameters"][parameter]["value"] = record[key]
                                break
                        except:
                            continue
    return commit_data

appID = st.secrets["appID"]
appSecret = st.secrets["appSecret"]

#PAGE CONFIG
st.set_page_config(
    page_title="SpeckleLit",
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

#Hide the Sidebar

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
           display: none;
        }
    </style>
""", unsafe_allow_html=True)



#navbar
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


<div class="middle-text-container">
    <h1 class="middle-text">Make sense from your <span class="gradient-text">Speckle Data</span>. SpeckleLit.</h1>
</div>

'''


st.markdown(html_code, unsafe_allow_html=True)


#Authentification#

#----------------------------------------------------------------------------------------------------------#

if not LOCAL:
    if 'access_code' not in st.session_state:
        st.session_state['access_code'] = None
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    if 'refresh_token' not in st.session_state:
        st.session_state['refresh_token'] = None
    try:
        access_code = st.experimental_get_query_params()['access_code'][0]
        st.session_state['access_code'] = access_code
    except:
        access_code = None
        st.session_state['access_code'] = None

    token = st.session_state['token']
    refresh_token = st.session_state['refresh_token']

    if not refresh_token:
        if not access_code:
            # Verify the app with the challenge
            verify_url="https://speckle.xyz/authn/verify/"+appID+"/"+st.secrets["challenge"]
            html_code = (f"""
                        <div class="container">
                            <button class="custom-login-button">
                                <a href="{verify_url}" style="color: inherit; text-decoration: none;">
                                    <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
                                    Login to Speckle
                                </a>
                            </button>
                        </div>
                        """
                )
            st.markdown(html_code, unsafe_allow_html=True)

        else:
            response = requests.post(
                    url=f"https://speckle.xyz/auth/token",
                    json={
                        "appSecret": appSecret,
                        "appId": appID,
                        "accessCode": access_code,
                        "challenge": st.secrets["challenge"],
                    },
                )
            if (response.status_code == 200):
                token = response.json()['token']
                refresh_token = response.json()['refreshToken']
                st.session_state['token'] = token
                st.session_state['refresh_token'] = refresh_token
            else:
                st.write("Error occurred : " ,response.status_code, response.text)

    streams = None
    if st.session_state['refresh_token']:
        account = get_account_from_token("speckle.xyz", token)
        client = SpeckleClient(host="speckle.xyz")
        client.authenticate_with_token(token)
        try:
            streams = getStreams(client)
        except:
            streams = None
        if not isinstance(streams, list):
            account = get_account_from_token("speckle.xyz", refresh_token)
            client = SpeckleClient(host="speckle.xyz")
            client.authenticate_with_token(refresh_token)
            try:
                streams = getStreams(client)
            except:
                streams = None
    #--------------------------------------------------------------------------------------------------------------------#
    
    #Selection of Streams#

    navbar_html = """
    <div class="fixed-nav">
        <div class="left-container">
            <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
            <h1>SpeckleLit</h1>
        </div>
        <div class="center-container"></div>
        <div class="right-container">
            <div class="nav-links">
                <a href="#" data-page="home">Home</a>
                <a href="#" data-page="data">Data</a>
                <a href="#" data-page="about">About</a>
            </div>
        </div>
    </div>
    """
    
    st.markdown(navbar_html, unsafe_allow_html=True)    
   
    js_code = ("""
    
    const navLinks = document.querySelectorAll(".nav-links");

    """)

    width = st_javascript(js_code)
    st.markdown(width)

    query_params = st.experimental_get_query_params()

    if isinstance(streams, list):

        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

            .stSelectbox {
                width: 100%;
            }
            .stSelectbox .st-ax,
            .stSelectbox .st-cq,
            .stSelectbox .st-d5,
            .stSelectbox .st-cs,
            .stSelectbox .st-ay,
            .stSelectbox .st-ce,
            .stSelectbox .st-ck {
                background-color: #1f77b4 !important;
                color: white !important;
                border-radius: 5px !important;
                padding: 5px !important;
                margin-bottom: 10px !important;
            }
            .stSelectbox .st-c7,
            .stSelectbox .st-cd {
                color: white !important;
            }
            .stSelectbox .st-bs,
            .stSelectbox .st-d3 {
                fill: white !important;
            }
            .stSelectbox .st-b3,
            .stSelectbox .st-d0 {
                border: none !important;
            }
            .stSelectbox .st-bf,
            .stSelectbox .st-ce {
                padding: 0 !important;
            }
            .stSelectbox .st-cg,
            .stSelectbox .st-ch,
            .stSelectbox .st-ci,
            .stSelectbox .st-cj {
                border: none !important;
            }
            .stSelectbox .st-b5,
            .stSelectbox .st-cl {
                border-radius: 5px !important;
            }
            .stSelectbox .st-cn,
            .stSelectbox .st-co {
                box-shadow: none !important;
            }
            .stSelectbox .st-d2 {
                transition: all 0.3s !important;
            }
            .stSelectbox:hover .st-d2 {
                transform: rotate(180deg) !important;
            }
            .stSelectbox label {
                font-family: 'Inter', sans-serif !important;
                color: #1f77b4 !important;
            }
        </style>
        """, unsafe_allow_html=True)

        stream_names = ["Select a stream"]
        for aStream in streams:
            stream_names.append(aStream.name)

        col1, col2, col3 = st.columns(3)

        option = col1.selectbox(
            'Select your stream',
            (stream_names))

        if option != "Select your stream":
            stream = streams[stream_names.index(option)-1]
            branches = getBranches([client, stream])
            branch_names = ["Select a branch"]
            for aBranch in branches:
                branch_names.append(aBranch.name)
            option = col2.selectbox(
                'Select a branch',
                (branch_names))
            if option != "Select a branch":
                branch = branches[branch_names.index(option)-1]
                commits = getCommits(branch)
                commit_names = ["Select a commit"]
                for aCommit in commits:
                    commit_names.append(str(aCommit.id) + ": " + aCommit.message)
                option = col3.selectbox('Select a commit', (commit_names))
                if option != "Select a commit":
                    commit = commits[commit_names.index(option)-1]

                    #change host, if not the public speckle.xyz"
                    commit_url = "https://speckle.xyz/streams/" + stream.id + "/commits/" + commit.id

                    def commit_url_to_speckle_url(commit_url):
                        # Extract stream id and commit id from the commit url
                        stream_id = commit_url.split('/')[4]
                        commit_id = commit_url.split('/')[6]
                        
                        # Build the speckle url
                        url = f"https://speckle.xyz/embed?stream={stream_id}&commit={commit_id}&transparent=true"
                        return url
                    
                    speckle_url = commit_url_to_speckle_url(commit_url)
                    commit_data = getObject(client,stream,commit)

                    if 'parsed_model_data' not in st.session_state:
                        st.session_state['parsed_model_data'] = None

                    col1, col2 = st.columns(2)

                    with col1:
                        
                        if st.session_state.current_page == "Data":
                            switch_page("Data")


                        categories = ["@Wände", "@Geschossdecken"]
                        params_to_search = ["IMP_Disziplin", "IMP_Bauteil"]

                        # Parse the model only if it's not already parsed
                        if st.session_state['parsed_model_data'] is None:
                            st.session_state['parsed_model_data'] = parse_and_update_model(commit_data, categories, params_to_search)

                        ##FUNCTION for generating speckle url
                        def generate_speckle_url(commit_url, ids):
                            ids_string = ','.join([f'"{id}"' for id in ids])
                            #transparent = "&transparent=false"
                            url = f"{commit_url}&filter={{\"isolatedIds\":[{ids_string}]}}"
                            return url 

                        if 'selected_rows' not in st.session_state:
                            st.session_state.selected_rows = None
                        
                        st.session_state["speckle_url"] = commit_url


                        custom_css_aggrid = {
                            ".ag-row-hover": { "background-color": "#3a9ac9 !important"},
                            ".ag-header-cell-label": {"color" : "white",
                                                    "background-color" : "#3a9ac9",
                                                        "border-radius" : "5px",
                                                        "padding" : "4px 8px"},
                            ".ag-row" : { "background-color" : "white", "border-radius": "5px"},
                            ".ag-row:nth-child(odd)" : {"background-color" : "#f0f5f9"},
                            ".ag-row-selected": {"background-color": "blue !important",
                                                "color": "white !important"}
                        }
                        
                        
                        gb = GridOptionsBuilder.from_dataframe(st.session_state['parsed_model_data'])
                        gb.configure_default_column(editable=True, groupable=True)
                        gb.configure_pagination(enabled=True)
                        gb.configure_selection(selection_mode="multiple", use_checkbox=True, groupSelectsChildren="Group checkbox select children")
                        gb.configure_side_bar()
                        gridoptions = gb.build()

                        grid_return = AgGrid(
                            st.session_state['parsed_model_data'],
                            gridOptions=gridoptions,
                            update_mode=GridUpdateMode.MANUAL,
                            data_return_mode=DataReturnMode.FILTERED,
                            reload_data=True,
                            custom_css=custom_css_aggrid,
                            allow_unsafe_jscode=True,
                            height=600)
                
                        sel_rows = grid_return["data"]
                        ids = list(sel_rows["ID"])
                        st.session_state["speckle_url"] =  generate_speckle_url(speckle_url,ids) #speckle_url 
                        edited_data_mid = grid_return["data"]
                        #st.write(edited_data)

                        grid_return_filtered = AgGrid(edited_data_mid,
                                                    gridOptions=gridoptions,
                                                    update_mode=GridUpdateMode.MANUAL,
                                                    data_return_mode=DataReturnMode.FILTERED,
                                                    reload_data=True,
                                                    custom_css = custom_css_aggrid,
                                                    allow_unsafe_jscode=True,
                                                    height=200
                                        )
                        if st.button("Commit Changes"):
                            edited_data = grid_return_filtered["data"]
                            updated = update_speckle_model(edited_data, commit_data, categories, params_to_search, upd=UPDATE)
                            transport = ServerTransport(stream.id, client)
                            new_object_id = operations.send(base=updated, transports=transport)

                            # Create a new commit on the stream with the updated object
                            new_commit_id = client.commit.create(
                                stream_id=stream.id,
                                object_id=new_object_id,
                                message="Updated parameter values using SpeckleLit",
                            )


                with col2:
                    #st.write(st.session_state["speckle_url"])
                    st.components.v1.iframe(src=st.session_state["speckle_url"],width=750,height=750)




else:
    col1, col2 = st.columns(2)

    commit_url = "https://speckle.xyz/streams/89ad038e05/commits/a914527708"

    def commit_url_to_speckle_url(commit_url):
        # Extract stream id and commit id from the commit url
        stream_id = commit_url.split('/')[4]
        commit_id = commit_url.split('/')[6]
        
        # Build the speckle url
        url = f"https://speckle.xyz/embed?stream={stream_id}&commit={commit_id}&transparent=true"
        return url
    
    speckle_url = commit_url_to_speckle_url(commit_url)
    wrapper = StreamWrapper(commit_url)
    client = wrapper.get_client()
    account = get_default_account()
    client.authenticate_with_account(account)

    if 'parsed_model_data' not in st.session_state:
        st.session_state['parsed_model_data'] = None

    with col1:

        commit = client.commit.get(wrapper.stream_id, wrapper.commit_id)
        obj_id = commit.referencedObject
        commit_data = operations.receive(obj_id, wrapper.get_transport())

        categories = ["@Wände", "@Geschossdecken"]
        params_to_search = ["IMP_Disziplin", "IMP_Bauteil"]

        # Parse the model only if it's not already parsed
        if st.session_state['parsed_model_data'] is None:
            st.session_state['parsed_model_data'] = parse_and_update_model(commit_data, categories, params_to_search)

        ##FUNCTION for generating speckle url
        def generate_speckle_url(commit_url, ids):
            ids_string = ','.join([f'"{id}"' for id in ids])
            #transparent = "&transparent=false"
            url = f"{commit_url}&filter={{\"isolatedIds\":[{ids_string}]}}"
            return url 

        if 'selected_rows' not in st.session_state:
            st.session_state.selected_rows = None
        
        st.session_state["speckle_url"] = commit_url


        custom_css_aggrid = {
            ".ag-row-hover": { "background-color": "#3a9ac9 !important"},
            ".ag-header-cell-label": {"color" : "white",
                                      "background-color" : "#3a9ac9",
                                        "border-radius" : "5px",
                                        "padding" : "4px 8px"},
            ".ag-row" : { "background-color" : "white", "border-radius": "5px"},
            ".ag-row:nth-child(odd)" : {"background-color" : "#f0f5f9"},
            ".ag-row-selected": {"background-color": "blue !important",
                                "color": "white !important"}
        }
        
        
        gb = GridOptionsBuilder.from_dataframe(st.session_state['parsed_model_data'])
        gb.configure_default_column(editable=True, groupable=True)
        gb.configure_pagination(enabled=True)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True, groupSelectsChildren="Group checkbox select children")
        gb.configure_side_bar()
        gridoptions = gb.build()

        grid_return = AgGrid(
            st.session_state['parsed_model_data'],
            gridOptions=gridoptions,
            update_mode=GridUpdateMode.MANUAL,
            data_return_mode=DataReturnMode.FILTERED,
            reload_data=True,
            custom_css=custom_css_aggrid,
            allow_unsafe_jscode=True,
            height=600)
   
        sel_rows = grid_return["data"]
        ids = list(sel_rows["ID"])
        st.session_state["speckle_url"] =  generate_speckle_url(speckle_url,ids) #speckle_url 
        edited_data_mid = grid_return["data"]
        #st.write(edited_data)

        grid_return_filtered = AgGrid(edited_data_mid,
                                      gridOptions=gridoptions,
                                      update_mode=GridUpdateMode.MANUAL,
                                      data_return_mode=DataReturnMode.FILTERED,
                                      reload_data=True,
                                      custom_css = custom_css_aggrid,
                                      allow_unsafe_jscode=True,
                                      height=200
                        )
        if st.button("Commit Changes"):
            edited_data = grid_return_filtered["data"]
            updated = update_speckle_model(edited_data, commit_data, categories, params_to_search, upd=UPDATE)
            new_object_id = operations.send(base=updated, transports=wrapper.get_transport())

            # Create a new commit on the stream with the updated object
            new_commit_id = client.commit.create(
                stream_id=wrapper.stream_id,
                object_id=new_object_id,
                message="Updated parameter values using SpeckleLit",
            )


    with col2:
        #st.write(st.session_state["speckle_url"])
        st.components.v1.iframe(src=st.session_state["speckle_url"],width=750,height=750)
