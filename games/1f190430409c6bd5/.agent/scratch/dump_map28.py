import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

map28 = data.get("Map0028.txt", {})
print(f"Total entries in Map0028.txt: {len(map28)}")
for key, entry in map28.items():
    text = entry.get('text_to_translate', '')
    print(f"Key: {repr(key)}")
    print(f"Val: {repr(text)}")
    print("-" * 50)
