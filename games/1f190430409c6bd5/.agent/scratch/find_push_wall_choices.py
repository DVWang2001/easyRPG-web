import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        if "接縫很不自然" in text or "不自然" in key:
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print("-" * 50)
