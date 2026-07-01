import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Regex pattern for variants of Lagropas
# e.g., 拉(格|葛|古|哥)(羅|洛|路|ル)(巴|帕|巴|帕)(斯|司)?
pattern = re.compile(r"拉[格葛古哥][羅洛路][巴帕]斯?")

print("=== Regex Search for Lagropas spelling variants ===")
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        matches = pattern.findall(text)
        if matches:
            # Check if this text has something other than "拉格羅帕斯"
            has_different = False
            for m in matches:
                if m != "拉格羅帕斯":
                    has_different = True
            
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print(f"Matches: {matches}")
            print("-" * 50)
