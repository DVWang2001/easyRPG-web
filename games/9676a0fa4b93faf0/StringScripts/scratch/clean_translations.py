# -*- coding: utf-8 -*-
import os
import glob
import re

TRANS_DIR = "scratch/to_translate"
translated_files = glob.glob(os.path.join(TRANS_DIR, "*.translated.txt"))

# 替換規則
# 1. 刪除 \S[n] 控制代碼 (例如 \S[4], \S[2])
# 2. 將日文中點 \u30fb 替換為繁體中文中點 \u2027
# 3. 將日文半角中點 \uff65 替換為繁體中文中點 \u2027
# 4. 將日文波浪號 \u301c 替換為全角波浪號 \uff5e
# 5. 將雙箭頭 \u21d2 (⇒) 替換為單箭頭 → (U+2192)
# 6. 將日文漢字 剣 (U+5263) 替換為繁體 劍
# 7. 將日文漢字 内 (U+5185) 替換為繁體 內
# 8. 將日文漢字 撃 (U+6483) 替換為繁體 擊
# 9. 將日文漢字 数 (U+6570) 替換為繁體 數
# 10. 將日文長音 ー (U+30fc) 替換為全角減號 － (U+ff0d)
# 11. 將音符 ♪ (U+266a) 替換為波浪號 ～
# 12. 將 U+56af 替換為 喔
# 13. 將 U+561e (不相容口字旁字元) 替換為 囉
# 14. 將不相容字元 獵 (U+731f) 替換為繁體 獵 (U+7375)
# 15. 特別處理 鮎 (U+9b8e): 動畫中的 '鮎ッ' 替換為 '香魚ッ'，人名中的 '鮎' 替換為 '阿羽'
def clean_line(line):
    # 刪除 \S[n]
    line = re.sub(r'\\S\[\d+\]', '', line)
    
    # 替換不相容字元
    line = line.replace('\u30fb', '\u00b7')  # ・ -> · (Big5 標準全角中點)
    line = line.replace('\uff65', '\u00b7')  # ･ -> ·
    line = line.replace('\u2027', '\u00b7')  # 將舊有中點轉為 \u00b7
    line = line.replace('\u301c', '\uff5e')  # 〜 -> ～
    line = line.replace('\u21d2', '→')      # ⇒ -> →
    line = line.replace('\u5263', '劍')      # 剣 -> 劍
    line = line.replace('\u5185', '內')      # 内 -> 內
    line = line.replace('\u6483', '擊')      # 撃 -> 擊
    line = line.replace('\u6570', '數')      # 数 -> 數
    line = line.replace('\u30fc', '－')      # ー -> －
    line = line.replace('\u266a', '～')      # ♪ -> ～
    line = line.replace('\u56af', '喔')      # U+56af -> 喔
    line = line.replace('\u561e', '囉')      # U+561e -> 囉
    line = line.replace('\u731f', '獵')      # U+731f -> 獵
    
    # 鮎 (U+9b8e)
    line = line.replace('鮎ッ', '香魚ッ')
    line = line.replace('\u9b8e', '阿羽')    # 其餘的鮎替換為阿羽
    
    return line

fixed_count = 0
problems = []

for file_path in sorted(translated_files):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 清理內容
    cleaned = clean_line(content)
    
    # 檢查是否有 cp950 無法編碼的字元
    lines = cleaned.split('\n')
    for line_idx, line in enumerate(lines, 1):
        rest = line
        if '. ' in line:
            parts = line.split('. ', 1)
            rest = parts[1]
        
        # 剝離 [MARKER: Message] [FACE: ...]
        if rest.startswith("[MARKER: Message]"):
            rest = rest[len("[MARKER: Message]"):].lstrip(' ')
            if rest.startswith("[FACE:"):
                end_idx = rest.find(']')
                if end_idx != -1:
                    rest = rest[end_idx + 1:].lstrip(' ')
        elif rest.startswith("[TAG:"):
            end_idx = rest.find(']')
            if end_idx != -1:
                rest = rest[end_idx + 1:].lstrip(' ')
                
        # 檢查該行是否有無法編碼的字元
        for char in rest:
            try:
                char.encode('cp950')
            except UnicodeEncodeError:
                problems.append({
                    'file': os.path.basename(file_path),
                    'line_num': line_idx,
                    'char': char,
                    'char_hex': f"U+{ord(char):04X}",
                    'text': rest
                })
            
    if cleaned != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        fixed_count += 1

print(f"Cleaned {fixed_count} files.")
print(f"Remaining unencodable instances: {len(problems)}")
for p in problems[:50]:
    safe_text = p['text'].encode('cp950', errors='replace').decode('cp950')
    print(f"File: {p['file']}:{p['line_num']} | Char: {p['char_hex']} | Text: {safe_text}")
