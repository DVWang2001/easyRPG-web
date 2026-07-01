import json
import os

total = 0
for i in range(21):
    path = f".agent/scratch/chunks/chunk_{i}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"chunk_{i}.json: {len(data)} entries (from {total+1} to {total+len(data)})")
            total += len(data)
print(f"Total entries: {total}")
