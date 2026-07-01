import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for file_name, entries in data.items():
    for key, entry in entries.items():
        if "ロミ" in key or "ジュリ" in key:
            # Only print Romi/Juri dialogue
            if "どうして、" in key or "あぁ！！！" in key:
                text = entry.get('text_to_translate', '')
                print(f"Key: {repr(key)}")
                print(f"Val: {repr(text)}")
                print("-" * 50)
