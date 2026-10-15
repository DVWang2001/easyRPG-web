import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for file_name, entries in data.items():
    for key, entry in entries.items():
        if "再考慮一下" in entry.get('text_to_translate', '') or "不参加" in key:
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(entry.get('text_to_translate', ''))}")
            print("-" * 50)
