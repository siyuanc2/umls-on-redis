import json
from cptdb.client import CPTDB

db = CPTDB(db=5)

full_hierarchy = db.generate_code_hierarchy_subtree("162132::CPT", include_addon_codes=True, strip_common_prefix=False)

full_hierarchy_str = json.dumps(full_hierarchy, indent=2)
with open("/home/ubuntu/Desktop/cpt_full_hierarchy.json", "w") as f:
    f.write(full_hierarchy_str)

print("Full hierarchy exported to cpt_full_hierarchy.json")

# Loop through all valid cpt codes and write documentation to a file
count = 0
for code in range(0, 99999):
    code_str = str(code).zfill(5)
    doc = db.get_code_docs_json(code_str)

    if doc:
        doc_str = json.dumps(doc, indent=2)
        with open("/home/ubuntu/Desktop/cpt_documentation.txt", "a") as f:
            f.write(doc_str + ",\n")
        count += 1

print(f"Exported documentation for {count} codes to cpt_documentation.txt")
