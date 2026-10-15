import json
import os
import re
import sys

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = os.path.dirname(os.path.abspath(__file__))
translation_json_path = os.path.join(workspace_dir, "untranslated", "translation.json")
list_txt_path = os.path.join(workspace_dir, "untranslated", "translation_translated_list.txt")
output_paths = [
    os.path.join(workspace_dir, "untranslated", "translation_translated.json"),
    os.path.join(workspace_dir, "translated", "translation.json"),
    os.path.join(workspace_dir, "translated", "translation_translated.json")
]

if not os.path.exists(translation_json_path):
    print(f"Error: Original JSON not found at {translation_json_path}")
    sys.exit(1)

if not os.path.exists(list_txt_path):
    print(f"Error: Numbered translation list not found at {list_txt_path}")
    sys.exit(1)

print("Loading original JSON...")
with open(translation_json_path, 'r', encoding='utf-8') as f:
    orig_data = json.load(f)

print("Parsing translation list...")
with open(list_txt_path, 'r', encoding='utf-8') as f:
    content = f.read()

parts = re.split(r'^(\d+)\.\s', content, flags=re.MULTILINE)
translations_map = {}
for i in range(1, len(parts), 2):
    idx = int(parts[i])
    text = parts[i+1]
    if text.endswith('\n'):
        text = text[:-1]
    if text.endswith('\n'):
        text = text[:-1]
    if text.startswith('{') and text.endswith('}'):
        text = text[1:-1]
    translations_map[idx] = text

print(f"Loaded {len(translations_map)} translations from list.")

print("Reconstructing JSON...")
reconstructed_data = {}
global_id = 1

for filename, items in orig_data.items():
    reconstructed_data[filename] = {}
    for key, item_info in items.items():
        translated_text = translations_map.get(global_id, item_info.get("text_to_translate", ""))
        reconstructed_data[filename][key] = {
            "original_marker": item_info.get("original_marker", ""),
            "text_to_translate": translated_text
        }
        if "speaker_id" in item_info:
            reconstructed_data[filename][key]["speaker_id"] = item_info["speaker_id"]
        global_id += 1

for output_path in output_paths:
    parent_dir = os.path.dirname(output_path)
    os.makedirs(parent_dir, exist_ok=True)
    print(f"Saving reconstructed JSON to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reconstructed_data, f, ensure_ascii=False, indent=2)

print("Reconstruction complete!")
