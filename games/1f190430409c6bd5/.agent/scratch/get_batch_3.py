import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

entries = []
for i in range(10, 15):
    chunk_path = f".agent/scratch/chunks/chunk_{i}.json"
    if os.path.exists(chunk_path):
        with open(chunk_path, "r", encoding="utf-8") as f:
            entries.extend(json.load(f))

output_path = ".agent/scratch/batch_3_originals.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"Total entries in this batch: {len(entries)}\n")
    for idx, entry in enumerate(entries, 1501):
        f.write(f"--- ENTRY {idx} ({entry['marker']}) ---\n")
        f.write(f"{entry['text']}\n")

print(f"Saved {len(entries)} entries to {output_path}")
