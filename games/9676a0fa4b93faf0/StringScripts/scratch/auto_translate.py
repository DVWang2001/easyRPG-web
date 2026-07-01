# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANS_DIR = os.path.join(SCRIPT_DIR, "to_translate")

UTF8_BOM = b'\xef\xbb\xbf'

# 譯名保護 Placeholder - 採用純數字序列，避免被 Google 音譯或翻譯
PLACEHOLDERS = [
    ("リード＝アレン", "99906"),
    ("リード", "99907"),
    ("イゾウ", "99901"),
    ("ナポレオン", "99902"),
    ("ダンディ", "99903"),
    ("オスカー", "99904"),
    ("ﾁｮﾁｮﾘｰﾅ", "99905"),
    ("チョチョリーナ", "99905"),
    ("オンドレ", "99908"),
    ("ベア", "99909"),
    ("マサル", "99910"),
    ("アルフ", "99911"),
]

# 後處理正則替換 - 容許 Google 翻譯在數字間插入空格
POST_PATTERNS = {
    r'9\s*9\s*9\s*0\s*1': "以藏",
    r'9\s*9\s*9\s*0\s*2': "拿破崙",
    r'9\s*9\s*9\s*0\s*3': "丹迪",
    r'9\s*9\s*9\s*0\s*4': "奧斯卡",
    r'9\s*9\s*9\s*0\s*5': "喬喬莉娜",
    r'9\s*9\s*9\s*0\s*6': "里德·艾倫",
    r'9\s*9\s*9\s*0\s*7': "里德",
    r'9\s*9\s*9\s*0\s*8': "安德烈",
    r'9\s*9\s*9\s*0\s*9': "貝爾",
    r'9\s*9\s*9\s*1\s*0': "阿勝",
    r'9\s*9\s*9\s*1\s*1': "阿爾夫",
}

def fix_control_codes(text):
    # 修復 \N[x]
    text = re.sub(r'\\\s*[Nn]\s*\[\s*(\d+)\s*\]', r'\\N[\1]', text)
    # 修復 \C[x]
    text = re.sub(r'\\\s*[Cc]\s*\[\s*(\d+)\s*\]', r'\\C[\1]', text)
    # 修復 \V[x]
    text = re.sub(r'\\\s*[Vv]\s*\[\s*(\d+)\s*\]', r'\\V[\1]', text)
    # 修復 \.
    text = re.sub(r'\\\s*\.', r'\\.', text)
    # 修復 \!
    text = re.sub(r'\\\s*\!', r'\\!', text)
    # 修復 \|
    text = re.sub(r'\\\s*\|', r'\\|', text)
    # 修復 \^
    text = re.sub(r'\\\s*\^', r'\\^', text)
    # 修復 $g
    text = re.sub(r'\$\s*[Gg]', r'$g', text)
    return text

def apply_post_replacements(text):
    for pattern, zh_name in POST_PATTERNS.items():
        text = re.sub(pattern, zh_name, text)
    return text

def translate_text_fallback(text):
    if not text.strip():
        return text
        
    for ja_name, placeholder in PLACEHOLDERS:
        text = text.replace(ja_name, placeholder)
        
    # 如果整批已經沒有日文字元，且不包含人名 Placeholder，直接解鎖返回
    if not re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text) and not any(re.search(pat, text) for pat in POST_PATTERNS.keys()):
        return apply_post_replacements(text)
        
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        translated_parts = []
        for part in data[0]:
            if part[0]:
                translated_parts.append(part[0])
        translated_text = "".join(translated_parts)
        translated_text = fix_control_codes(translated_text)
        translated_text = apply_post_replacements(translated_text)
        time.sleep(0.2)
        return translated_text
    except Exception as e:
        print(f"    [WARN] Fallback translation error for '{text}': {e}")
        return apply_post_replacements(text)

