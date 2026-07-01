import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

map33 = data.get("Map0033.txt", {})
for key, entry in map33.items():
    if "ウェイン" in key:
        print(f"Key: {repr(key)}")
        print(f"Val: {repr(entry.get('text_to_translate', ''))}")
        print("-" * 50)
