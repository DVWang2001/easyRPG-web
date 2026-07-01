# -*- coding: utf-8 -*-
"""
RPG Maker 2000/2003 StringScripts 翻譯工具
用法：
  python scratch/translator.py list
  python scratch/translator.py export <原始檔路徑>
  python scratch/translator.py import <原始檔路徑> <翻譯對照檔> <輸出檔>
"""

import sys
import os
import re
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANS_DIR = os.path.join(SCRIPT_DIR, "to_translate")
CWD_BASE = os.getcwd()

UTF8_BOM = b'\xef\xbb\xbf'


def read_file(path):
    """讀取 UTF-8（含或不含 BOM）文字檔案，返回 (lines_list, original_bytes)"""
    with open(path, 'rb') as f:
        raw = f.read()
    if raw.startswith(UTF8_BOM):
        text = raw[3:].decode('utf-8')
    else:
        text = raw.decode('utf-8')
    # 統一換行符
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return lines


def write_file_bom(path, lines):
    """寫入 UTF-8 BOM 文字檔案"""
    text = '\r\n'.join(lines)
    data = UTF8_BOM + text.encode('utf-8')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"  -> Written: {path}")


# ============================================================
# Message-based 解析（地圖檔案）
# ============================================================

def parse_message_based(lines):
    """解析 Message-based 格式，回傳 items 列表
    每個 item: {
        'face': str or None,
        'content_lines': [str, ...],
        'start_line_idx': int,   # #Message# 行的索引
        'end_line_idx': int,     # ## 行的索引
        'trans_hint': str,
    }
    """
    items = []
    current_face = None
    i = 0
    while i < len(lines):
        line = lines[i]
        # 偵測臉圖
        face_match = re.match(r'\{\{+\s*Select Face Graphic:\s*(.+?)\s*\}\}+', line)
        if face_match:
            current_face = face_match.group(1).strip()
        # 偵測訊息開始
        if line.strip() == '#Message#':
            start_idx = i
            content = []
            i += 1
            while i < len(lines) and lines[i].strip() != '##':
                content.append(lines[i])
                i += 1
            end_idx = i  # ## 所在行
            # 移除尾部空行
            while content and content[-1].strip() == '':
                content.pop()
            hint = f"[MARKER: Message]"
            if current_face:
                hint += f" [FACE: {current_face}]"
            items.append({
                'face': current_face,
                'content_lines': content,
                'start_line_idx': start_idx,
                'end_line_idx': end_idx,
                'trans_hint': hint,
            })
        i += 1
    return items


def parse_tag_based(lines):
    """解析 Tag-based 格式（Database），回傳 items 列表
    每個 item: {
        'tag': str,
        'value': str,
        'line_idx': int,   # 值所在行索引
        'trans_hint': str,
    }
    """
    items = []
    i = 0
    while i < len(lines):
        line = lines[i]
        tag_match = re.match(r'^#([^#]+)#(?:\s*\[\d+\])?', line)
        if tag_match:
            tag = tag_match.group(1)
            if i + 1 < len(lines):
                value = lines[i + 1]
                # 跳過空值行（分隔線或空白）
                if value.strip() and value.strip() != '':
                    items.append({
                        'tag': tag,
                        'value': value,
                        'line_idx': i + 1,
                        'trans_hint': f"[TAG: {tag}]",
                    })
        i += 1
    return items


def detect_file_type(lines):
    """自動判斷檔案類型（Message-based 或 Tag-based）"""
    for line in lines:
        if line.strip() == '#Message#':
            return 'message'
    for line in lines:
        if re.match(r'^#\w+#', line):
            return 'tag'
    return 'message'


# ============================================================
# list 指令
# ============================================================

def cmd_list():
    origin_dir = os.path.join('..', 'StringScripts_Origin')
    if not os.path.isdir(origin_dir):
        print(f"[ERROR] StringScripts_Origin directory not found: {origin_dir}")
        return

    print(f"{'Filename':<40} | {'Type':<15} | Items to Translate")
    print('-' * 75)

    def process_dir(d, prefix=''):
        files = sorted(os.listdir(d))
        for fname in files:
            fpath = os.path.join(d, fname)
            if os.path.isdir(fpath):
                process_dir(fpath, prefix=fname + '/')
            elif fname.endswith('.txt'):
                lines = read_file(fpath)
                ftype = detect_file_type(lines)
                if ftype == 'message':
                    items = parse_message_based(lines)
                else:
                    items = parse_tag_based(lines)
                count = len(items)
                display_name = prefix + fname
                print(f"{display_name:<40} | {ftype + '-based':<15} | {count}")

    process_dir(origin_dir)


# ============================================================
# export 指令
# ============================================================

