# -*- coding: utf-8 -*-
"""
write_translation.py
由 AI 直接翻譯後，將翻譯內容寫入對應的 .translated.txt 檔案。
此腳本由 AI 翻譯工具自動呼叫，不需手動執行。
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANS_DIR = os.path.join(SCRIPT_DIR, "to_translate")
UTF8_BOM = b'\xef\xbb\xbf'

def write_translated(filename, lines):
    """
    filename: trans.txt 的檔名（不含路徑），例如 'Map0074.txt.trans.txt'
    lines: 翻譯後的行列表
    """
    out_name = filename.replace(".trans.txt", ".translated.txt")
    out_path = os.path.join(TRANS_DIR, out_name)
    text = '\r\n'.join(lines)
    data = UTF8_BOM + text.encode('utf-8')
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"[OK] Written: {out_name}  ({len(lines)} lines)")

def read_trans(filename):
    """讀取原始 .trans.txt 檔案內容"""
    path = os.path.join(TRANS_DIR, filename)
    with open(path, 'rb') as f:
        raw = f.read()
    if raw.startswith(UTF8_BOM):
        text = raw[3:].decode('utf-8')
    else:
        text = raw.decode('utf-8')
    return text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

if __name__ == "__main__":
    print("此腳本由 AI 翻譯流程呼叫，請勿直接執行。")
