import sys
from collections import OrderedDict


def are_migrations_running():
    """
    Checks whether the app was launched with the migration-specific params
    """
    # return sys.argv and ('migrate' in sys.argv or 'makemigrations' in sys.argv)
    return sys.argv and (
        "migrate" in sys.argv
        or "makemigrations" in sys.argv
        or "showmigrations" in sys.argv
        or "sqlmigrate" in sys.argv
    )


def search(dictionary, search_list):
    """
    To run:
            from boranga.utils import search
            search(dictionary, ['BRM', 'JM 1'])
    """
    result = []
    flat_dict = flatten(dictionary)
    # for k, v in flat_dict.iteritems():
    for k, v in flat_dict.items():
        if any(x.lower() in v.lower() for x in search_list):
            result.append({k: v})

    return result


def search_approval(approval, searchWords):
    qs = []
    a = approval
    if a.surrender_details:
        results = search(a.surrender_details, searchWords)
        if results:
            res = {
                "number": a.lodgement_number,
                "id": a.id,
                "type": "Approval",
                "applicant": a.applicant,
                "text": results,
            }
            qs.append(res)
    if a.suspension_details:
        results = search(a.suspension_details, searchWords)
        if results:
            res = {
                "number": a.lodgement_number,
                "id": a.id,
                "type": "Approval",
                "applicant": a.applicant,
                "text": results,
            }
            qs.append(res)
    if a.cancellation_details:
        found = False
        for s in searchWords:
            if s.lower() in a.cancellation_details.lower():
                found = True
        if found:
            res = {
                "number": a.lodgement_number,
                "id": a.id,
                "type": "Approval",
                "applicant": a.applicant,
                "text": a.cancellation_details,
            }
            qs.append(res)
    return qs


def search_compliance(compliance, searchWords):
    qs = []
    c = compliance
    if c.text:
        found = False
        for s in searchWords:
            if s.lower() in c.text.lower():
                found = True
        if found:
            res = {
                "number": c.reference,
                "id": c.id,
                "type": "Compliance",
                "applicant": c.proposal.applicant,
                "text": c.text,
            }
            qs.append(res)
    if c.requirement:
        found = False
        for s in searchWords:
            if s.lower() in c.requirement.requirement.lower():
                found = True
        if found:
            res = {
                "number": c.reference,
                "id": c.id,
                "type": "Compliance",
                "applicant": c.proposal.applicant,
                "text": c.requirement.requirement,
            }
            qs.append(res)
    return qs


def compare_data(dict1, dict2, schema):
    """
    dict1 - most recent data
    dict2 - prev data
    schema - proposal.schema

    To run:
            from boranga.utils import compare
            compare_data(dict1, dict2, schema)

    eg.
            p=Proposal.objects.get(id=110)
            dict1=p.data[0]
            dict2=p.previous_application.data[0]
            return compare_data(dict1, dict2, p.schema)
    """
    result = []
    flat_dict1 = flatten(dict1)
    flat_dict2 = flatten(dict2)
    # for k1, v1 in flat_dict1.iteritems():
    for k1, v1 in flat_dict1.items():
        # for k2, v2 in flat_dict2.iteritems():
        for k2, v2 in flat_dict2.items():
            if k1 == k2 and v2:
                if v1 != v2:
                    result.append({k1: [v1, v2]})
                continue

    # Now find the Question(label) for this section(k1 or k2) and incorporate into the dict result
    new = {}
    # name_map=search_keys2(flatten(schema), search_list=['name', 'label'])
    name_map = search_keys(schema, search_list=["name", "label"])
    for item in result:
        k = item.keys()[0]
        v = item[k]
        section = k.split(".")[-1]
        label = [i["label"] for i in name_map if section in i["name"]]
        if label:
            new.update({k: {label[0]: v}})

    return new


def create_richtext_help(help_list=None, help_text="help_text"):

    # for testing
    # if not help_list:
    # 	pt = ProposalType.objects.all()[4]
    # 	help_list = search_keys(pt.schema, search_list=['help_text','label'])[:3]

    richtext = ""
    for i in help_list:
        if i.has_key(help_text) and "anchor=" in i[help_text]:
            anchor = i[help_text].split("anchor=")[1].split('"')[0]
            # print anchor, i['label']

            richtext += '<h1><a id="{0}" name="{0}"> {1} </a></h1><p>&nbsp;</p>'.format(
                anchor, i["label"]
            )
        else:
            richtext += "<h1> {} </h1><p>&nbsp;</p>".format(i["label"])

    return richtext


