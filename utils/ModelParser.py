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

