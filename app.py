#IMPORT LIBRARIES
import requests
import random
import math
import string
import streamlit as st
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

#-----------------#

#toggle between local / redirection from speckleserver to app
LOCAL = False

if LOCAL:
    appID = st.secrets["appIDlocal"]
    appSecret = st.secrets["appSecretlocal"]
else:
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

#--------------------------

with header:
    st.title("SpeckleLit")

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

commit_type = "Building"
if isinstance(streams, list):
    if len(streams) > 0:
        type_names = ["Select a type", "Building", "Apertures", "Shading"]
        option = st.selectbox(
            'Select A Type',
            type_names)
        if option != "Select a type":
            commit_type = option
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
                                                width=1200,
                                                height=750)

