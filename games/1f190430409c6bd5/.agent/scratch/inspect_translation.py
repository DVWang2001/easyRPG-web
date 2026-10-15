import json

with open("untranslated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Root level keys:", list(data.keys())[:10])
first_key = list(data.keys())[0]
print(f"First key: {first_key}")
print(f"First value sample (keys):", list(data[first_key].keys())[:5])
first_subkey = list(data[first_key].keys())[0]
print(f"Sample value inside first subkey:", data[first_key][first_subkey])
