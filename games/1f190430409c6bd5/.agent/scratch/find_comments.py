import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for b in [1, 2, 3, 4]:
    path = f".agent/scratch/translated_chunks/batch_{b}.txt"
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    print(f"\n=== Batch {b} ===")
    current_entry = None
    for line in lines:
        match = re.match(r"^(\d+)[\.:]\s?(.*)", line)
        if match:
            current_entry = match.group(1)
            content = match.group(2)
        else:
            content = line
            
        if "->" in content or "翻譯：" in content or "翻譯:" in content:
            print(f"Entry {current_entry}: {content.strip()}")
