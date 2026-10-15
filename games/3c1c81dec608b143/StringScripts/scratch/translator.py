import os
import re
import sys
import json

def detect_file_type(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    return '#Message#' in content, content

def extract_file(filepath):
    is_map_like, content = detect_file_type(filepath)
    lines = content.splitlines()
    trans_items = []
    meta = []
    
    if is_map_like:
        current_face = "NONE"
        face_re = re.compile(r'Select Face Graphic:\s*([^,]+)')
        
        in_message = False
        message_lines = []
        message_start_idx = -1
        
        for idx, line in enumerate(lines):
            line_strip = line.strip()
            
            # Track face
            if "Select Face Graphic:" in line:
                match = face_re.search(line)
                if match:
                    face = match.group(1).strip()
                    if face.lower() == "erase":
                        current_face = "NONE"
                    else:
                        current_face = face
                        
            if line_strip == '#Message#':
                in_message = True
                message_lines = []
                message_start_idx = idx + 1
                continue
                
            if line_strip == '##':
                in_message = False
                # Join lines and check if it contains any non-whitespace characters
                text = "\n".join(message_lines)
                if text.strip():
                    trans_items.append({
                        "face": current_face,
                        "marker": "Message",
                        "text": text
                    })
                    meta.append({
                        "type": "message",
                        "start_line_idx": message_start_idx,
                        "end_line_idx": idx - 1 # line before '##'
                    })
                continue
                
            if in_message:
                message_lines.append(line)
                
    else:
        # Tag-based file
        tag_re = re.compile(r'^#([\w:.-]+)#(?:\s*\[\d+\])?$')
        for idx, line in enumerate(lines):
            match = tag_re.match(line.strip())
            if match:
                tag_name = match.group(1)
                val_idx = idx + 1
                if val_idx < len(lines):
                    val = lines[val_idx]
                    if val.strip():
                        trans_items.append({
                            "face": "NONE",
                            "marker": tag_name,
                            "text": val
                        })
                        meta.append({
                            "type": "tag",
                            "line_idx": val_idx
                        })
                        
    return trans_items, meta, lines

def reconstruct(original_lines, trans_items, meta, translated_texts):
    new_lines = list(original_lines)
    for i in range(len(trans_items) - 1, -1, -1):
        m = meta[i]
        trans_val = translated_texts[i]
        if m["type"] == "message":
            start = m["start_line_idx"]
            end = m["end_line_idx"]
            val_lines = trans_val.split('\n')
            new_lines[start:end+1] = val_lines
        elif m["type"] == "tag":
            line_idx = m["line_idx"]
            new_lines[line_idx] = trans_val
    return new_lines

def parse_translation_file(translation_filepath, expected_count):
    with open(translation_filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # We parse the textarea style numbered lines
    # It looks like:
    # 1. Line 1
    # Line 2
    # 2. Line 1
    items = []
    current_item = []
    
    # Clean output by splitting lines
    lines = content.splitlines()
    for line in lines:
        # Match "1. " or "22. "
        match = re.match(r'^(\d+)\. (.*)', line)
        if match:
            if current_item:
                items.append("\n".join(current_item))
            current_item = [match.group(2)]
        else:
            if current_item:
                current_item.append(line)
            else:
                # Text before the first number (e.g. metadata or blank lines)
                pass
                
    if current_item:
        items.append("\n".join(current_item))
        
    return items

def main_cli():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python translator.py list")
        print("  python translator.py export <file_path>")
        print("  python translator.py import <file_path> <translation_file_path> <output_file_path>")
        return

    cmd = sys.argv[1]
    
    if cmd == "list":
        # List all txt files and their item counts
        files = []
        # Root Map files
        for f in sorted(os.listdir('.')):
            if f.startswith('Map') and f.endswith('.txt'):
                files.append(f)
        # Database files
        db_dir = './Database'
        if os.path.exists(db_dir):
            for f in sorted(os.listdir(db_dir)):
                if f.endswith('.txt'):
                    files.append(f"Database/{f}")
                    
        print(f"{'Filename':<35} | {'Type':<12} | {'Items to Translate':<18}")
        print("-" * 75)
        for f_path in files:
            if not os.path.exists(f_path):
                continue
            is_map_like, _ = detect_file_type(f_path)
            items, _, _ = extract_file(f_path)
            t_str = "Message-based" if is_map_like else "Tag-based"
            print(f"{f_path:<35} | {t_str:<12} | {len(items):<18}")
            
    elif cmd == "export":
        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f"Error: {filepath} not found.")
            return
            
        items, meta, _ = extract_file(filepath)
        print(f"Exporting {len(items)} items from {filepath}...")
        
        # Write format ready for translation
        os.makedirs('scratch/to_translate', exist_ok=True)
        # Save mapping
        map_path = f"scratch/to_translate/{os.path.basename(filepath)}.meta.json"
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump({"filepath": filepath, "meta": meta, "items": items}, f, indent=4, ensure_ascii=False)
            
        export_path = f"scratch/to_translate/{os.path.basename(filepath)}.trans.txt"
        with open(export_path, 'w', encoding='utf-8-sig') as f:
            for idx, item in enumerate(items, 1):
                prefix = f"[MARKER: {item['marker']}]"
                if item['face'] != "NONE":
                    prefix += f" [FACE: {item['face']}]"
                
                # Multi-line handling
                lines = item['text'].split('\n')
                f.write(f"{idx}. {prefix} {lines[0]}\n")
                for sub_line in lines[1:]:
                    f.write(f"{sub_line}\n")
                    
        print(f"Exported to {export_path} and metadata saved to {map_path}")
        
    elif cmd == "import":
        if len(sys.argv) < 5:
            print("Usage: python translator.py import <file_path> <translation_file_path> <output_file_path>")
            return
        filepath = sys.argv[2]
        trans_filepath = sys.argv[3]
        out_filepath = sys.argv[4]
        
        # Load meta
        map_path = f"scratch/to_translate/{os.path.basename(filepath)}.meta.json"
        if not os.path.exists(map_path):
            print(f"Error: Metadata file {map_path} not found. Please export first.")
            return
            
        with open(map_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
            
        trans_items = map_data["items"]
        meta = map_data["meta"]
        
        # Read original file lines
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            original_lines = f.read().splitlines()
            
        # Parse translated file
        translated_texts = parse_translation_file(trans_filepath, len(trans_items))
        
        if len(translated_texts) != len(trans_items):
            print(f"Warning: Count mismatch! Expected {len(trans_items)} translated items, but parsed {len(translated_texts)}.")
            print("Please check the translated file format.")
            # We can still proceed if the user wants, but print first 3 mismatches if any
            min_len = min(len(translated_texts), len(trans_items))
        else:
            min_len = len(trans_items)
            
        new_lines = reconstruct(original_lines, trans_items[:min_len], meta[:min_len], translated_texts[:min_len])
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(out_filepath) if os.path.dirname(out_filepath) else '.', exist_ok=True)
        
        # Write output with UTF-8-BOM
        with open(out_filepath, 'w', encoding='utf-8-sig') as f:
            f.write("\n".join(new_lines) + "\n")
            
        print(f"Successfully imported translation. Reconstructed file saved to {out_filepath}")

if __name__ == '__main__':
    main_cli()
