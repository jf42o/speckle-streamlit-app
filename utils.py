UPDATE = True
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
import streamlit.components.v1 as components
from st_on_hover_tabs import on_hover_tabs

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

def inject_css(css_path):
    st.markdown('<style>' + open(f'{css_path}').read() + '</style>', unsafe_allow_html=True)