import os
import sys

def split_file(filepath, output_dir, lines_per_file=500):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_name = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    
    file_count = 1
    current_lines = []
    in_message = False
    
    for line in lines:
        current_lines.append(line)
        if "#Message#" in line:
            in_message = True
        if "##" in line:
            in_message = False
        
        if len(current_lines) >= lines_per_file and not in_message:
            output_path = os.path.join(output_dir, f"{base_name}_part{file_count:02d}.txt")
            with open(output_path, 'w', encoding='utf-8-sig') as out_f:
                out_f.writelines(current_lines)
            print(f"Created: {output_path}")
            current_lines = []
            file_count += 1
            
    if current_lines:
        output_path = os.path.join(output_dir, f"{base_name}_part{file_count:02d}.txt")
        with open(output_path, 'w', encoding='utf-8-sig') as out_f:
            out_f.writelines(current_lines)
        print(f"Created: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_file.py <filepath>")
    else:
        split_file(sys.argv[1], r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts\segments")
