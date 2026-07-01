# -*- coding: utf-8 -*-
"""
Soul of Dandizm - AI 高品質翻譯腳本
使用 Google Gemini API 進行全遊戲文本翻譯

使用方法：
  1. 安裝依賴：pip install google-generativeai
  2. 設定 API Key（任選一種）：
     a. 環境變數：set GEMINI_API_KEY=your_key_here
     b. 直接修改本腳本底部的 API_KEY 變數
  3. 執行：python scratch/ai_translate.py
  4. 執行完成後，執行 import_all.py 將翻譯結果寫回遊戲檔案

API Key 取得：https://aistudio.google.com/app/apikey（免費）
"""

import os
import re
import sys
import json
import time

# ============================================================
# 設定
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANS_DIR = os.path.join(SCRIPT_DIR, "to_translate")
UTF8_BOM = b'\xef\xbb\xbf'

# 在此填入 API Key（或設環境變數 GEMINI_API_KEY）
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini 模型設定
GEMINI_MODEL = "gemini-2.0-flash"

# 每批翻譯的最大行數（避免超出 token 限制）
BATCH_SIZE = 30

# ============================================================
# 遊戲背景知識 / 角色詞典（用於翻譯提示詞）
# ============================================================

GAME_CONTEXT = """
你正在翻譯一款 RPG Maker 2000 製作的日本 RPG 遊戲《Soul of Dandizm》（丹迪主義之魂）的遊戲腳本。

【遊戲背景】
這是一款充滿個性與幽默的 RPG，主題圍繞「丹迪主義」（Dandyism）。

【固定人名對照表】（嚴格遵守，不可更改）
- イゾウ / イゾウ「 → 以藏
- オスカー / オスカー「 → 奧斯卡
- DANDY / DANDY「 → 丹迪（此為主角之一，頭銜為「丹迪之神」）
- ﾁｮﾁｮﾘｰﾅ / チョチョリーナ / ﾁｮﾁｮﾘｰﾅ「 → 喬喬莉娜（魔導師）
- 流漸 / 流漸「 → 流漸（此為漢字名，保持原樣即可）
- オンドレ → 安德烈（稱謂「アニキ」= 大哥）
- ベア → 貝爾（槍手）
- マサル → 阿勝（神殿騎士）
- 真っ黒 → 漆黑（黑子角色）
- アルフ → 阿爾夫
- リード＝アレン / リード → 里德・艾倫 / 里德
- ナポレオン → 拿破崙
- ウィルス → 病毒（此為遊戲中的敵人實體名，翻譯為「病毒」）

【職業/頭銜對照】
- 傭兵 → 傭兵
- 隊長 → 隊長
- ダンディの神 → 丹迪之神
- 魔導師 → 魔導師
- オリジナル → 原型體
- アニキ → 大哥
- ガンマン → 槍手
- 神殿騎士 → 神殿騎士
- 黒子 → 黑子

【重要控制代碼說明】（翻譯時必須原樣保留，不可修改或刪除）
- \\S[n] → 表情切換指令（如 \\S[1]、\\S[2] 等）
- \\N[n] → 顯示角色名稱
- \\C[n] → 顯示顏色
- \\V[n] → 顯示變數值
- \\. → 短暫停頓
- \\| → 等待按鍵
- \\! → 不等待
- \\^ → 不顯示對話框
- $g → 顯示金錢視窗
- 這些代碼必須完整保留在翻譯結果的對應位置。

【翻譯風格要求】
- 翻譯成繁體中文（台灣用語）
- 保持角色各自的說話個性：
  * 以藏：冷靜沉穩，簡短有力
  * 奧斯卡：領袖風範，較正式
  * 丹迪：中二/帥氣口吻，誇張的英雄主義
  * 喬喬莉娜：俏皮活潑的女性口吻，結尾常用「$g」（表示吐舌）
  * 流漸：神秘莫測
  * 安德烈：大哥風格，粗獷
- 戰鬥訊息使用簡練的動詞片語（如「受到○○點傷害！」）
- 商店對話保持禮貌但自然的口吻
- 物品/技能名稱盡量簡潔（考慮顯示字元限制）
"""

TRANSLATION_INSTRUCTION = """
請將以下日文遊戲文本翻譯成繁體中文。

規則：
1. 嚴格遵守上方角色名稱對照表，不可自行翻譯人名
2. \\S[n]、\\N[n]、\\C[n]、\\V[n]、\\.、\\|、\\!、\\^、$g 等控制代碼必須完整保留於翻譯結果中
3. 「流漸「」「イゾウ「」等角色名稱後接「「」的格式，翻譯後改為 角色名「（保留引號作為說話者標記）
4. 行與行之間用換行分隔，輸出行數必須與輸入行數完全相同
5. 若某行完全不需要翻譯（如已是中文、數字、英文符號），原樣輸出
6. 不要加任何解釋、註解或多餘文字，只輸出翻譯結果

待翻譯文本（每行對應一行輸出）：
"""

