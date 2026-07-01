import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Searching for occurrences of '神' ===")
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        
        # Filter out common compound words with '神' to avoid noise
        clean_text = text
        for word in ["精神", "神父", "神經", "神经", "神秘", "眼神", "神色", "神態", "神態", "神仙", "神殿", "神話", "神速", "神祕", "心神"]:
            clean_text = clean_text.replace(word, "")
            
        if "神" in clean_text:
            print(f"File: {file_name}")
            print(f"Key: {repr(key)}")
            print(f"Val: {repr(text)}")
            print("-" * 50)
