import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

# Ensure directories exist
os.makedirs(".agent/scratch/chunks", exist_ok=True)

# Load flat entries
flat_entries_path = ".agent/scratch/flat_entries.json"
if not os.path.exists(flat_entries_path):
    print(f"Error: {flat_entries_path} does not exist.")
    exit(1)

with open(flat_entries_path, "r", encoding="utf-8") as f:
    flat_entries = json.load(f)

# Step 2 & 3: Find characters and objects
# We will analyze dialogue texts to find speaker prefixes.
# Pattern: e.g. "ウェイン：\n" or "ウェイン\n「"
speaker_counter = Counter()

for item in flat_entries:
    text = item['text']
    marker = item['marker']
    # Message markers are dialogues
    if marker == "Message" and text:
        # Match lines starting with a character name followed by a colon or quote
        # Examples: "ウェイン：\n", "ウェイン\n「", "ウェイン：「"
        match = re.match(r'^([^：\n\s「」\\]+)(：\n|：|:\n|:|「|\n「)', text)
        if match:
            sp = match.group(1).strip()
            # Exclude control characters or codes
            if sp and not re.search(r'[\\[\]\d]', sp):
                speaker_counter[sp] += 1

print("Detected active dialogue speakers:")
for sp, cnt in speaker_counter.most_common(10):
    print(f"  {sp}: {cnt} times")

# Filter speakers appearing at least 2 times for character dictionary
characters = [sp for sp, cnt in speaker_counter.items() if cnt >= 2]

# Step 1 Name Glossary translation drafts (translating placeholders for common RPG terms)
# We can draft translation pairs for characters/objects to assist the model
# For characters dictionary: "原文,譯文,對應原名,性別,年齡,性格,口吻,描述"
# Let's write character template
char_dict_csv = []
for char in characters:
    # Basic translation mapping drafts for common names if we recognize them
    trans = char
    if char == "ウェイン": trans = "韋恩"
    elif char == "医者": trans = "醫生"
    elif char == "スレイ": trans = "斯雷"
    elif char == "サリア": trans = "莎莉亞"
    elif char == "村長": trans = "村長"
    elif char == "少女": trans = "少女"
    elif char == "若者": trans = "年輕人"
    elif char == "男": trans = "男人"
    elif char == "女": trans = "女人"
    
    # Format: "原文,譯文,對應原名,性別,年齡,性格,口吻,描述"
    char_dict_csv.append(f'"{char}","{trans}","","","","","",""')

with open(".agent/scratch/character_dictionary_draft.csv", "w", encoding="utf-8") as f:
    f.write("\n".join(char_dict_csv))

print(f"\nSaved {len(char_dict_csv)} character entries to character_dictionary_draft.csv")

# For objects dictionary: "原文,譯文,類別,描述"
# We extract terms that are in Name Glossary (non-dialogue)
# Sort by length descending, and write a draft CSV
obj_candidates = []
for item in flat_entries:
    marker = item['marker']
    text = item['text']
    if marker not in ['Message', 'Choice', 'ScrollText'] and text:
        if not re.match(r'^[\d\s\-_]*$', text) and len(text) > 1:
            obj_candidates.append(text)

obj_counter = Counter(obj_candidates)
objects = [obj for obj, cnt in obj_counter.items() if cnt >= 1]

obj_dict_csv = []
for obj in objects[:50]: # Just output some common ones
    # Format: "原文,譯文,類別,描述"
    obj_dict_csv.append(f'"{obj}","{obj}","",""')

with open(".agent/scratch/object_dictionary_draft.csv", "w", encoding="utf-8") as f:
    f.write("\n".join(obj_dict_csv))

print(f"Saved object_dictionary_draft.csv with top items")

# Split flat_entries into chunks of 150
chunk_size = 150
chunks = [flat_entries[i:i + chunk_size] for i in range(0, len(flat_entries), chunk_size)]

for idx, chunk in enumerate(chunks):
    chunk_file = f".agent/scratch/chunks/chunk_{idx}.json"
    with open(chunk_file, "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False, indent=2)

print(f"Split {len(flat_entries)} entries into {len(chunks)} chunks in .agent/scratch/chunks/")
