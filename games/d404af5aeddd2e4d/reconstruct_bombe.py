import json
import re
import os

# 1. 讀取譯文
text_path = "translated_text.txt"
with open(text_path, "r", encoding="utf-8") as f:
    content = f.read()

# 為了防止 windows 換行符干擾，先把 \r\n 轉成 \n
content = content.replace("\r\n", "\n")

# 用正則提取
items = re.findall(r'<<<ITEM (\d+)>>>\n(.*?)(?=\n<<<ITEM \d+>>>|\Z)', content, re.DOTALL)
translated_dict = {int(num): text for num, text in items}

print(f"Loaded {len(translated_dict)} translated items.")

# 2. 讀取原始 JSON
json_path = os.path.join("untranslated", "translation.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. 依序替換
counter = 1
for file_key, file_data in data.items():
    for text_key, item in file_data.items():
        if counter in translated_dict:
            item["text_to_translate"] = translated_dict[counter]
        counter += 1

print(f"Replaced {counter-1} items.")

# 4. 寫入到 translated/translation_translated.json
out_dir = "translated"
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "translation_translated.json")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Successfully saved to {out_path}")