def translate_batch(texts):
    if not texts:
        return []
    
    # 預處理保護人名
    processed_texts = []
    for text in texts:
        if not text.strip():
            processed_texts.append("")
            continue
        
        t = text
        for ja_name, placeholder in PLACEHOLDERS:
            t = t.replace(ja_name, placeholder)
        processed_texts.append(t)
        
    # 合併發送
    combined_text = "\n".join(processed_texts)
    
    # 如果整批已經沒有日文字元，且不包含人名 Placeholder，直接解鎖返回
    if not re.search(r'[\u3040-\u309F\u30A0-\u30FF]', combined_text) and not any(re.search(pat, combined_text) for pat in POST_PATTERNS.keys()):
        return [apply_post_replacements(t) for t in processed_texts]
        
    try:
        q = urllib.parse.quote(combined_text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=zh-TW&dt=t&q={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=15)
        data = json.loads(response.read().decode('utf-8'))
        
        translated_parts = []
        for part in data[0]:
            if part[0]:
                translated_parts.append(part[0])
        translated_combined = "".join(translated_parts)
        
        # 後處理：修復被破壞的控制代碼
        translated_combined = fix_control_codes(translated_combined)
        
        # 拆分回列表
        translated_lines = translated_combined.split('\n')
        
        # 如果拆分後的行數與輸入不符，用 fallback 退回逐行翻譯
        if len(translated_lines) != len(texts):
            print(f"  [WARN] Batch translation count mismatch (sent {len(texts)}, got {len(translated_lines)}). Falling back to line-by-line.")
            results = []
            for t in processed_texts:
                results.append(translate_text_fallback(t))
            return results
            
        return [apply_post_replacements(line) for line in translated_lines]
    except Exception as e:
        print(f"  [ERROR] Batch translation failed: {e}. Falling back to line-by-line.")
        results = []
        for t in processed_texts:
            results.append(translate_text_fallback(t))
        return results

def read_file(path):
    with open(path, 'rb') as f:
        raw = f.read()
    if raw.startswith(UTF8_BOM):
        text = raw[3:].decode('utf-8')
    else:
        text = raw.decode('utf-8')
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return lines

def translate_file(trans_file):
    translated_file = trans_file.replace(".trans.txt", ".translated.txt")
    
    print(f"Translating {os.path.basename(trans_file)}...")
    lines = read_file(trans_file)
    
    entries = []
    for line in lines:
        m = re.match(r'^(\d+)\.\s*(\[MARKER:\s*Message\]\s*(?:\[FACE:\s*[^\]]+\])?|\[TAG:\s*[^\]]+\])\s*(.*)', line)
        if m:
            num = m.group(1)
            marker = m.group(2)
            content = m.group(3)
            entries.append({
                'is_header': True,
                'prefix': f"{num}. {marker} ",
                'text': content
            })
        else:
            entries.append({
                'is_header': False,
                'prefix': "",
                'text': line
            })
            
    # 提取待翻譯文本
    texts_to_translate = [entry['text'] for entry in entries]
    
    # 批次翻譯
    translated_texts = []
    batch_size = 40
    for i in range(0, len(texts_to_translate), batch_size):
        batch = texts_to_translate[i:i+batch_size]
        batch_translated = translate_batch(batch)
        translated_texts.extend(batch_translated)
        time.sleep(0.3) # 批次間微延遲
        
    # 重組
    reconstructed_lines = []
    for entry, trans_text in zip(entries, translated_texts):
        reconstructed_lines.append(f"{entry['prefix']}{trans_text}")
        
    # 寫入翻譯結果
    text = '\r\n'.join(reconstructed_lines)
    data = UTF8_BOM + text.encode('utf-8')
    with open(translated_file, 'wb') as f:
        f.write(data)
    print(f"  -> Saved translation to {os.path.basename(translated_file)}")
    return True

def main():
    if not os.path.exists(TRANS_DIR):
        print(f"Error: {TRANS_DIR} does not exist. Run export_all.py first.")
        sys.exit(1)
        
    trans_files = sorted([os.path.join(TRANS_DIR, f) for f in os.listdir(TRANS_DIR) if f.endswith(".trans.txt")])
    print(f"Found {len(trans_files)} files to translate.")
    
    success_count = 0
    
    for idx, fpath in enumerate(trans_files, 1):
        try:
            print(f"[{idx}/{len(trans_files)}] Processing...")
            translate_file(fpath)
            success_count += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"\nStopped translation process due to error: {e}")
            print("You can rerun this script to resume translation.")
            sys.exit(1)
            
    print("-" * 60)
    print(f"Translation run finished.")
    print(f"Successfully translated: {success_count} files.")

if __name__ == "__main__":
    main()
