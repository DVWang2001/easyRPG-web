# -*- coding: utf-8 -*-
import os

def extract_names(trans_file):
    names = []
    with open(trans_file, 'r', encoding='utf-8') as f:
        for line in f:
            if "[TAG: Name]" in line:
                name = line.split("[TAG: Name]")[1].strip()
                if name:
                    names.append(name)
    return names

items_names = extract_names("scratch/to_translate/Database_Items.txt.trans.txt")
skills_names = extract_names("scratch/to_translate/Database_Skills.txt.trans.txt")

with open("scratch/extracted_names.txt", "w", encoding="utf-8") as f:
    f.write("--- Items Names ---\n")
    for n in items_names:
        f.write(n + "\n")
    f.write("\n--- Skills Names ---\n")
    for n in skills_names:
        f.write(n + "\n")

print("Done! Extracted to scratch/extracted_names.txt")
