# -*- coding: utf-8 -*-
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPORT_FILE = os.path.join(SCRIPT_DIR, "translation_validation_report.txt")

# 檢查檔案是否含日文假名（平假名/片假名）
RE_JAPANESE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')

issues = []
files_checked = 0

# 掃描正式 StringScripts/ 目錄下的所有 txt 檔案
for root, dirs, files in os.walk(WORK_DIR):
    # 排除 scratch 目錄和 to_translate 備份目錄，我們只校對最終寫回遊戲的正式 txt 檔案
    if "scratch" in root or "to_translate" in root or "StringScripts_Origin" in root:
        continue
        
    for file in files:
        if not file.endswith(".txt"):
            continue
            
        filepath = os.path.join(root, file)
        rel_path = os.path.relpath(filepath, WORK_DIR)
        files_checked += 1
        
        try:
            with open(filepath, 'rb') as f:
                raw_content = f.read()
                
            # 優先使用 cp950 解碼，若失敗再回退到 utf-8
            try:
                text = raw_content.decode('cp950')
            except UnicodeDecodeError:
                if raw_content.startswith(b'\xef\xbb\xbf'):
                    text = raw_content[3:].decode('utf-8')
                else:
                    text = raw_content.decode('utf-8')
        except Exception as e:
            issues.append({
                'file': rel_path,
                'line': 0,
                'type': 'FILE_READ_ERROR',
                'msg': f"Cannot read file: {e}",
                'content': ''
            })
            continue
            
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # 1. 處理 MapXXXX.txt 以及 Database_Troops / Database_CommonEvents 的訊息區塊校對
        if (file.startswith("Map") or "Troops" in file or "CommonEvents" in file) and file.endswith(".txt"):
            in_text_block = False
            for line_idx, line in enumerate(lines, 1):
                line_strip = line.strip()
                
                # 進入需要顯示給玩家看的文字區塊
                if line_strip in ['#Message#', '#Choice#', '#Shop#']:
                    in_text_block = True
                    continue
                elif line_strip == '##':
                    in_text_block = False
                    continue
                    
                if in_text_block:
                    # A. 檢測 cp950 編碼性
                    try:
                        line.encode('cp950')
                    except UnicodeEncodeError as e:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNENCODABLE_CP950',
                            'msg': f"Character '{e.object[e.start:e.end]}' (U+{ord(e.object[e.start]):04X}) is not supported by CP950 (Big5)",
                            'content': line
                        })
                        
                    # B. 檢測是否有未翻譯日文假名
                    if RE_JAPANESE.search(line):
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNTRANSLATED_JAPANESE',
                            'msg': "Contains untranslated Japanese Hiragana/Katakana",
                            'content': line
                        })
                        
                    # C. 檢測是否殘留不支援的打字速度代碼 \S[n]
                    if '\\S[' in line:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNSUPPORTED_CONTROL_CODE',
                            'msg': "Contains unsupported speed control code \\S[n]",
                            'content': line
                        })
                        
                    # D. 檢測是否包含日文中點或半角中點（應替換成標準全角中點 \u00b7）
                    if '\u30fb' in line or '\uff65' in line or '\u2027' in line:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'NON_STANDARD_DOT',
                            'msg': "Contains non-standard Japanese or old middle-dot (should be \\u00b7)",
                            'content': line
                        })
                        
        # 2. 處理 Database/*.txt 的校對
        elif rel_path.startswith("Database") and file.endswith(".txt"):
            check_next_line = False
            label = ""
            for line_idx, line in enumerate(lines, 1):
                line_strip = line.strip()
                
                # 如果遇到 Name, Description, UseMessage1, UseMessage2，下一行就是文字內容
                if line_strip.startswith('#') and any(lbl in line_strip for lbl in ['#Name#', '#Description#', '#UseMessage1#', '#UseMessage2#']):
                    check_next_line = True
                    label = line_strip
                    continue
                    
                if check_next_line:
                    check_next_line = False
                    if not line_strip:
                        continue
                        
                    # A. 檢測 cp950 編碼性
                    try:
                        line.encode('cp950')
                    except UnicodeEncodeError as e:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNENCODABLE_CP950',
                            'msg': f"Character '{e.object[e.start:e.end]}' (U+{ord(e.object[e.start]):04X}) under {label} is not supported by CP950 (Big5)",
                            'content': line
                        })
                        
                    # B. 檢測是否有未翻譯日文假名
                    if RE_JAPANESE.search(line):
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNTRANSLATED_JAPANESE',
                            'msg': f"Untranslated Japanese Hiragana/Katakana under {label}",
                            'content': line
                        })
                        
                    # C. 檢測不支援的代碼 \S[n]
                    if '\\S[' in line:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'UNSUPPORTED_CONTROL_CODE',
                            'msg': f"Contains unsupported speed control code \\S[n] under {label}",
                            'content': line
                        })
                        
                    # D. 檢測中點
                    if '\u30fb' in line or '\uff65' in line or '\u2027' in line:
                        issues.append({
                            'file': rel_path,
                            'line': line_idx,
                            'type': 'NON_STANDARD_DOT',
                            'msg': f"Contains non-standard middle-dot (should be \\u00b7) under {label}",
                            'content': line
                        })

# 寫入 UTF-8 報告檔案
with open(REPORT_FILE, 'w', encoding='utf-8') as rf:
    rf.write("=== Translation Quality Validation Report ===\n")
    rf.write(f"Files Checked: {files_checked}\n")
    rf.write(f"Total Issues Found: {len(issues)}\n\n")
    
    if issues:
        for idx, iss in enumerate(issues, 1):
            rf.write(f"[{idx}] File: {iss['file']}:{iss['line']} | Type: {iss['type']}\n")
            rf.write(f"    Message: {iss['msg']}\n")
            rf.write(f"    Content: {iss['content']}\n")
            rf.write("-" * 60 + "\n")
    else:
        rf.write("[SUCCESS] No translation issues found! All text is clean and fully compatible.\n")

print(f"QA Scan completed. Checked {files_checked} files.")
print(f"Total issues found: {len(issues)}")
print(f"Detailed report written to: scratch/translation_validation_report.txt")
