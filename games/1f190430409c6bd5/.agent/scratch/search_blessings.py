import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Searching for all blessing translations ===")
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        
        found = False
        for kw in ["保佑", "庇佑", "加護", "降福", "保祐", "庇祐"]:
            if kw in text:
                found = True
        
        if found:
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print("-" * 50)
