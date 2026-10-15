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
    current_lines = []
    
    # We want to reconstruct the final translations mapping first
    translations = {}
    temp_id = None
    temp_lines = []
    
    for line in lines:
        match = re.match(r"^(\d+)[\.:]\s?(.*)", line)
        if match:
            if temp_id is not None:
                translations[temp_id] = "".join(temp_lines).rstrip('\n')
            temp_id = int(match.group(1))
            temp_lines = [match.group(2)]
        else:
            if temp_id is not None:
                temp_lines.append(line)
    if temp_id is not None:
        translations[temp_id] = "".join(temp_lines).rstrip('\n')
        
    # Check each reconstructed translation for suspicious text
    for eid, text in sorted(translations.items()):
        # Suspicious if contains keywords like "等等", "日文原文", "應該是", "備註", "翻譯" inside parentheses
        # or if it has english/chinese parentheses with "等等", "原文", "譯為", "翻譯", "應為"
        suspicious = False
        reasons = []
        
        # Check for brackets containing suspicious keywords
        for m in re.finditer(r'[\(（][^）\)]*[\)）]', text):
            bracket_content = m.group(0)
            for kw in ["等等", "原文", "譯為", "翻譯", "應為", "應該是", "注意", "括號", "對應"]:
                if kw in bracket_content:
                    suspicious = True
                    reasons.append(f"bracket containing '{kw}'")
                    
        # Check if "等等" or "原文" is outside brackets too
        if not suspicious:
            for kw in ["等等！", "日文原文是", "我們在翻譯時", "譯為"]:
                if kw in text:
                    suspicious = True
                    reasons.append(f"text containing '{kw}'")
                    
        if suspicious:
            print(f"Entry {eid} ({', '.join(reasons)}):")
            print(f"  [RAW]: {repr(text)}")
