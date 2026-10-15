import json
import os

json_path = r"untranslated\translation.json"

if not os.path.exists(json_path):
    print(f"Error: {json_path} does not exist.")
    exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("JSON Keys:", list(data.keys()))
total_entries = 0
file_counts = {}

# Structure of WindyTranslator translation.json is usually a dict of files,
# where each file contains a dict of translation entries. Let's inspect.
first_key = list(data.keys())[0]
first_val = data[first_key]
print(f"First key is: {first_key}")
print(f"Type of first value: {type(first_val)}")

if isinstance(first_val, dict):
    print("Sample entry from first file:")
    sample_subkeys = list(first_val.keys())[:3]
    for sk in sample_subkeys:
        print(f"  {sk}: {first_val[sk]}")
    
    # Calculate total entries
    for file_name, entries in data.items():
        if isinstance(entries, dict):
            file_counts[file_name] = len(entries)
            total_entries += len(entries)
        else:
            total_entries += 1
else:
    total_entries = len(data)

print(f"Total entries: {total_entries}")
print(f"Number of files: {len(data)}")
print("Files and their entry counts:")
for k, v in list(file_counts.items())[:10]:
    print(f"  {k}: {v}")
if len(file_counts) > 10:
    print("  ...")
