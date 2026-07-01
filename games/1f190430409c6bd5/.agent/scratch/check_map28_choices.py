import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Find Map0028.txt entries
map28 = data.get("Map0028.txt", {})
for key, entry in map28.items():
    text = entry.get('text_to_translate', '')
    # Print key and val to see what they look like
    if any(q in key for q in ["？", "?", "そうや", "なんでもない", "選択", "選択肢"]):
        print(f"Key: {repr(key)}")
        print(f"Val: {repr(text)}")
        print("-" * 50)
