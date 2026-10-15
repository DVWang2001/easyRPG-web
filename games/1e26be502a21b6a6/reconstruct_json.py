"""
reconstruct_json.py
將 Gemini 輸出的譯文.txt還原成 WindyTranslator 可用的 translation_translated.json。

使用方法：
    python reconstruct_json.py <translation.json路徑> <翻譯.txt路徑> [輸出路徑]

範例：
    python reconstruct_json.py "C:/Games/Hanayome/untranslated/translation.json" "gemini_output.txt"
    python reconstruct_json.py "C:/Games/Hanayome/untranslated/translation.json" "gemini_output.txt" "C:/Games/Hanayome/translated/translation_translated.json"
"""

import json
import re
import sys
import os


def parse_numbered_output(txt_path):
    """解析 Gemini 譯文，返回 {編號: 譯文} dict。"""
    with open(txt_path, encoding="utf-8") as f:
        content = f.read()

    # 去除 ```txt ... ``` 標記
    content = re.sub(r'^```\w*\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'^```\s*$', '', content, flags=re.MULTILINE)

    translations = {}
    current_num = None
    current_lines = []

    for line in content.splitlines():
        m = re.match(r'^(\d+)\.\s?(.*)', line)
        if m:
            if current_num is not None:
                translations[current_num] = "\n".join(current_lines).rstrip()
            current_num = int(m.group(1))
            current_lines = [m.group(2)]
        elif current_num is not None:
            current_lines.append(line)

    if current_num is not None:
        translations[current_num] = "\n".join(current_lines).rstrip()

    return translations


def reconstruct(input_json_path, txt_path, output_path):
    with open(input_json_path, encoding="utf-8") as f:
        input_data = json.load(f)

    translations = parse_numbered_output(txt_path)

    result = {}
    counter = 1

    for file_name, entries in input_data.items():
        result[file_name] = {}
        for orig_key, meta in entries.items():
            text_to_translate = meta.get("text_to_translate", orig_key)
            marker = meta.get("original_marker", "")
            speaker = meta.get("speaker_id", "")

            raw = translations.get(counter, text_to_translate)
            # {原文} 或 {xxx} 則不翻譯
            if raw.startswith("{") and raw.endswith("}"):
                translated = text_to_translate
            else:
                translated = raw
            counter += 1

            result[file_name][orig_key] = {
                "text": translated,
                "status": "success",
                "failure_context": None,
                "original_marker": marker,
                "speaker_id": speaker,
            }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"成功還原 {counter - 1} 條譯文，輸出至 {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    txt_path = sys.argv[2]

    if len(sys.argv) >= 4:
        out_path = sys.argv[3]
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(input_path)))
        out_path = os.path.join(base, "translated", "translation_translated.json")

    reconstruct(input_path, txt_path, out_path)
