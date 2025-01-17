import json
from collections import defaultdict
from typing import List, Union

import redis
from owlready2 import *
from owlready2.pymedtermino2 import *
from owlready2.pymedtermino2.umls import *


def format_valuelist(input: Union[owlready2.prop.IndividualValueList, owlready2.prop.ClassValueList, None]) -> Union[List[str], None]:
    if not input:
        return None
    else:
        if isinstance(input, owlready2.prop.IndividualValueList):
            lines = [re.sub(r'\d{3}: ', '', line) for line in sorted(input)]
            filtered_lines = [line for line in lines if not line.startswith("<")]
            return filtered_lines

        if isinstance(input, owlready2.prop.ClassValueList):
            return [f"{x.terminology.name} {x.name}, {x.label.first()}" for x in input]

        else:
            raise ValueError("input must be of type IndividualValueList or ClassValueList")

if __name__ == "__main__":
    import argparse
    def get_all_isa_parents(cpt_code: str) -> list:
        this_code = CPT_lib[cpt_code]
        parent_codes = []
        parents = []
        while this_code:
            this_parent_code = this_code.is_a.first().name
            parent_desc = str(this_code.is_a.first().label.first())
            parent_codes.append(this_parent_code)
            parents.append(parent_desc)
            this_code = CPT_lib[this_parent_code]
        return parent_codes, parents

    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite_db_path", type=str, required=True, help="Path to where the SQLite database file will be stored")
    parser.add_argument("--redis_db_num", type=int, required=True, help="Redis database number to use")
    parser.add_argument("--umls_release_file_path", type=str, required=True, help="Path to the UMLS release file")
    args = parser.parse_args()

    print("Importing UMLS data into SQLite database")
    default_world.set_backend(filename=args.sqlite_db_path)
    import_umls(args.umls_release_file_path, terminologies=['ICD10', 'CPT', 'HCPCS', 'HCPT', 'ICD10CM', 'ICD10PCS'])
    default_world.save()

    print("Writing CPT data to Redis")
    PYM = get_ontology("http://PYM/").load()

    CPT_lib = PYM["CPT"]

    r = redis.Redis(host='localhost', port=6379, db=args.redis_db_num, decode_responses=False)

    # Maintain a dict to keep track of child nodes with **direct** is_a relations to a parent node
    is_a_descendants = defaultdict(list)

    # Maintain a dict to keep track of number of child nodes with **either direct or indirect** is_a relations to a parent node
    num_is_a_descendants = defaultdict(int)

    # Maintain a dict to keep track of reverse has_add_on_code relations
    has_add_on_code_ancestors = defaultdict(list)

    # Look up all CPT codes, and store the relevant information in a dictionary, put into redis
    count = 0

    # for code in cptlink_codelist["CPT Code"].tolist():
    for code in range(0, 99999):
        code = str(code).zfill(5)
        #Ensure that the code is a 5-digit alphanumerić string
        # if not code.isalnum() or len(code) != 5:
        #     print(f"Skipping {code}")
        concept = CPT_lib[code]
        if concept is None:
            continue
        # Get the lay term for the CPT code from the "Consumer" column in the CPTLink code list
        # lay_term=cptlink_codelist.loc[cptlink_codelist["CPT Code"] == code, "Consumer"].values
        # lay_term = lay_term[0] if len(lay_term) > 0 else None

        #Get all is_a parents of the CPT code
        is_a_parent_codes, is_a_parents = get_all_isa_parents(code)
        # Increment the descendent CPT code count for each parent code
        for parent_code in is_a_parent_codes:
            num_is_a_descendants [parent_code] += 1

        # Add the code to the list of immediate descendants for the lowest level parent code
        if is_a_parent_codes:
            is_a_descendants [is_a_parent_codes[0]].append(code)

        # Create a dictionary with the CPT code, lay term, and definition

        entry = {
            "code": code,
            "definition": str(concept.label.first()),
            "is_a_code": is_a_parent_codes,
            "is_a": is_a_parents,
            # "lay_term": lay_term,
            "guidelines": format_valuelist(concept.guideline),
            "addl_guidelines": format_valuelist(concept.additional_guideline),
            "do_not_code_with_str": format_valuelist(concept.do_not_code_with),
            "do_not_code_with": [x.name for x in concept.do_not_code_with], 
            "has_add_on_code_str": format_valuelist(concept.has_add_on_code),
            "has_add_on_code": [x.name for x in concept.has_add_on_code],
            "is_add_on_code_to": [],
            # "effective_date": cptlink_codelist.loc[cptlink_codelist["CPT Code"] == code, "Current Descriptor Effective Date"].values[0] if len(cptlink_codelist.loc[cptlink_codelist["CPT Code"] == code, "Current Descriptor Effective Date"].values) > 0 else None,
        }

        # Add the CPT code to the list of ancestors for each code it is add-on code for
        for add_on_code in concept.has_add_on_code:
            has_add_on_code_ancestors [add_on_code.name].append(code)
        # print(json.dumps(entry, indent=4)) #
        # Store the dictionary in redis
        r.set(f"162132::{code}", json.dumps(entry))
        count += 1

    # For each code that is known to be an add-on code, add this info to the redis entry

    for code, ancestors in has_add_on_code_ancestors.items():
        #print (f"(code): (ancestors)")
        entry = r.get(f"162132::{code}")

        if entry:
            entry = json.loads(entry)
            entry["is_add_on_code_to"].extend(ancestors)
            r.set(f"162132::{code}", json.dumps(entry))

    # At this step, is_a_descendants only has keys for the lowest level parent codes. Add the rest of the parent codes
    for code in num_is_a_descendants.keys():
        is_a_parent_codes, _ = get_all_isa_parents(code)
        if is_a_parent_codes:
            #Add self to the lowest level parent code
            if code not in is_a_descendants[is_a_parent_codes[0]]:
                is_a_descendants[is_a_parent_codes[0]].append(code)


    assert len(is_a_descendants) == len(num_is_a_descendants)

    # Each key in num_is_a_descendants is a parent concept code. Add this info to the redis entry for each concept
    for code, num_descendants in num_is_a_descendants.items():
        concept = CPT_lib[code]
        # print(concept, is_a_descendants[code])
        # Get all is a parents of the CPT code
        is_a_parent_codes, is_a_parents = get_all_isa_parents(code)

        entry = {
            "code": code,
            "definition": str(concept.label.first()) if code != "CPT" else "Root node",
            "is_a_code": is_a_parent_codes,
            "is_a": is_a_parents,
            "descendant_codes": is_a_descendants[code],
            "num_descendants": num_descendants,
        }

        r.set(f"162132::{code}", json.dumps(entry))


    os.system("redis-cli save")

    r.close()
    print("Finished initial set-up")
