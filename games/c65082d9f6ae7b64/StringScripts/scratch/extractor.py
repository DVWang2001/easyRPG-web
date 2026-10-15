import os
import json
import re

def parse_txt_to_json(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    entries = []
    current_entry = None
    
    # 簡單的正則表達式來識別標籤
    msg_start = re.compile(r'^#Message#')
    tag_end = re.compile(r'^##')
    face_graphic = re.compile(r'^\{{20\} Select Face Graphic: (.*) \}{20\}')
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        
        # 處理 Select Face Graphic
        face_match = face_graphic.match(line)
        if face_match:
            face_id = face_match.group(1).split(',')[0].strip()
            # 獲取接下來的 Message
            # 尋找最近的下一個 #Message#
            j = i + 1
            found_msg = False
            while j < len(lines):
                if msg_start.match(lines[j]):
                    found_msg = True
                    break
                if tag_end.match(lines[j]) or face_graphic.match(lines[j]):
                    break
                j += 1
            
            if found_msg:
                # 這裡我們只是標記下一個 Message 的 Face
                pass
            i += 1
            continue

        if msg_start.match(line):
            start_line = i
            content = []
            i += 1
            face_id = "NONE"
            # 往回找最近的 Face Graphic
            k = start_line - 1
            while k >= 0:
                if tag_end.match(lines[k]): break
                face_back_match = face_graphic.match(lines[k])
                if face_back_match:
                    face_id = face_back_match.group(1).split(',')[0].strip()
                    break
                k -= 1

            while i < len(lines) and not tag_end.match(lines[i]):
                content.append(lines[i].rstrip('\n'))
                i += 1
            
            text_content = "\n".join(content)
            marker_type = "Message"
            
            # 嘗試檢測對話內部的角色名稱描述
            # 格式通常是 >>角色名<
            # 或者是直接的第一行是角色名
            
            entries.append({
                "id": len(entries) + 1,
                "marker": marker_type,
                "face": face_id,
                "original": text_content
            })
            i += 1

        else:
            i += 1
            
    return entries

if __name__ == "__main__":
    import sys
    target = sys.argv[1]
    data = parse_txt_to_json(target)
    sys.stdout.buffer.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

