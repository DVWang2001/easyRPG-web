import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

jp_say = "\u8aac" # 説 (Japanese Kanji)
sc_say = "\u8b6a" # 说 (Simplified Chinese)
tc_say = "\u8aaa" # 說 (Traditional Chinese)

jp_count = 0
sc_count = 0

for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        if jp_say in text:
            jp_count += text.count(jp_say)
            print(f"Japanese '説' found in {file_name}: {repr(text)}")
        if sc_say in text:
            sc_count += text.count(sc_say)
            print(f"Simplified '说' found in {file_name}: {repr(text)}")

print(f"Total Japanese '説' found: {jp_count}")
print(f"Total Simplified '说' found: {sc_count}")