def cmd_export(origin_path):
    if not os.path.isfile(origin_path):
        print(f"[ERROR] File not found: {origin_path}")
        return

    lines = read_file(origin_path)
    ftype = detect_file_type(lines)
    
    # 保持子目錄結構
    # 例如：../StringScripts_Origin/Database/Items.txt -> Database/Items.txt
    rel_path = os.path.relpath(origin_path, os.path.join('..', 'StringScripts_Origin'))
    trans_name = rel_path.replace(os.sep, '_') # 用底線代替路徑分隔符，避免子目錄問題
    
    os.makedirs(TRANS_DIR, exist_ok=True)

    if ftype == 'message':
        items = parse_message_based(lines)
        trans_path = os.path.join(TRANS_DIR, trans_name + '.trans.txt')
        meta_path = os.path.join(TRANS_DIR, trans_name + '.meta.json')

        trans_lines = []
        for idx, item in enumerate(items, 1):
            hint = item['trans_hint']
            first_content = item['content_lines'][0] if item['content_lines'] else ''
            trans_lines.append(f"{idx}. {hint} {first_content}")
            for extra in item['content_lines'][1:]:
                trans_lines.append(extra)

        write_file_bom(trans_path, trans_lines)

        # 儲存 meta
        meta = [{
            'idx': i,
            'face': item['face'],
            'start_line_idx': item['start_line_idx'],
            'end_line_idx': item['end_line_idx'],
            'num_content_lines': len(item['content_lines']),
        } for i, item in enumerate(items, 1)]
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(items)} message items to: {trans_path}")

    else:
        items = parse_tag_based(lines)
        trans_path = os.path.join(TRANS_DIR, trans_name + '.trans.txt')
        meta_path = os.path.join(TRANS_DIR, trans_name + '.meta.json')

        trans_lines = []
        for idx, item in enumerate(items, 1):
            hint = item['trans_hint']
            trans_lines.append(f"{idx}. {hint} {item['value']}")

        write_file_bom(trans_path, trans_lines)

        meta = [{
            'idx': i,
            'tag': item['tag'],
            'line_idx': item['line_idx'],
        } for i, item in enumerate(items, 1)]
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(items)} tag items to: {trans_path}")


# ============================================================
# import 指令
# ============================================================

def parse_translated_file(trans_path):
    """解析翻譯對照檔，返回 {編號: [行列表]} 字典"""
    lines = read_file(trans_path)
    result = {}
    current_num = None
    current_lines = []

    for line in lines:
        m = re.match(r'^(\d+)\.\s*(.*)', line)
        if m:
            if current_num is not None:
                # 移除尾部空行
                while current_lines and current_lines[-1].strip() == '':
                    current_lines.pop()
                result[current_num] = current_lines
            current_num = int(m.group(1))
            rest = m.group(2)
            
            # 剝離輔助標記
            # 1. 剝離 [MARKER: Message]
            if rest.startswith("[MARKER: Message]"):
                rest = rest[len("[MARKER: Message]"):].lstrip(' ')
                # 2. 剝離隨後的 [FACE: xxx]
                if rest.startswith("[FACE:"):
                    end_idx = rest.find(']')
                    if end_idx != -1:
                        rest = rest[end_idx + 1:].lstrip(' ')
            # 3. 剝離 [TAG: xxx]
            elif rest.startswith("[TAG:"):
                end_idx = rest.find(']')
                if end_idx != -1:
                    rest = rest[end_idx + 1:].lstrip(' ')
                    
            current_lines = [rest]
        else:
            if current_num is not None:
                current_lines.append(line)

    if current_num is not None:
        while current_lines and current_lines[-1].strip() == '':
            current_lines.pop()
        result[current_num] = current_lines

    return result



def cmd_import(origin_path, translated_path, output_path):
    if not os.path.isfile(origin_path):
        print(f"[ERROR] Origin file not found: {origin_path}")
        return
    if not os.path.isfile(translated_path):
        print(f"[ERROR] Translated file not found: {translated_path}")
        return

    lines = read_file(origin_path)
    ftype = detect_file_type(lines)
    
    rel_path = os.path.relpath(origin_path, os.path.join('..', 'StringScripts_Origin'))
    trans_name = rel_path.replace(os.sep, '_')
    meta_path = os.path.join(TRANS_DIR, trans_name + '.meta.json')

    translations = parse_translated_file(translated_path)

    if ftype == 'message':
        items = parse_message_based(lines)

        if len(translations) != len(items):
            print(f"Warning: Count mismatch! Expected {len(items)} translated items, but parsed {len(translations)} in {translated_path}.")

        new_lines = list(lines)

        # 倒序替換
        for i in range(len(items) - 1, -1, -1):
            item = items[i]
            num = i + 1
            if num not in translations:
                print(f"  [WARN] Missing translation for item {num}, keeping original.")
                continue

            trans_content = translations[num]
            start = item['start_line_idx']
            end = item['end_line_idx']

            # 重建：#Message# + 翻譯行 + ##
            replacement = ['#Message#'] + trans_content + ['##']
            new_lines[start:end + 1] = replacement

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        write_file_bom(output_path, new_lines)
        print(f"Successfully imported translation. Reconstructed file saved to {output_path}")

    else:
        items = parse_tag_based(lines)

        if len(translations) != len(items):
            print(f"Warning: Count mismatch! Expected {len(items)} translated items, but parsed {len(translations)} in {translated_path}.")

        new_lines = list(lines)

        # 倒序替換單行
        for i in range(len(items) - 1, -1, -1):
            item = items[i]
            num = i + 1
            if num not in translations:
                print(f"  [WARN] Missing translation for item {num}, keeping original.")
                continue

            trans_lines = translations[num]
            # Tag-based 只替換單行
            trans_value = trans_lines[0] if trans_lines else ''
            new_lines[item['line_idx']] = trans_value

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        write_file_bom(output_path, new_lines)
        print(f"Successfully imported translation. Reconstructed file saved to {output_path}")


# ============================================================
# 主程式
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == 'list':
        cmd_list()
    elif cmd == 'export':
        if len(sys.argv) < 3:
            print("Usage: python scratch/translator.py export <origin_path>")
            sys.exit(1)
        cmd_export(sys.argv[2])
    elif cmd == 'import':
        if len(sys.argv) < 5:
            print("Usage: python scratch/translator.py import <origin_path> <translated_path> <output_path>")
            sys.exit(1)
        cmd_import(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
