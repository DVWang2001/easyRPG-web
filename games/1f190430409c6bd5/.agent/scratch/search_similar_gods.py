import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Searching for Lagropas variants in translations ===")
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        
        found = False
        for variant in ["拉格羅", "拉格羅巴", "拉格羅帕", "拉葛羅", "拉古羅", "拉克羅"]:
            if variant in text:
                found = True
                
        # Only check if original key contains the full god name ラグロパス
        if "ラグロパス" in key:
            found = True
            
        if found:
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print("-" * 50)
