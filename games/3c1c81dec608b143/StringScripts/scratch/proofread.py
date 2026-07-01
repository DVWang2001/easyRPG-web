import re
import sys
import codecs

def count_tags(filepath):
    tags = ["#Message#", "#Choice#", "Select Face Graphic", "##"]
    counts = {t: 0 for t in tags}
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                for t in tags:
                    if t in line:
                        counts[t] += 1
    except Exception as e:
        print(f"Error counting tags in {filepath}: {e}")
    return counts

def check_bom(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read(3)
            return content == codecs.BOM_UTF8
    except Exception as e:
        print(f"Error checking BOM in {filepath}: {e}")
        return False

def check_japanese_residue(filepath):
    # Match hiragana and katakana
    jp_re = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    residues = []
    in_message = False
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
                if in_message:
                    # Ignore markup control characters or specific tags if any,
                    # but check for general hiragana/katakana
                    matches = jp_re.findall(line)
                    if matches:
                        residues.append((i, line.strip(), "".join(matches)))
    except Exception as e:
        print(f"Error scanning Japanese residue in {filepath}: {e}")
    return residues

def check_and_clean_punctuation(filepath):
    replacements = {
        'ー': '—',
        '・': '．',
        '～': '～',
        '？': '？',
        '！': '！'
    }
    # We will report if there are raw 'ー' or '・' inside messages
    punctuation_issues = []
    in_message = False
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
                if in_message:
                    for char, repl in replacements.items():
                        if char in ['ー', '・'] and char in line:
                            punctuation_issues.append((i, line.strip(), char))
    except Exception as e:
        print(f"Error scanning punctuation in {filepath}: {e}")
    return punctuation_issues

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    files_to_check = (
        [f"Map{i:04d}.txt" for i in range(1, 12)] +
        ["Map0018.txt", "Map0019.txt", "Map0020.txt", "Map0021.txt",
         "Map0022.txt", "Map0023.txt", "Map0024.txt", "Map0025.txt"]
    )
    origin_dir = "StringScripts_Origin"
    
    print("=== STARTING BATCH PROOFREADING ===")
    
    for fn in files_to_check:
        origin_path = f"../StringScripts_Origin/{fn}"
        trans_path = fn
        
        print(f"\n--- Checking File: {fn} ---")
        
        # 1. Check BOM
        if not check_bom(trans_path):
            print(f"[ERROR] {fn} is missing UTF-8 BOM encoding!")
        else:
            print(f"[OK] BOM encoding is valid (UTF-8 BOM).")
            
        # 2. Check Tag counts compared to Origin
        origin_counts = count_tags(origin_path)
        trans_counts = count_tags(trans_path)
        
        counts_match = True
        for tag, count in origin_counts.items():
            if trans_counts[tag] != count:
                print(f"[ERROR] Tag '{tag}' mismatch! Origin: {count}, Reconstructed: {trans_counts[tag]}")
                counts_match = False
                
        if counts_match:
            print(f"[OK] Tag structure matches origin perfectly. ({origin_counts})")
            
        # 3. Check Japanese Residue in Messages
        residues = check_japanese_residue(trans_path)
        if residues:
            print(f"[WARNING] Japanese characters (hiragana/katakana) found in message blocks:")
            for line_no, content, chars in residues[:10]:
                print(f"  Line {line_no}: '{content}' (Found: {chars})")
            if len(residues) > 10:
                print(f"  ... and {len(residues) - 10} more lines.")
        else:
            print(f"[OK] No Japanese hiragana/katakana residue in messages.")
            
        # 4. Check Punctuation issues (like ー or ・)
        punct_issues = check_and_clean_punctuation(trans_path)
        if punct_issues:
            print(f"[WARNING] Obsolete/Japanese punctuation ('ー' or '・') found in message blocks:")
            for line_no, content, char in punct_issues[:10]:
                print(f"  Line {line_no}: '{content}' (Found raw: {char})")
            if len(punct_issues) > 10:
                print(f"  ... and {len(punct_issues) - 10} more lines.")
        else:
            print(f"[OK] Punctuation formatting (ー/・) is clean.")

if __name__ == '__main__':
    main()
