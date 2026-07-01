# -*- coding: utf-8 -*-
import os
import re
import urllib.request
import urllib.parse
import json
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

UTF8_BOM = b'\xef\xbb\xbf'

PRE_REPLACEMENTS = {
    "イゾウ": "以藏",
    "ナポレオン": "拿破崙",
    "ダンディ": "丹迪",
    "オスカー": "奧斯卡",
    "ﾁｮﾁｮﾘｰﾅ": "喬喬莉娜",
    "チョチョリーナ": "喬喬莉娜",
    "リード＝アレン": "里德·艾倫",
    "リード": "里德",
    "オンドレ": "安德烈",
    "ベア": "貝爾",
    "マサル": "阿勝",
    "アルフ": "阿爾夫",
}

QUICK_CHOICES = {
    "はい": "是",
    "いいえ": "否",
    "やる": "做",
    "やらない": "不做",
    "やめる": "放棄",
    "やめない": "不放棄",
    "はい。": "是。",
    "いいえ。": "否。",
    "コーヒー": "咖啡",
    "ウーロン茶": "烏龍茶",
    "ビール": "啤酒",
    "紅茶": "紅茶",
    "オレンジジュース": "柳橙汁",
    "ジュース": "果汁",
    "お茶": "茶",
    "水": "水",
    "ミネラルウォーター": "礦泉水",
    "日本酒": "日本酒",
    "ワイン": "葡萄酒",
    "ウイスキー": "威士忌",
    "カクテル": "雞尾酒",
}

def translate_text(text):
    if not text.strip():
        return text
    
    # 預處理
    for ja, zh in PRE_REPLACEMENTS.items():
        text = text.replace(ja, zh)
        
    if not re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):
        return text
        
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        translated_text = "".join([part[0] for part in data[0] if part[0]])
        
        # 簡單修復代碼（雖然 Choice 中一般不含有 control code）
        translated_text = re.sub(r'\\\s*[Nn]\s*\[\s*(\d+)\s*\]', r'\\N[\1]', translated_text)
        return translated_text
    except Exception as e:
        print(f"  [Choice Translation Error] {text}: {e}")
        return text

def process_file_choices(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    if raw.startswith(UTF8_BOM):
        text = raw[3:].decode('utf-8')
    else:
        text = raw.decode('utf-8')
        
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    
    modified = False
    in_choice = False
    choice_start_idx = -1
    choice_options = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == '#Choice#':
            in_choice = True
            choice_start_idx = i
            choice_options = []
            i += 1
            continue
            
        if in_choice:
            if line.strip() == '##':
                in_choice = False
                translated_options = []
                for opt in choice_options:
                    opt_strip = opt.strip()
                    if opt_strip in QUICK_CHOICES:
                        translated_options.append(QUICK_CHOICES[opt_strip])
                        modified = True
                    elif re.search(r'[\u3040-\u309F\u30A0-\u30FF]', opt):
                        safe_opt = opt_strip.encode('cp950', errors='replace').decode('cp950')
                        print(f"  Translating choice: {safe_opt} in {os.path.basename(filepath)}")
                        trans = translate_text(opt_strip)
                        translated_options.append(trans)
                        modified = True
                        time.sleep(0.15)
                    else:
                        translated_options.append(opt)
                        
                # 替換回 lines 陣列
                lines[choice_start_idx+1 : i] = translated_options
                # 重設索引
                i = choice_start_idx + 1 + len(translated_options)
            else:
                choice_options.append(line)
        i += 1
        
    if modified:
        new_text = '\r\n'.join(lines)
        with open(filepath, 'wb') as f:
            f.write(UTF8_BOM + new_text.encode('utf-8'))
        print(f"  -> Updated choices in: {os.path.basename(filepath)}")

def main():
    print("Scanning Map text files for #Choice# blocks...")
    map_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith("Map") and f.endswith(".txt")])
    print(f"Found {len(map_files)} Map files in output directory.")
    
    for idx, fname in enumerate(map_files, 1):
        fpath = os.path.join(OUTPUT_DIR, fname)
        process_file_choices(fpath)
        
    print("Choice translation completed successfully!")

if __name__ == "__main__":
    main()
