import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("translated/translation.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Searching for all Chinese words containing Lagro variants ===")
for file_name, entries in data.items():
    for key, entry in entries.items():
        text = entry.get('text_to_translate', '')
        
        found = False
        for kw in ["拉格", "拉葛", "拉古", "拉哥"]:
            if kw in text:
                found = True
        
        if found:
            # Filter out the common companion character "拉格" (Ragu)
            # which appears in "拉格：" or "朝著拉格" etc.
            # But keep words that are longer, like "拉格羅..."
            # Let's just print anything that is NOT just "拉格"
            clean = text.replace("拉格投擲飛刀", "").replace("拉格", "")
            # If after removing "拉格", there's still "拉格", "拉葛", "拉古", "拉哥" or it contains "羅" or "巴"
            has_other = False
            for k in ["拉格", "拉葛", "拉古", "拉哥"]:
                if k in clean:
                    has_other = True
            if "羅帕斯" in text or "羅巴斯" in text or "魯帕斯" in text:
                has_other = True
                
            if has_other:
                print(f"File: {file_name}")
                print(f"Key: {repr(key)}")
                print(f"Val: {repr(text)}")
                print("-" * 50)
