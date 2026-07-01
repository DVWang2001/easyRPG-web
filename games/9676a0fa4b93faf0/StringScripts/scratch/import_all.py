# -*- coding: utf-8 -*-
import os
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANS_DIR = os.path.join(SCRIPT_DIR, "to_translate")
ORIGIN_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "StringScripts_Origin"))
OUTPUT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

print(f"Origin dir: {ORIGIN_DIR}")
print(f"Output dir: {OUTPUT_DIR}")
print(f"Translation dir: {TRANS_DIR}")

# 1. 掃描 StringScripts_Origin 中的所有檔案
origin_files = []
for root, dirs, files in os.walk(ORIGIN_DIR):
    for f in files:
        if f.endswith('.txt'):
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, ORIGIN_DIR)
            origin_files.append(rel_path)

print(f"Total files in origin: {len(origin_files)}")

# 2. 進行 batch import
import_count = 0
copy_count = 0

for idx, rel_path in enumerate(sorted(origin_files), 1):
    orig_path = os.path.join(ORIGIN_DIR, rel_path)
    out_path = os.path.join(OUTPUT_DIR, rel_path)
    
    # 找出對應的翻譯檔名（例如 Database/Items.txt -> Database_Items.txt.translated.txt）
    trans_name = rel_path.replace(os.sep, '_')
    translated_path = os.path.join(TRANS_DIR, trans_name + ".translated.txt")
    
    # 確保輸出目錄存在
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    if os.path.exists(translated_path):
        # 如果有翻譯檔，執行 import
        print(f"[{idx}] Importing translation for {rel_path}...")
        subprocess.run(["python", "scratch/translator.py", "import", orig_path, translated_path, out_path])
        import_count += 1
    else:
        # 如果沒有翻譯檔，直接複製原始檔
        print(f"[{idx}] Copying original {rel_path} directly...")
        shutil.copyfile(orig_path, out_path)
        copy_count += 1

print("-" * 60)
print(f"Batch import completed.")
print(f"Imported translated files: {import_count}")
print(f"Copied original files directly: {copy_count}")

# 3. 呼叫 Choice 翻譯工具
print("\nTranslating #Choice# options...")
subprocess.run(["python", "scratch/translate_choices.py"])
