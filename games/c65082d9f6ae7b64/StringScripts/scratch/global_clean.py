import os
import re
import sys

def global_clean(filepath):
    replacements = {
        'ー': '—',
        '・': '．',
        '～': '～',
        '？': '？',
        '！': '！',
        '。': '。',
        '，': '，',
        '「': '「',
        '」': '」',
        '『': '『',
        '』': '』'
    }
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # 寫回檔案 (確保 UTF-8-BOM)
    with open(filepath, 'w', encoding='utf-8-sig') as f:
        f.write(content)
    print(f"Cleaned and saved: {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python global_clean.py <filename_in_scripts>")
    else:
        scripts_dir = r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts"
        target_file = os.path.join(scripts_dir, sys.argv[1])
        global_clean(target_file)
