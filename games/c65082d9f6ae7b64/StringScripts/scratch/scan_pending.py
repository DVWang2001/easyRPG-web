import os
import re

def scan_japanese_files(directory):
    kana_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    files_to_translate = []
    
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".txt") and filename.startswith("Map"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    if kana_pattern.search(content):
                        files_to_translate.append(filename)
            except Exception:
                pass
    
    return files_to_translate

if __name__ == "__main__":
    scripts_dir = r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts"
    pending_files = scan_japanese_files(scripts_dir)
    print("Files pending translation:")
    for f in pending_files:
        print(f)
