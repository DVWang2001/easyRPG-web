# -*- coding: utf-8 -*-
import os
import subprocess
import sys

# 獲取 StringScripts_Origin 目錄
ORIGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "StringScripts_Origin"))
print(f"Origin directory: {ORIGIN_DIR}")

if not os.path.exists(ORIGIN_DIR):
    print(f"Error: Origin directory not found at {ORIGIN_DIR}")
    sys.exit(1)

# 遍歷 Origin 目錄下的所有檔案
txt_files = []
for root, dirs, files in os.walk(ORIGIN_DIR):
    for f in files:
        if f.endswith('.txt'):
            full_path = os.path.join(root, f)
            txt_files.append(full_path)

print(f"Found {len(txt_files)} text files in total.")
print("Scanning files for translatable items...")

export_count = 0
for idx, fpath in enumerate(sorted(txt_files), 1):
    # 讀取檔案，快速檢查是否包含有用內容
    with open(fpath, 'rb') as f:
        content = f.read()
    
    # 判斷是否包含 #Message# 或 #TAG#
    has_message = b'#Message#' in content
    # 有些 database 檔案包含 #Name#、#Description# 等等
    # 我們可以用正則表達式或直接看是否含有 '#' 字元
    # 由於 RPG Maker 2000 的 Database 檔案大小通常較大，非空的我們都導出
    # 如果大小小於 10 bytes，且不包含特殊字元，可以直接忽略
    if len(content) <= 10 and not has_message:
        continue
        
    # 我們利用 translator.py 的 detect_file_type 或直接 export 來看是否有內容
    # 呼叫 export
    print(f"[{idx}] Exporting {os.path.relpath(fpath, ORIGIN_DIR)}...")
    subprocess.run(["python", "scratch/translator.py", "export", fpath])
    export_count += 1

print("-" * 60)
print(f"Successfully exported {export_count} files for translation.")
