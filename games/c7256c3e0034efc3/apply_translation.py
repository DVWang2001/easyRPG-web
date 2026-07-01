# -*- coding: utf-8 -*-
import json
import os
import re
import difflib

# 讀取本地翻譯對照 JSON 檔案
translation_map = {}
map_path = "translation_map.json"
if os.path.exists(map_path):
    with open(map_path, 'r', encoding='utf-8') as f:
        translation_map = json.load(f)
    print(f"Loaded {len(translation_map)} translation pairs from {map_path}")
else:
    print("Warning: translation_map.json not found!")

# 預先處理快取以供快速模糊匹配使用
cleaned_map = {}
for k, v in translation_map.items():
    cleaned_k = "".join(c for c in k if c.isalnum())
    if cleaned_k:
        cleaned_map[cleaned_k] = v

def clean_text(s):
    return "".join(c for c in s if c.isalnum())

# 尋找最佳翻譯匹配
def get_translation(text):
    if not text:
        return ""
        
    # 1. 精確匹配
    if text in translation_map:
        return translation_map[text]
        
    # 2. 清理後精確匹配 (去除標點、空格、換行等)
    cleaned_text = clean_text(text)
    if cleaned_text in cleaned_map:
        return cleaned_map[cleaned_text]
        
    # 3. 模糊匹配 (針對長句，長度 > 5)
    if len(text) > 5:
        matches = difflib.get_close_matches(cleaned_text, cleaned_map.keys(), n=1, cutoff=0.75)
        if matches:
            return cleaned_map[matches[0]]
            
    return None

# 用於處理未被 translation_map 顯式或模糊定義的後備翻譯
def custom_translate(text, marker, speaker):
    matched = get_translation(text)
    if matched is not None:
        return matched
        
    # 套用自動正則規則
    # 1. 藥草 / 明靈草 / 戰鬥 / 擊破 / 士兵
    m = re.match(r'^薬草(\d+)$', text)
    if m: return f"藥草{m.group(1)}"
    m = re.match(r'^明霊草(\d+)$', text)
    if m: return f"明靈草{m.group(1)}"
    m = re.match(r'^戦闘(\d+)(\s+.*)?$', text)
    if m:
        suffix = m.group(2) if m.group(2) else ""
        return f"戰鬥{m.group(1)}{suffix}"
    m = re.match(r'^撃破(\d+)$', text)
    if m: return f"擊破{m.group(1)}"
    m = re.match(r'^兵士(\d+)$', text)
    if m: return f"士兵{m.group(1)}"
    m = re.match(r'^志願兵([0-9ⅠⅡⅢ]+)$', text)
    if m: return f"志願兵{m.group(1)}"
    m = re.match(r'^コープス([0-9ⅠⅡⅢ]+)$', text)
    if m: return f"食屍鬼{m.group(1)}"
    m = re.match(r'^キーパー([0-9ⅠⅡⅢ]+)$', text)
    if m: return f"守護者{m.group(1)}"
    m = re.match(r'^ゴースト([0-9ⅠⅡⅢ]+)$', text)
    if m: return f"幽靈{m.group(1)}"
    m = re.match(r'^小部屋(\d+)$', text)
    if m: return f"小房間{m.group(1)}"
    m = re.match(r'^民家(\d+)$', text)
    if m: return f"民房{m.group(1)}"
    m = re.match(r'^(\d+)階$', text)
    if m: return f"{m.group(1)}樓"
    m = re.match(r'^(\d+)階通路$', text)
    if m: return f"{m.group(1)}樓通道"

    # 特殊代碼處理與字詞繁體化
    replaced = text
    replacements = {
        '薬草': '藥草', '明霊草': '明靈草', '天命草': '天命草',
        '戦闘': '戰鬥', '撃破': '擊破', '攻撃': '攻擊', '防御': '防禦',
        '辞書': '字典', '地図': '地圖', '隠れ家': '據點',
        '死者の森': '亡者之森', '神世の森': '神世之森',
        'モリガン': '莫里根', 'オスロウ': '奧斯洛', 'モラズ': '莫拉茲',
        'ヴォル': '沃爾', 'ティルファ': '蒂爾法', 'バンダナ': '班達納',
        'スオウ': '蘇芳', 'ロザネス': '羅薩內斯', 'エナ': '艾娜', 'アレフ': '阿雷夫',
        'モンスター': '魔物', '兵士': '士兵', 'レジスタンス': '反抗軍',
        '部屋': '房間', '通路': '通道', '基地': '基地', '階段': '樓梯',
        '回復': '恢復', '手に入れた': '獲得了', '見つけた': '發現了',
        '仲間': '同伴', '記憶': '記憶', '仕事': '工作', '手紙': '信件',
        '帝国': '帝國', '人質': '人質', '混乱': '混亂', '作戦': '作戰',
        '戦う': '戰鬥', '逃げる': '逃跑', '勝った': '贏了', '負けた': '輸了',
        '終了': '結束', '開始': '開始', '表示': '顯示', '選択': '選擇',
        'メニュー': '選單', 'コマンド': '指令', 'アイテム': '道具',
        'セーブ': '存檔', 'ロード': '讀檔', 'ファイル': '檔案',
        'ゲーム': '遊戲', 'システム': '系統',
    }
    for k, v in replacements.items():
        replaced = replaced.replace(k, v)
        
    replaced = re.sub(r'よ$', '啊', replaced)
    replaced = re.sub(r'ね$', '呢', replaced)
    replaced = re.sub(r'か？$', '嗎？', replaced)
    replaced = re.sub(r'だ。$', '。', replaced)
    replaced = re.sub(r'の$', '的', replaced)

    return replaced

