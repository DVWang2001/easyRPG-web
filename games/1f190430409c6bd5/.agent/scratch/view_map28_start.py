import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

map28 = data.get("Map0028.txt", {})
for i, (key, entry) in enumerate(list(map28.items())[:30]):
    text = entry.get('text_to_translate', '')
    print(f"{i}: Key: {repr(key)}")
    print(f"   Val: {repr(text)}")
    print("-" * 50)
