import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load original translation.json structure
json_path = r"untranslated\translation.json"
if not os.path.exists(json_path):
    print(f"Error: {json_path} does not exist.")
    exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    translation_data = json.load(f)

# 2. Load flat_entries.json to map sequential IDs to keys
flat_entries_path = ".agent/scratch/flat_entries.json"
with open(flat_entries_path, "r", encoding="utf-8") as f:
    flat_entries = json.load(f)

# 3. Load all translated batches
translations = {}
current_id = None
current_lines = []

for b in [1, 2, 3, 4]:
    path = f".agent/scratch/translated_chunks/batch_{b}.txt"
    if not os.path.exists(path):
        print(f"Error: Batch file {path} not found.")
        exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        match = re.match(r"^(\d+)[\.:]\s?(.*)", line)
        if match:
            if current_id is not None:
                translations[current_id] = "".join(current_lines).rstrip('\n')
            current_id = int(match.group(1))
            current_lines = [match.group(2)]
        else:
            if current_id is not None:
                current_lines.append(line)

# Save the last entry
if current_id is not None:
    translations[current_id] = "".join(current_lines).rstrip('\n')

print(f"Loaded {len(translations)} translated entries from batch files.")

# Define manual fixes for entries that had inline comments/self-corrections across all batches
manual_fixes = {
    # Batch 1
    189: "男人：\n　老夫的賭博生涯已經有 80 年了。\n　可還不會輸給年輕一輩呢。",
    213: "？：\n　米奇塔前輩！！！",
    265: "韋恩：\n　（差不多該來了吧……）",
    271: "米奇塔：\n　（帥、帥呆了……）",
    274: "海姆雷克：\n　糟、糟糕……\\!總之先逃走！！！",
    360: "韋恩：\n　明白了。那樣就行。",
    551: "薩菲爾斯：\n　既然如此，我就如你所願吧……",
    671: "韋恩：\n　比起那個，有件事讓我挺在意的……。",
    679: "韋恩：\n　沒、沒有……\\!怎麼可能嘛……哈哈……",
    733: "馬里斯·薩汀：\n　嗯？？？可是明明已經沒勝算了啊？",

    # Batch 2
    941: "\\>韋恩：\\<\n\u3000\\>布。\\<\n\\>拉格：\\<\n\u3000\\>石頭。\\<",
    946: "啊啊啊啊啊……",
    1148: "沒想到，你們居然就是侵入者……",
    1154: "你在、\\.在胡說些什麼傻話……",
    1243: "該不會在油燈裡面吧……\\|果然還是沒有啊……",
    1256: "是啊……\\!瓦迪斯師父。",
    1353: "嗯……竟然會通到這種地方啊……",

    # Batch 3
    1932: "對敵方單體造成水屬性的傷害。",

    # Batch 4
    2318: "D·哈許的房間",
    2422: "玩家葫蘆",
    2550: "確認消滅警備兵（右）",
    2691: "對手剩餘"
}

# 4. Map back to original structure
success_count = 0
untranslated_count = 0

for idx, item in enumerate(flat_entries, 1):
    file_name = item['file']
    entry_key = item['key']
    original_text = item['text']
    
    # Check if manual override exists
    if idx in manual_fixes:
        final_text = manual_fixes[idx]
        success_count += 1
    else:
        translated_text = translations.get(idx)
        
        if translated_text is None:
            print(f"Warning: No translation found for ENTRY {idx} (file: {file_name}, key: {entry_key})")
            continue
        
        # Handle {原文} placeholder
        if translated_text == "{原文}":
            final_text = original_text
            untranslated_count += 1
        else:
            final_text = translated_text
            success_count += 1
            
    # Convert literal \n to actual newlines to prevent RPG Maker from misinterpreting \n as \N
    final_text = final_text.replace(r"\n", "\n").replace("\\n", "\n")
    
    # Replace Japanese kanji variants or simplified chars that might render as "?" in RPG Maker Big5/GBK font
    char_replacements = {
        "\u8aac": "\u8aaa",  # 説 (JP) -> 說 (TC)
        "\u8b6a": "\u8aaa",  # 说 (SC) -> 說 (TC)
        "\u6e80": "\u6eff",  # 満 (JP) -> 滿 (TC)
        "\u5bfe": "\u5c0d",  # 対 (JP) -> 對 (TC)
        "\u92ed": "\u9231",  # 鋭 (JP) -> 銳 (TC)
        "\u8131": "\u812b",  # 脱 (JP) -> 脫 (TC)
        "嚯": "呵"           # 嚯 (生僻字) -> 呵 (常用字，修復老爺爺笑聲 ??? 亂碼)
    }
    for jp_char, tc_char in char_replacements.items():
        final_text = final_text.replace(jp_char, tc_char)
        
    # Standardize character names to unify translation inconsistencies
    final_text = final_text.replace("塞格曼", "塞古梅因")
    
    # Standardize God names to unify "拉格羅帕斯" and "拉格羅帕斯神"
    final_text = final_text.replace("拉格羅帕斯神", "拉格羅帕斯")

    # Standardize parodied Romeo & Juliet name translations
    final_text = final_text.replace("茉莉", "茱麗")
    final_text = final_text.replace("羅蜜", "羅密")

    # Force translate leftover Japanese character names in values to prevent ????
    final_text = final_text.replace("サフィールス", "薩菲爾斯")
    final_text = final_text.replace("・點數計算方法如下", "•點數計算方法如下")

    # Restore missing name prefixes in dialogues for Romi & Juri if stripped during translation
    if entry_key.startswith("ロミ：\n") and not final_text.startswith("羅密："):
        final_text = "羅密：\n" + final_text
    elif entry_key.startswith("ジュリ：\n") and not final_text.startswith("茱麗："):
        final_text = "茱麗：\n" + final_text

    # Force auto-translate standalone "ウェイン：" to prevent rendering as ????
    if entry_key in ["ウェイン：", "ウェイン:"]:
        final_text = "韋恩："
        
    # Write back into translation_data dict
    if file_name in translation_data and entry_key in translation_data[file_name]:
        translation_data[file_name][entry_key]['text_to_translate'] = final_text
    else:
        print(f"Error: Key mismatch at ENTRY {idx} (file: {file_name}, key: {entry_key})")

print(f"Successfully processed {success_count} translations, kept {untranslated_count} original text entries.")

# 5. Save back to output paths (especially translated/translation.json)
output_paths = [
    r"untranslated\translation.json",
    r"translated\translation.json",
    r"translation.json"
]

for out_path in output_paths:
    dir_name = os.path.dirname(out_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(translation_data, f, ensure_ascii=False, indent=2)
    print(f"Saved completed translation file to: {out_path}")

print("Translation restoration finished successfully.")