# 計算全/半形字數寬度
def count_width(text):
    code_pattern = r'\\[a-zA-Z]+(?:\[\d+\])?|\\[><!\.\^\|_]'
    cleaned = re.sub(code_pattern, '', text)
    width = 0.0
    for char in cleaned:
        if ord(char) > 255:
            width += 1.0
        else:
            width += 0.5
    return width

# 將文字依上限換行
def wrap_line(line, limit):
    if count_width(line) <= limit:
        return line
    code_pattern = r'(\\[a-zA-Z]+(?:\[\d+\])?|\\[><!\.\^\|_]|.)'
    tokens = re.findall(code_pattern, line)
    
    wrapped_lines = []
    current_line = []
    current_width = 0.0
    
    for token in tokens:
        if token.startswith('\\'):
            token_width = 0.0
        else:
            token_width = 1.0 if ord(token) > 255 else 0.5
            
        if current_width + token_width > limit:
            wrapped_lines.append("".join(current_line))
            current_line = [token]
            current_width = token_width
        else:
            current_line.append(token)
            current_width += token_width
            
    if current_line:
        wrapped_lines.append("".join(current_line))
        
    return "\\n".join(wrapped_lines)

# 主流程
def main():
    json_path = r"untranslated\translation.json"
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 建立 translated 資料夾
    os.makedirs("translated", exist_ok=True)

    translated_data = {}
    total_entries = 0
    output_entries = []

    for file_name, file_data in data.items():
        translated_data[file_name] = {}
        for original_text, item_data in file_data.items():
            total_entries += 1
            text = item_data.get("text_to_translate", "")
            marker = item_data.get("original_marker", "")
            speaker = item_data.get("speaker_id", "NONE")

            # 1. 判斷是否需要翻譯
            if re.match(r'^[\d\s\-\+\*\/\=\%\@\#\$\^\&\(\)\[\]\{\}\:\;\'\"\,\.\<\>\?\/\\|~`!_]*$', text) or re.match(r'^EV\d+$', text) or re.match(r'^[A-Z0-9\s_\-\!\?\.（）\(\)]+$', text):
                translated_text = "{原文}"
            else:
                # 2. 進行翻譯
                translated_text = custom_translate(text, marker, speaker)
                
                # 3. 標點轉換
                translated_text = translated_text.replace('!', '！').replace('?', '？').replace(',', '，')
                if '\\' not in translated_text:
                    translated_text = translated_text.replace('.', '。')
                translated_text = translated_text.replace('『', '「').replace('』', '」')
                translated_text = translated_text.replace('、', '，').replace('〜', '~').replace('～', '~').replace('・', '·').replace('‧', '·')
                
                # Big5 相容性過濾
                replacements = {
                    '↔': '←→',
                    '⇔': '←→',
                }
                for bad, good in replacements.items():
                    translated_text = translated_text.replace(bad, good)

                
                # 4. 處理自動換行
                if marker == "Message":
                    has_face = speaker not in ["NARRATION", "NONE", "SYSTEM", ""]
                    limit = 19 if has_face else 25
                    
                    lines = translated_text.split('\\n')
                    wrapped_lines = [wrap_line(l, limit) for l in lines]
                    translated_text = '\\n'.join(wrapped_lines)

            # 寫入翻譯後的 JSON 結構
            translated_data[file_name][original_text] = {
                "text_to_translate": text,
                "translation": translated_text if translated_text != "{原文}" else text,
                "original_marker": marker,
                "speaker_id": speaker
            }

            # 收集譯文
            output_entries.append(f"{total_entries}. {translated_text}")

    # 輸出至 translated/translation_translated.json
    output_json_path = r"translated\translation_translated.json"
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully wrote {output_json_path}")

    # 輸出至 gemini_output.txt
    with open("gemini_output.txt", 'w', encoding='utf-8') as f:
        for entry in output_entries:
            f.write(entry + "\n")
    print("Successfully wrote gemini_output.txt")
    print(f"Total processed entries: {total_entries}")

if __name__ == '__main__':
    main()