# ============================================================
# 初始化 Gemini
# ============================================================

def init_gemini():
    try:
        import google.generativeai as genai
    except ImportError:
        print("[ERROR] 未安裝 google-generativeai 套件")
        print("請執行：pip install google-generativeai")
        sys.exit(1)
    
    if not API_KEY:
        print("[ERROR] 未設定 GEMINI_API_KEY")
        print("請設定環境變數 GEMINI_API_KEY，或在腳本中直接填入 API Key")
        print("取得免費 API Key：https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=GAME_CONTEXT
    )
    return model

# ============================================================
# 翻譯核心函式
# ============================================================

def translate_lines_with_gemini(model, lines):
    """使用 Gemini 翻譯一批文字行，返回等量的翻譯結果行"""
    if not lines:
        return []
    
    # 完全空白或無日文的行，直接跳過翻譯
    def needs_translation(line):
        if not line.strip():
            return False
        # 含日文假名
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', line):
            # 但「流漸」是漢字，且是角色名，算需要翻譯（含「」標記）
            return True
        return False
    
    # 建立索引映射：哪些行需要翻譯
    indices_to_translate = [i for i, l in enumerate(lines) if needs_translation(l)]
    
    if not indices_to_translate:
        return list(lines)
    
    texts_to_translate = [lines[i] for i in indices_to_translate]
    
    # 構建提示
    numbered_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts_to_translate))
    prompt = TRANSLATION_INSTRUCTION + "\n" + numbered_text + f"\n\n請輸出 {len(texts_to_translate)} 行翻譯結果（對應編號1到{len(texts_to_translate)}，每行一個，不含編號）："
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
            translated_lines_raw = translated_text.split('\n')
            
            # 清理可能的編號前綴
            cleaned = []
            for l in translated_lines_raw:
                # 移除 "1. " "2. " 等前綴
                l = re.sub(r'^\d+\.\s*', '', l)
                cleaned.append(l)
            
            # 移除空尾行
            while cleaned and not cleaned[-1].strip():
                cleaned.pop()
            
            if len(cleaned) != len(texts_to_translate):
                print(f"    [WARN] 行數不符（預期{len(texts_to_translate)}，得到{len(cleaned)}），嘗試逐行翻譯...")
                # fallback：逐行翻譯
                cleaned = []
                for text in texts_to_translate:
                    single_prompt = TRANSLATION_INSTRUCTION + "\n1. " + text + "\n\n請輸出1行翻譯結果（不含編號）："
                    r = model.generate_content(single_prompt)
                    result = re.sub(r'^\d+\.\s*', '', r.text.strip())
                    cleaned.append(result)
                    time.sleep(0.3)
            
            # 修復控制代碼
            cleaned = [fix_control_codes(l) for l in cleaned]
            
            # 合回完整行列表
            result = list(lines)
            for idx, translated in zip(indices_to_translate, cleaned):
                result[idx] = translated
            
            return result
            
        except Exception as e:
            print(f"    [WARN] Gemini API 錯誤（第{attempt+1}次）：{e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指數退避
            else:
                print("    [ERROR] 翻譯失敗，保留原文")
                return list(lines)


def fix_control_codes(text):
    """修復 AI 可能破壞的控制代碼格式"""
    text = re.sub(r'\\\s*[Ss]\s*\[\s*(\d+)\s*\]', r'\\S[\1]', text)
    text = re.sub(r'\\\s*[Nn]\s*\[\s*(\d+)\s*\]', r'\\N[\1]', text)
    text = re.sub(r'\\\s*[Cc]\s*\[\s*(\d+)\s*\]', r'\\C[\1]', text)
    text = re.sub(r'\\\s*[Vv]\s*\[\s*(\d+)\s*\]', r'\\V[\1]', text)
    text = re.sub(r'\\\s*\.', r'\\.', text)
    text = re.sub(r'\\\s*!', r'\\!', text)
    text = re.sub(r'\\\s*\|', r'\\|', text)
    text = re.sub(r'\\\s*\^', r'\\^', text)
    text = re.sub(r'\$\s*[Gg]', r'$g', text)
    return text


# ============================================================
# 檔案處理
# ============================================================

def read_file(path):
    with open(path, 'rb') as f:
        raw = f.read()
    if raw.startswith(UTF8_BOM):
        text = raw[3:].decode('utf-8')
    else:
        text = raw.decode('utf-8')
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return lines


def parse_trans_file(lines):
    """解析 .trans.txt 格式，回傳 entries 列表"""
    entries = []
    for line in lines:
        m = re.match(r'^(\d+)\.\s*(\[MARKER:\s*Message\]\s*(?:\[FACE:\s*[^\]]+\])?|\[TAG:\s*[^\]]+\])\s*(.*)', line)
        if m:
            entries.append({
                'is_tagged': True,
                'prefix': f"{m.group(1)}. {m.group(2)} ",
                'text': m.group(3)
            })
        else:
            entries.append({
                'is_tagged': False,
                'prefix': '',
                'text': line
            })
    return entries


def translate_file(model, trans_file):
    translated_file = trans_file.replace(".trans.txt", ".translated.txt")
    
    # 如果已翻譯過，跳過（除非強制重譯）
    if os.path.exists(translated_file):
        print(f"  [SKIP] 已存在：{os.path.basename(translated_file)}")
        return True
    
    print(f"  翻譯中：{os.path.basename(trans_file)}")
    lines = read_file(trans_file)
    entries = parse_trans_file(lines)
    
    # 提取所有待翻譯文本
    texts = [e['text'] for e in entries]
    
    # 分批翻譯
    translated_texts = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_result = translate_lines_with_gemini(model, batch)
        translated_texts.extend(batch_result)
        if i + BATCH_SIZE < len(texts):
            time.sleep(0.5)  # 批次間延遲，避免 rate limit
    
    # 重組
    result_lines = []
    for entry, trans_text in zip(entries, translated_texts):
        result_lines.append(f"{entry['prefix']}{trans_text}")
    
    # 寫入
    text = '\r\n'.join(result_lines)
    data = UTF8_BOM + text.encode('utf-8')
    with open(translated_file, 'wb') as f:
        f.write(data)
    print(f"    → 儲存：{os.path.basename(translated_file)}")
    return True


# ============================================================
# 主程式
# ============================================================

def main():
    # 解析參數
    force_retranslate = '--force' in sys.argv or '-f' in sys.argv
    single_file = None
    for arg in sys.argv[1:]:
        if not arg.startswith('-') and arg.endswith('.trans.txt'):
            single_file = arg
    
    if not os.path.exists(TRANS_DIR):
        print(f"[ERROR] 找不到 to_translate 目錄：{TRANS_DIR}")
        print("請先執行 export_all.py")
        sys.exit(1)
    
    # 初始化 Gemini
    print("初始化 Gemini API...")
    model = init_gemini()
    print(f"使用模型：{GEMINI_MODEL}")
    
    # 若指定強制重譯，刪除已存在的翻譯檔
    if force_retranslate:
        print("[INFO] 強制重譯模式：將覆蓋所有已翻譯檔案")
        for f in os.listdir(TRANS_DIR):
            if f.endswith('.translated.txt'):
                os.remove(os.path.join(TRANS_DIR, f))
    
    # 取得待翻譯檔案清單
    if single_file:
        if not os.path.isabs(single_file):
            single_file = os.path.join(TRANS_DIR, single_file)
        trans_files = [single_file]
    else:
        trans_files = sorted([
            os.path.join(TRANS_DIR, f)
            for f in os.listdir(TRANS_DIR)
            if f.endswith('.trans.txt')
        ])
    
    print(f"\n找到 {len(trans_files)} 個待翻譯檔案\n" + "-" * 60)
    
    success = 0
    skipped = 0
    failed = 0
    
    for idx, fpath in enumerate(trans_files, 1):
        print(f"[{idx}/{len(trans_files)}] {os.path.basename(fpath)}")
        translated_file = fpath.replace(".trans.txt", ".translated.txt")
        
        if os.path.exists(translated_file) and not force_retranslate:
            print(f"  [SKIP] 已翻譯，跳過（使用 --force 強制重譯）")
            skipped += 1
            continue
        
        try:
            translate_file(model, fpath)
            success += 1
            time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n\n[INFO] 使用者中斷翻譯")
            print(f"已完成 {success} 個，可重新執行繼續（會自動跳過已完成的）")
            sys.exit(0)
        except Exception as e:
            print(f"  [ERROR] 翻譯失敗：{e}")
            failed += 1
            continue
    
    print("\n" + "=" * 60)
    print(f"翻譯完成！")
    print(f"  成功：{success} 個")
    print(f"  跳過：{skipped} 個（已翻譯）")
    if failed:
        print(f"  失敗：{failed} 個")
    print("\n下一步：執行 python scratch/import_all.py 將翻譯寫回遊戲檔案")


if __name__ == "__main__":
    main()
