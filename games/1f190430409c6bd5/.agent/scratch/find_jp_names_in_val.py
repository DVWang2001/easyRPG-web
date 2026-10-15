import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Regex to detect Japanese Hiragana/Katakana characters in translation values
jp_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Scanning for Japanese characters in translated Values ===")
count = 0
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        # Ignore entries that are completely untranslated placeholder {原文}
        if text == "{原文}":
            continue
        
        # Check if the translation value itself contains Japanese chars
        if jp_pattern.search(text):
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print("-" * 50)
            count += 1

print(f"Total entries with Japanese chars in translated values: {count}")
