# UMLS on Redis

UMLS on Redis is a Python class designed to facilitate interaction with a Redis database containing medical terminologies from the [Unified Medical Language System](https://www.nlm.nih.gov/research/umls/index.html) (UMLS). While established libraries such as [PyMedTermino2](https://owlready2.readthedocs.io/en/latest/pymedtermino2.html) exist, they rely on a SQLite database that does not support multiple clients simultaneously. This package provides methods for retrieving data, finding parent concepts, generating code hierarchies, and obtaining detailed documentation for Current Procedural Terminology (CPT) codes and concepts, with planned support for HCPCS and ICD-10-CM in the future.

## Features

- Retrieve codes and their hierarchies from a Redis database.
- Identify the parent concept groups of semantically adjacent codes.
- Generate a hierarchy subtree for a specified concept group.
- Retrieve UMLS documentation for CPT codes in JSON format.

## Installation and Setup

To install the package, execute the following commands:

```bash
git clone git@github.com:siyuanc2/umls-on-redis.git
cd umls-on-redis
pip install -e .
```

### Import Data from UMLS Using PyMedTermino2

You must obtain a UMLS Metathesaurus license from [here](https://www.nlm.nih.gov/research/umls/index.html). UMLS contains copyrighted material developed by various organizations, and this project does not assume rights to any of the material from UMLS. Download the UMLS Metathesaurus Full Subset or Full Release files as instructed [here](https://owlready2.readthedocs.io/en/latest/pymedtermino2.html#installation).

Once you have obtained a UMLS release file, run the initial setup script to import UMLS data to Redis:

```bash
python redis_initial_setup.py --sqlite_db_path SQLITE_DB_PATH --redis_db_num REDIS_DB_NUM --umls_release_file_path UMLS_RELEASE_FILE_PATH --cptlink_consolidated_code_list_path CPTLINK_CONSOLIDATED_CODE_LIST_PATH --cptlink_clinician_descriptor_path CPTLINK_CLINICIAN_DESCRIPTOR_PATH
```

Where:
 - `SQLITE_DB_PATH` is the path to the SQLite DB file that will be created by PyMedTermino2, e.g., `/home/usr/pym.sqlite3`
 - `REDIS_DB_NUM` is the database ID where the data will be stored in Redis, e.g., `0`
 - `UMLS_RELEASE_FILE_PATH` is the path to the zipped UMLS release file, e.g., `/home/usr/umls-2024AB-metathesaurus-full.zip`
 - `CPTLINK_CONSOLIDATED_CODE_LIST_PATH` is path to Consolidated Code List file from CPTLink Primary Data Files converted to csv format, e.g., `/home/usr/consolidated_code_list.csv`
 - `CPTLINK_CLINICIAN_DESCRIPTOR_PATH` is path to ClinicianDescriptor file from CPTLink Primary Data Files converted to csv format, e.g., `/home/usr/clinician_descriptor.csv`

## Usage

Below is a simple example of how to use the CPTDB package:

```Python
import json
from cptdb.client import CPTDB

# Create an instance of the CPTDB class
cpt_db = CPTDB(db=0)

# Retrieve raw data for CPT code 96374
code = '96374'
code_data = cpt_db._retrieve(f'162132::{code}')

# Find the parent concept of a given CPT code, whose number of descendants is as close to the target as possible
parent_concept = cpt_db.find_parent_concept(code, target_group_size=10)
parent_concept_entry = db._retrieve(f"162132::{parent_concept}")
print(f"Parent concept of {code}: {parent_concept_entry['definition']}")

# Generate a hierarchy subtree with the given concept as root
subtree = cpt_db.generate_code_hierarchy_subtree(parent_concept)
print(json.dumps(subtree, indent=4))

# Get detailed documentation for a CPT code
docs = cpt_db.get_code_docs_json(code)
print(json.dumps(docs, indent=4))
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Important Notice:**
This project requires a licensed copy of the Unified Medical Language System (UMLS) Metathesaurus. UMLS contains copyrighted material. While any user can use this project freely, this project does not claim or assume any rights to UMLS material.