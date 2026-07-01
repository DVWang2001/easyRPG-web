import os
import json
import re
import sys

def extract_messages():
    sys.stdout.reconfigure(encoding='utf-8')
    all_messages = []
    
    face_re = re.compile(r'Select Face Graphic:\s*([^,]+)')
    
    for f in sorted(os.listdir('.')):
        if not (f.startswith('Map') and f.endswith('.txt')):
            continue
            
        current_face = "NONE"
        in_message = False
        message_lines = []
        start_line = 0
        
        try:
            with open(f, 'r', encoding='utf-8-sig') as file_obj:
                for idx, line in enumerate(file_obj, 1):
                    line_str = line.strip()
                    
                    # Track face graphics
                    if "Select Face Graphic:" in line:
                        match = face_re.search(line)
                        if match:
                            current_face = match.group(1).strip()
                            if current_face.lower() == "erase":
                                current_face = "NONE"
                        continue
                        
                    if line_str == '#Message#':
                        in_message = True
                        message_lines = []
                        start_line = idx + 1
                        continue
                        
                    if line_str == '##':
                        in_message = False
                        if message_lines:
                            all_messages.append({
                                "file": f,
                                "start_line": start_line,
                                "face": current_face,
                                "text": "\n".join(message_lines)
                            })
                        continue
                        
                    if in_message:
                        message_lines.append(line.rstrip('\r\n'))
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    output_path = 'scratch/all_messages.json'
    with open(output_path, 'w', encoding='utf-8') as out_f:
        json.dump(all_messages, out_f, indent=4, ensure_ascii=False)
        
    print(f"Extracted {len(all_messages)} messages to {output_path}")

if __name__ == '__main__':
    extract_messages()
