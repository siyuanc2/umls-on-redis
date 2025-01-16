import re
import json
from typing import Union, Optional

import redis

def extract_choices(data):
    """
    Traverse a tree-like JSON structure to extract a list of leaf nodes.
    """
    codes_list = []
    code_pattern = re.compile(r"\b\d{5}\b|\b\d{4}[A-Za-z]\b")

    def traverse_dict(d):
        if isinstance(d, dict):
            for key, value in d.items():
                if key == "choices":
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                traverse_dict(item)
                            elif isinstance(item, str):
                                match = code_pattern.search(item)
                                if match:
                                    codes_list.append(match.group())
                            else:
                                raise ValueError("Unexpected type in choices list")
                else:
                    traverse_dict(value)
        elif isinstance(d, list):
            for item in d:
                traverse_dict(item)
    traverse_dict(data)
    return codes_list

class CPTDB():
    """
    A class to interact with a Redis database containing CPT (Current Procedural Terminology) codes and their hierarchies imported from UMLS.

    Methods
    -------
    retrieve(key: str) -> Optional[dict]:
        Retrieves a dictionary from Redis by key.
    
    find_parent_concept(code: str, target_group_size: int = 10) -> str:
        Finds the largest parent concept of a given CPT code whose number of descendants is less than a target group size.
    
    generate_code_hierarchy_subtree(parent_code: str, include_addon_codes: bool = True, strip_common_prefix: bool = False, parent_prefix = Optional[str]) -> Union[str, dict, None]:
        Generates a hierarchy subtree with the given parent CPT code as the root.
    
    get_code_docs_json(code: str, verbose_level: Optional[int] = 2) -> Union[dict, None]:
        Retrieves detailed documentation for a given CPT code in JSON format.
    """
    def __init__(self, db: int = 5):
        self.redis = redis.Redis(host='localhost', port=6379, db=db, decode_responses=False)
        self.cpt_code_pattern = re.compile(r"\b\d{5}\b|\b\d{4}[UFTM]\b")

    def __del__(self):
        self.redis.close()

    def _retrieve(self, key: str) -> Optional[dict]:
        """
        Retrieve a dictionary from Redis by key.
        """
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def find_parent_concept(self, code: str, target_group_size: int = 10) -> str:
        """
        Find the parent concept of a given CPT code whose number of descendants is closest to the target group size.
        """
        if code.startswith("162132::"):
            code_number = code.split("::")[1]
        else:
            code_number = code

        entry = self._retrieve(f"162132::{code_number}")
        closest_group = None
        closest_group_diff = float('inf')

        if entry:
            for parent_concept in entry["is_a_code"]:
                parent_entry = self._retrieve(f"162132::{parent_concept}")
                if parent_entry:
                    num_descendants = parent_entry["num_descendants"]
                    diff = abs(num_descendants - target_group_size)
                    if diff < closest_group_diff:
                        closest_group = parent_concept
                        closest_group_diff = diff
        return closest_group

    def generate_code_hierarchy_subtree(self, parent_code: str, include_addon_codes: bool = True, strip_common_prefix: bool = False, parent_prefix = Optional[str]) -> Union[str, dict, None]:
        if parent_code.startswith("162132::"):
            code_number = parent_code.split("::")[1]
        else:
            code_number = parent_code
        entry = self._retrieve(f"162132::{code_number}")
        if entry:
            if not self.cpt_code_pattern.match(code_number):
                # This is a parent concept
                ret = {"concept": entry["definition"], "children": []}
                for desc_code in entry["descendant_codes"]:
                    child_desc = self.generate_code_hierarchy_subtree(desc_code, include_addon_codes, strip_common_prefix, entry["definition"])
                    if child_desc:
                        ret["children"].append(child_desc)
                return ret if len(ret["children"]) > 0 else None
            else:
                # This is a leaf node (CPT code)
                if not include_addon_codes and len(entry["is_addon_code_to"]) > 0:
                    return None
                descr = entry["definition"]
                if strip_common_prefix and parent_prefix:
                    descr = descr.replace(parent_prefix, "(Same as parent description)", 1)
                return f"CPT {code_number}, {descr}"
        return None

    def get_code_docs_json(self, code: str, verbose_level: Optional[int] = 2) -> Union[dict, None]:
        if code.startswith("162132::"):
            code_number = code.split("::")[1]
        else:
            code_number = code
        entry = self._retrieve(f"162132::{code_number}")
        if not entry:
            return None
            # return f"{code_number} is not a valid CPT code."
        if verbose_level > 2:
            return entry
        ret = {}
        ret["code"] = entry["code"]
        ret["description"] = entry["definition"]
        ret["hierarchy"] = entry["is_a"]
        if entry.get("lay_term", None):
            ret["common_language_term"] = entry["lay_term"]
        if verbose_level > 1:
            if entry["guidelines"]:
                ret["guidelines"] = entry["guidelines"]
            if entry["addl_guidelines"]:
                ret["additional_guidelines"] = entry["addl_guidelines"]
            if entry["do_not_code_with"]:
                ret["do_not_code_with"] = entry["do_not_code_with_str"]
            if entry["has_add_on_code"]:
                ret["has_add_on_code"] = entry["has_add_on_code_str"]
        return ret

