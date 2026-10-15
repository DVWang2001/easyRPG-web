import os
import sys

def count_tags(filepath):
    tags = ["#Message#", "##", "Select Face Graphic:"]
    counts = {t: 0 for t in tags}
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                for t in tags:
                    if t in line:
                        counts[t] += 1
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return counts

def check_consistency(origin_dir, trans_dir, filename):
    origin_path = os.path.join(origin_dir, filename)
    trans_path = os.path.join(trans_dir, filename)
    
    if not os.path.exists(origin_path):
        print(f"Origin file not found: {origin_path}")
        return
    if not os.path.exists(trans_path):
        print(f"Trans file not found: {trans_path}")
        return
        
    origin_counts = count_tags(origin_path)
    trans_counts = count_tags(trans_path)
    
    print(f"--- Consistency Check for {filename} ---")
    is_ok = True
    for tag in origin_counts:
        o_c = origin_counts[tag]
        t_c = trans_counts[tag]
        status = "OK" if o_c == t_c else "MISMATCH"
        print(f"{tag:20}: Origin={o_c}, Trans={t_c} -> {status}")
        if status == "MISMATCH":
            is_ok = False
    
    if is_ok:
        print("RESULT: SUCCESS")
    else:
        print("RESULT: FAILED")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python final_check.py <filename>")
    else:
        check_consistency(r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts_Origin",
                         r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts",
                         sys.argv[1])
