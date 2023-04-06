#IMPORT LIBRARIES
import requests
import random
import math
import string
import streamlit as st
import pandas as pd


#specklepy libraries
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
#specklepy libraries
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
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

from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.api.resources.stream import Stream
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.logging.exceptions import SpeckleException

## DEFINITIONS
def createRandomChallenge(length=0):
    lowercase = list(string.ascii_lowercase)
    uppercase = list(string.ascii_uppercase)
    punctuation = ["-",".","_","~"] # Only hyphen, period, underscore, and tilde are allowed by OAuth Code Challenge
    digits = list(string.digits)
    masterlist = lowercase+uppercase+digits+punctuation
    masterlist = masterlist+lowercase+uppercase+digits
    random.shuffle(masterlist)
    if 0 < length <= 128:
        masterlist = random.sample(masterlist, random.randint(length, length))
    else:
        masterlist = random.sample(masterlist, random.randint(64, 128))
    return ''.join(masterlist)

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

def parse_and_update_model(commit_data, categories, params_to_search, updates=None, upd=UPDATE):
    if updates is None:
        updates = {}
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
                            if upd:
                                element["parameters"][parameter]["value"] = updates[key]
                            dict[key] = element["parameters"][parameter]["value"]
                            break
                    except:
                        continue
            result.append(dict)
    return result

#-----------------#

#toggle between local / redirection from speckleserver to app
LOCAL = False

appID = st.secrets["appID"]
appSecret = st.secrets["appSecret"]

#PAGE CONFIG
st.set_page_config(
    page_title="SpeckleLit",
    page_icon="📊",
    layout = "wide"
)

#--------------------------
#CONTAINERS
header = st.container()
authenticate = st.container()
#--------------------------

#Authentification#

#----------------------------------------------------------------------------------------------------------#

with header:
    st.title("SpeckleLit")
if not LOCAL:

    if 'access_code' not in st.session_state:
        st.session_state['access_code'] = None
    if 'token' not in st.session_state:
        st.session_state['token'] = None
    if 'refresh_token' not in st.session_state:
        st.session_state['refresh_token'] = None
    if 'Building' not in st.session_state:
        st.session_state['Building'] = None
    if 'Apertures' not in st.session_state:
        st.session_state['Apertures'] = None
    if 'Shading' not in st.session_state:
        st.session_state['Shading'] = None
    if 'hbjson' not in st.session_state:
        st.session_state['hbjson'] = None
    if 'daylight_job' not in st.session_state:
        st.session_state['daylight_job'] = None
    if 'energyanalysis_job' not in st.session_state:
        st.session_state['energyanalysis_job'] = None
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
            st.image("https://speckle.systems/content/images/2021/02/logo_big.png",width=50)
            link = '[Login to Speckle]('+verify_url+')'
            st.subheader(link)
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

    if isinstance(streams, list):
        stream_names = ["Select a stream"]
        for aStream in streams:
            stream_names.append(aStream.name)
        option = st.selectbox(
            'Select A Stream',
            (stream_names))
        if option != "Select a stream":
            stream = streams[stream_names.index(option)-1]
            branches = getBranches([client, stream])
            branch_names = ["Select a branch"]
            for aBranch in branches:
                branch_names.append(aBranch.name)
            option = st.selectbox(
                'Select A Branch',
                (branch_names))
            if option != "Select a branch":
                branch = branches[branch_names.index(option)-1]
                commits = getCommits(branch)
                commit_names = ["Select a commit"]
                for aCommit in commits:
                    commit_names.append(str(aCommit.id)+": "+aCommit.message)
                option = st.selectbox('Select A Commit', (commit_names))
                if option != "Select a commit":
                    commit = commits[commit_names.index(option)-1]
                    st.components.v1.iframe(src="https://speckle.xyz/embed?stream="+
                                            stream.id+"&commit="
                                            +commit.id+
                                            "&transparent=false",
                                            width=1250,
                                            height=750)


else:

    commit_url = "https://speckle.xyz/streams/063a663421/commits/153e617495"
    wrapper = StreamWrapper(commit_url)
    client = wrapper.get_client()
    account = get_default_account()
    client.authenticate_with_account(account)
    st.components.v1.iframe(src="https://speckle.xyz/embed?stream="+"063a663421"+"&commit="
                                            "153e617495"+
                                            "&transparent=false",
                                            width=1250,
                                            height=750)

    commit = client.commit.get(wrapper.stream_id, wrapper.commit_id)
    obj_id = commit.referencedObject
    commit_data = operations.receive(obj_id, wrapper.get_transport())
    categories = ["@Wände", "@Geschossdecken"]
    params_to_search = ["IMP_Disziplin", "IMP_Bauteil"]
    modeldata = parse_and_update_model(commit.referencedObject, categories, params_to_search)
    dataframe_editable = st.experimental_data_editor(pd.DataFrame(modeldata))