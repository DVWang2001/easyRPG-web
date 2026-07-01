import os
import re
import sys

def merge_files(original_filepath, segment_dir, output_filepath):
    base_name = os.path.basename(original_filepath)
    # Get all segments, sort them by part number
    segments = sorted([f for f in os.listdir(segment_dir) if f.startswith(base_name) and f.endswith("_trans.txt")])
    
    if not segments:
        print(f"No translated segments found for {base_name}")
        return

    merged_lines = []
    for segment in segments:
        segment_path = os.path.join(segment_dir, segment)
        with open(segment_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            # Extract content between <textarea> tags
            match = re.search(r'<textarea>(.*?)</textarea>', content, re.DOTALL)
            if match:
                text = match.group(1).strip()
                lines = text.splitlines()
                processed_lines = []
                for line in lines:
                    # Remove the "N. " prefix added by the prompt requirement if it exists
                    cleaned_line = re.sub(r'^\d+\.\s?', '', line)
                    processed_lines.append(cleaned_line)
                
                merged_lines.extend(processed_lines)
            else:
                print(f"Warning: No <textarea> found in {segment}")

    # For safety, let's backup the original before overwriting if output_filepath is same as original
    if original_filepath == output_filepath:
        backup_path = original_filepath + ".bak"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(original_filepath, backup_path)

    with open(output_filepath, 'w', encoding='utf-8-sig') as out_f:
        for line in merged_lines:
            out_f.write(line + '\n')
    
    print(f"Merged {len(segments)} segments into {output_filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_file.py <filename_in_scripts>")
    else:
        scripts_dir = r"c:\Games\RPG Maker 2000 value+ 樣品遊戲漢化\現在能感覺到風（長篇RPG）\StringScripts"
        segment_dir = os.path.join(scripts_dir, "segments")
        target_file = os.path.join(scripts_dir, sys.argv[1])
        merge_files(target_file, segment_dir, target_file)
