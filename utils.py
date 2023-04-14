UPDATE = True
import requests
import streamlit as st
import pandas as pd
import numpy as np
import trimesh
from trimesh.collision import CollisionManager
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode, DataReturnMode, JsCode
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper
from specklepy.transports.server import ServerTransport
from specklepy.objects.geometry import *
from specklepy.api import operations
from specklepy.objects.geometry import Brep, Point, Mesh
from specklepy.objects import Base
from specklepy.objects.other import RenderMaterial
from specklepy.api.credentials import get_default_account
import streamlit.components.v1 as components
from st_on_hover_tabs import on_hover_tabs
import collada
from io import BytesIO
import os


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
        try:
            category_elements = commit_data[cat]
        except:
            continue
        if category_elements is not None:
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

def get_all_meshes(child: Base) -> List[Mesh]:
    """Returns all the meshes from a given Base object."""
    meshes = []

    names = child.get_dynamic_member_names()
    for name in names:
        prop = child[name]
        if isinstance(prop, Base):
            if isinstance(prop, Brep):
                if not hasattr(prop, "displayValue"):
                    break
                meshes.append((prop.displayValue, prop.id,
                                prop.applicationId, prop))
            elif isinstance(prop, Mesh):
                meshes.append((prop, prop.id, prop.applicationId))
        elif isinstance(prop, list):
            for p in prop:
                if isinstance(p, Brep):
                    if not hasattr(p, "displayValue"):
                        break
                    meshes.append(
                        (p.displayValue, p.id, p.applicationId, p))
                elif isinstance(p, Mesh):
                    meshes.append((p, p.id, p.applicationId))
                elif hasattr(p, "displayValue") or hasattr(p, "@displayValue"):
                    meshes.append((p.displayValue, p.id, p.applicationId))

    return meshes

def speckle_meshes_to_trimesh(speckle_meshes):
    trimesh_objects = []

    for mesh in speckle_meshes:
        # Extract vertices and faces data from the mesh
        data1 = mesh[0][0].vertices
        data2 = mesh[0][0].faces

        # Convert the vertices list into a list of tuples
        vertices_tuples = [(data1[i], data1[i+1], data1[i+2]) for i in range(0, len(data1), 3)]

        # Convert the faces list into a list of tuples
        faces_tuples = [(data2[i+1], data2[i+2], data2[i+3]) for i in range(0, len(data2), 4)]

        # Create the trimesh object and add it to the list
        trimesh_object = trimesh.Trimesh(vertices=vertices_tuples, faces=faces_tuples)
        trimesh_objects.append(trimesh_object)

    return trimesh_objects

def download_dae_button(trimesh_objects, filename='meshes.dae'):
    # Combine all trimesh objects into one
    combined_trimesh = trimesh.util.concatenate(trimesh_objects)
    
    # Export the combined trimesh object as a .dae file
    dae_data = combined_trimesh.export(file_type='dae')

    # Create a download button with the .dae file data
    buffer = BytesIO()
    buffer.write(dae_data)
    buffer.seek(0)

    return st.download_button(
        label='Download .dae file',
        data=buffer,
        file_name=filename,
        mime='application/octet-stream',)

def detect_clashes(trimesh_list1, trimesh_list2, mesh_list1, mesh_list2):
    clashes = []

    # Create CollisionManager instances for each set of trimesh objects
    manager1 = CollisionManager()
    manager2 = CollisionManager()

    # Add trimesh objects to their respective CollisionManagers
    for i, mesh in enumerate(trimesh_list1):
        manager1.add_object(name=mesh_list1[i][1], mesh=mesh)
    
    for i, mesh in enumerate(trimesh_list2):
        manager2.add_object(name=mesh_list2[i][1], mesh=mesh)

    # Check for collisions between objects from the two CollisionManagers
    is_collision, names = manager1.in_collision_other(manager2, return_names=True)

    if is_collision:
        for name1, name2 in names:
            mesh1 = manager1.objects[name1].geometry
            mesh2 = manager2.objects[name2].geometry
            intersection_volume = mesh1.intersection(mesh2).volume

            # Set the color of colliding Speckle meshes to red
            speckle_mesh1 = next(mesh for mesh in mesh_list1 if mesh[1] == name1)
            speckle_mesh2 = next(mesh for mesh in mesh_list2 if mesh[1] == name2)

            def set_mesh_color_red(speckle_mesh):
                speckle_mesh.colors = 65536
                
            set_mesh_color_red(speckle_mesh1[0])
            set_mesh_color_red(speckle_mesh2[0])

            clashes.append({
                'mesh1_id': name1,
                'mesh2_id': name2,
                'intersection_volume': intersection_volume,
                'mesh1': mesh1,
                'mesh2': mesh2
            })

    return clashes