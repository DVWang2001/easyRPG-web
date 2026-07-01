import json
import os
import re
import sys
from collections import Counter

# Reconfigure stdout to support UTF-8 printing on Windows
sys.stdout.reconfigure(encoding='utf-8')

json_path = r"untranslated\translation.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Step 0: Detect source language
sample_texts = []
flat_entries = [] # For splitting later
for file_name, entries in data.items():
    if isinstance(entries, dict):
        for entry_key, entry in entries.items():
            text = entry.get('text_to_translate', '')
            sample_texts.append(text)
            flat_entries.append({
                "file": file_name,
                "key": entry_key,
                "text": text,
                "marker": entry.get('original_marker', ''),
                "speaker": entry.get('speaker_id', '')
            })

combined_text = "".join(sample_texts)

hiragana_katakana = re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', combined_text)
hangul = re.findall(r'[\uAC00-\uD7AF]', combined_text)
thai = re.findall(r'[\u0E00-\u0E7F]', combined_text)
cyrillic = re.findall(r'[\u0400-\u04FF]', combined_text)
chinese_chars = re.findall(r'[\u4E00-\u9FFF]', combined_text)

source_lang = "西歐語系" # Default
if len(hiragana_katakana) > 10:
    source_lang = "日語"
elif len(hangul) > 10:
    source_lang = "韓語"
elif len(thai) > 10:
    source_lang = "泰語"
elif len(cyrillic) > 10:
    source_lang = "俄語/東歐語系"
elif len(chinese_chars) > len(combined_text) * 0.1: # Significant Chinese chars and no kana
    source_lang = "中文（繁體或簡體）"

print(f"Detected SOURCE_LANG: {source_lang}")
print(f"Character counts: Kana={len(hiragana_katakana)}, Hangul={len(hangul)}, Thai={len(thai)}, Cyrillic={len(cyrillic)}, Hanzi={len(chinese_chars)}")

# Print a few sample texts to confirm
print("\nSample texts (first 20):")
for t in sample_texts[:20]:
    print(f"  {repr(t)}")

# Step 1: Name 詞庫 (non-dialogue)
name_glossary = {}
for item in flat_entries:
    marker = item['marker']
    text = item['text']
    if marker not in ['Message', 'Choice', 'ScrollText'] and text:
        # Check if text is just placeholders, numbers, etc.
        if not re.match(r'^[\d\s\-_]*$', text):
            name_glossary[text] = text

print(f"\nName Glossary entries count: {len(name_glossary)}")

# Let's save statistics and all flat entries to a file so we can chunk them easily
os.makedirs(".agent/scratch", exist_ok=True)
with open(".agent/stats.json", "w", encoding="utf-8") as f:
    json.dump({
        "source_lang": source_lang,
        "total_entries": len(flat_entries),
        "name_glossary_count": len(name_glossary)
    }, f, ensure_ascii=False, indent=2)

with open(".agent/scratch/flat_entries.json", "w", encoding="utf-8") as f:
    json.dump(flat_entries, f, ensure_ascii=False, indent=2)

print("Saved flat_entries.json and stats.json")

