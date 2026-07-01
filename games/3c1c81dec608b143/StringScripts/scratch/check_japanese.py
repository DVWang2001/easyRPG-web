import os
import re
import sys

def check_japanese_in_file(filepath):
    # Match Japanese characters (hiragana, katakana, and kanji)
    # Note: Kanji overlaps with Chinese, so we focus on Hiragana/Katakana first
    jp_re = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    
    in_message = False
    outside_jp_lines = []
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f, 1):
                clean_line = line.strip()
                if clean_line == '#Message#':
                    in_message = True
                    continue
                if clean_line == '##':
                    in_message = False
                    continue
                
                # Check for face graphic line which is not translated
                if 'Select Face Graphic' in clean_line:
                    continue
                    
                # If not inside a message block, check if it contains hiragana/katakana
                if not in_message:
                    if jp_re.search(line):
                        outside_jp_lines.append((i, line.strip()))
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        
    return outside_jp_lines

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    all_outside = {}
    
    for f in sorted(os.listdir('.')):
        if f.startswith('Map') and f.endswith('.txt'):
            outside = check_japanese_in_file(f)
            if outside:
                all_outside[f] = outside
                
    if all_outside:
        print("Found Japanese characters outside #Message# in map files:")
        for fn, lines in all_outside.items():
            print(f"\n--- {fn} ---")
            for line_no, content in lines[:10]:
                print(f"Line {line_no}: {content}")
            if len(lines) > 10:
                print(f"... and {len(lines) - 10} more lines")
    else:
        print("No Japanese characters outside #Message# in map files.")

if __name__ == '__main__':
    main()
