import requests
import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode, JsCode
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.api import operations
from specklepy.api.credentials import get_default_account
from st_on_hover_tabs import on_hover_tabs
from utils import getBranches, getStreams, getCommits, getObject, parse_and_update_model, update_speckle_model, inject_css

#toggle between local / redirection from speckleserver to app
LOCAL = False
UPDATE = True

def login():

    appID = st.secrets["appID"]
    appSecret = st.secrets["appSecret"]

    inject_css('./style/hide_streamlit_style.css')
    inject_css('./style/style_header.css')
    #navbar
    st.markdown('''
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400&display=swap">
    <div class="fixed-nav">
    <div class="left-container">
        <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
        <h1>SpeckleLit</h1>
    </div>
    ''',unsafe_allow_html=True)


    middle_text = st.markdown( """
    <div class="middle-text-container">
        <h1 class="middle-text">Make sense from your <span class="gradient-text">Speckle Data</span>. SpeckleLit.</h1>
    </div>

    """,unsafe_allow_html=True)

    #Authentification#

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
                st.session_state.client = client
    
def edit():
    inject_css('./style/hide_streamlit_style.css')
    inject_css('./style/style_header.css')

    #navbar
    st.markdown('''

    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400&display=swap">
    <div class="fixed-nav">
    <div class="left-container">
        <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
        <h1>SpeckleLit</h1>
    </div>
    ''',unsafe_allow_html=True)

    client = st.session_state.client
    st.write(client.username)

    try:
        streams = getStreams(st.session_state.client)
    except:
        streams = None
    if not isinstance(streams, list):
        account = get_account_from_token("speckle.xyz", st.session_state.refresh_token)
        client = SpeckleClient(host="speckle.xyz")
        client.authenticate_with_token(st.session_state.refresh_token)
        try:
            streams = getStreams(client)
        except:
            streams = None

    if isinstance(streams, list):
        
        st.markdown('<style>' + open('./style/style_selectbox.css').read() + '</style>', unsafe_allow_html=True)
        
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
    elif LOCAL:
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

def data():

    inject_css('./style/hide_streamlit_style.css')
    inject_css('./style/style_header.css')
    #navbar
    st.markdown('''

    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400&display=swap">
    <div class="fixed-nav">
    <div class="left-container">
        <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
        <h1>SpeckleLit</h1>
    </div>
    ''',unsafe_allow_html=True)


    st.dataframe(st.session_state.parsed_model_data)

def about():

    inject_css('./style/hide_streamlit_style.css')
    inject_css('./style/style_header.css')

    #navbar
    st.markdown('''

    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400&display=swap">
    <div class="fixed-nav">
    <div class="left-container">
        <img src="https://speckle.systems/content/images/2021/02/logo_big.png" alt="Speckle Logo">
        <h1>SpeckleLit</h1>
    </div>
    ''',unsafe_allow_html=True)


def main():

    st.set_page_config(
        page_title="SpeckleLit",
        page_icon="📊",
        layout = "wide"
    )

    inject_css('./style/style_navbar.css')
   
    with st.sidebar:
        tabs = on_hover_tabs(tabName=["Home", "Edit", "Data", "About"], iconName=['home','edit', 'pie_chart', 'person'], 
                            styles = {'navtab': {'background-color':'#fff',
                                                    'color': '#1f77b4',
                                                    'font-size': '20px',
                                                        'font-family' : 'Public Sans',
                                                    'transition': '.5s',
                                                    'white-space': 'nowrap',
                                                    'text-transform': 'uppercase'},
                                        'tabOptionsStyle': {':hover :hover': {'color': '#1f77b4',
                                                                        'cursor': 'pointer'}},
                                        'iconStyle':{'position':'fixed',
                                                        'left':'7.5px',
                                                        'text-align': 'left'},
                                        'tabStyle' : {'list-style-type': 'none',
                                                        'margin-bottom': '30px',
                                                        'padding-left': '5px'}},
                                            key="1", default_choice=0)
        

    if tabs == "Home":
        login()
    if tabs == "Data":
        data()
    elif tabs == "Edit":
        edit()
    elif tabs == "About":
        about()
        
main()