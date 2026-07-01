import os
import sys

def extract_db_names():
    sys.stdout.reconfigure(encoding='utf-8')
    db_dir = './Database'
    if not os.path.exists(db_dir):
        print("Database not found.")
        return
        
    for f in sorted(os.listdir(db_dir)):
        path = os.path.join(db_dir, f)
        if not (os.path.isfile(path) and f.endswith('.txt')):
            continue
            
        print(f"\n==================== {f} ====================")
        current_entry = ""
        try:
            with open(path, 'r', encoding='utf-8-sig') as file_obj:
                for line in file_obj:
                    line_str = line.strip()
                    if line_str.startswith('*****Entry') or line_str.startswith('*** '):
                        current_entry = line_str
                        continue
                    if line_str.startswith('#Name#') or line_str.startswith('#Description#') or line_str.startswith('#Title#') or line_str.startswith('#Message#'):
                        tag = line_str.split()[0]
                        val = next(file_obj).strip()
                        if val:
                            print(f"  {current_entry} {tag}: {val}")
        except Exception as e:
            print(f"Error reading {f}: {e}")

if __name__ == '__main__':
    db_dir = './Database'
    extract_db_names()
