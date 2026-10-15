import os
import re

def inject_translation(filepath, translations):
    """
    translations: list of translated strings, each corresponds to one #Message# block.
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    new_lines = []
    trans_idx = 0
    in_message = False
    
    for line in lines:
        if "#Message#" in line:
            new_lines.append(line)
            in_message = True
            if trans_idx < len(translations):
                # We expect the translation to include the >>Name<< and content
                new_lines.append(translations[trans_idx] + "\n")
                trans_idx += 1
            continue
        
        if "##" in line and in_message:
            new_lines.append(line)
            in_message = False
            continue
            
        if in_message:
            # Skip original lines inside message block until ##
            continue
        else:
            new_lines.append(line)

    with open(filepath, 'w', encoding='utf-8-sig') as f:
        f.writelines(new_lines)
    print(f"Successfully injected {trans_idx} blocks into {filepath}")

# Example usage will be triggered via run_command
