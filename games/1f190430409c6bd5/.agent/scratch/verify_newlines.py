import json

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        if "\\n" in text:
            print(f"Literal \\n found in {file_name} under key {repr(key)}: {repr(text)}")
            count += 1

print(f"Total literal \\n occurrences: {count}")