def search_keys(dictionary, search_list=["help_text", "label"]):
    """
    Return search_list pairs from the schema -- given help_text, finds the equiv. label

    To run:
            from boranga.utils import search_keys
            search_keys2(dictionary, search_list=['help_text', 'label'])
            search_keys2(dictionary, search_list=['name', 'label'])
    """
    search_item1 = search_list[0]
    search_item2 = search_list[1]
    result = []
    flat_dict = flatten(dictionary)
    # for k, v in flat_dict.iteritems():
    for k, v in flat_dict.items():
        if any(x in k for x in search_list):
            result.append({k: v})

    help_list = []
    for i in result:
        try:
            key = i.keys()[0]
            if key and key.endswith(search_item1):
                corresponding_label_key = (
                    ".".join(key.split(".")[:-1]) + "." + search_item2
                )
                for j in result:
                    key_label = j.keys()[0]
                    if (
                        key_label
                        and key_label.endswith(search_item2)
                        and key_label == corresponding_label_key
                    ):  # and result.has_key(key):
                        help_list.append(
                            {search_item2: j[key_label], search_item1: i[key]}
                        )
        except Exception as e:
            print(e)

    return help_list


def missing_required_fields(proposal):
    """
    Returns the missing required fields from the schema (no data is entered)
    """
    data = flatten(proposal.data[0])
    sections = search_multiple_keys(
        proposal.schema, primary_search="isRequired", search_list=["label", "name"]
    )

    missing_fields = []
    # for flat_key in data.iteritems():
    for flat_key in data.items():
        for item in sections:
            if flat_key[0].endswith(item["name"]):
                if not flat_key[1].strip():
                    missing_fields.append(dict(name=flat_key[0], label=item["label"]))
    return missing_fields


def search_multiple_keys(
    dictionary, primary_search="isRequired", search_list=["label", "name"]
):
    """
    Given a primary search key, return a list of key/value pairs corresponding to the same section/level

    To test:
            p=Proposal.objects.get(id=139)
            return search_multiple_keys(p.schema, primary_search='isRequired', search_list=['label', 'name'])

    Example result:
    [
            {'isRequired': {'label': u'Enter the title of this proposal','name': u'Section0-0'}},
            {'isRequired': {'label': u'Enter the purpose of this proposal', 'name': u'Section0-1'}},
            {'isRequired': {'label': u'In which Local Government Authority (LAG)
                is this proposal located?','name': u'Section0-2'}},
            {'isRequired': {'label': u'Describe where this proposal is located', 'name': u'Section0-3'}}
    ]
    """

    # get a flat list of the schema and keep only items in all_search_list
    all_search_list = [primary_search] + search_list
    result = []
    flat_dict = flatten(dictionary)
    # for k, v in flat_dict.iteritems():
    for k, v in flat_dict.items():
        if any(x in k for x in all_search_list):
            result.append({k: v})

    # iterate through the schema and get the search items
    # corresponding to each primary_search item (at the same level/section)
    help_list = []
    for i in result:
        try:
            tmp_dict = {}
            key = i.keys()[0]
            if key and key.endswith(primary_search):
                for item in all_search_list:
                    corresponding_label_key = ".".join(key.split(".")[:-1]) + "." + item
                    for j in result:
                        key_label = j.keys()[0]
                        if (
                            key_label
                            and key_label.endswith(item)
                            and key_label == corresponding_label_key
                        ):  # and result.has_key(key):
                            tmp_dict.update({item: j[key_label]})
                if tmp_dict:
                    help_list.append(tmp_dict)
                # if tmp_dict:
                #  help_list.append( {primary_search: tmp_dict} )

        except Exception as e:
            print(e)

    return help_list


def flatten(old_data, new_data=None, parent_key="", sep=".", width=4):
    """
    Json-style nested dictionary / list flattener
    :old_data: the original data
    :new_data: the result dictionary
    :parent_key: all keys will have this prefix
    :sep: the separator between the keys
    :width: width of the field when converting list indexes
    """
    if new_data is None:
        # new_data = {}
        new_data = OrderedDict()

    if isinstance(old_data, dict):
        for k, v in old_data.items():
            new_key = parent_key + sep + k if parent_key else k
            flatten(v, new_data, new_key, sep, width)
    elif isinstance(old_data, list):
        if len(old_data) == 1:
            flatten(old_data[0], new_data, parent_key, sep, width)
        else:
            for i, elem in enumerate(old_data):
                new_key = "{}{}{:0>{width}}".format(
                    parent_key, sep if parent_key else "", i, width=width
                )
                flatten(elem, new_data, new_key, sep, width)
    else:
        if parent_key not in new_data:
            new_data[parent_key] = old_data
        else:
            raise AttributeError(f"key {parent_key} is already used")

    return new_data
