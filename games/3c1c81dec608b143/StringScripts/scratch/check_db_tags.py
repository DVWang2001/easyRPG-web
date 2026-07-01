import os
import re
import sys

def check_db_tags():
    sys.stdout.reconfigure(encoding='utf-8')
    db_dir = './Database'
    if not os.path.exists(db_dir):
        print("Database directory not found.")
        return
        
    tag_re = re.compile(r'#(\w+)#')
    db_tags = {}
    
    for f in sorted(os.listdir(db_dir)):
        path = os.path.join(db_dir, f)
        if os.path.isfile(path) and f.endswith('.txt'):
            tags = set()
            try:
                with open(path, 'r', encoding='utf-8-sig') as file_obj:
                    for line in file_obj:
                        matches = tag_re.findall(line)
                        for m in matches:
                            tags.add(m)
            except Exception as e:
                print(f"Error reading {f}: {e}")
            db_tags[f] = sorted(list(tags))
            
    print("Database tags per file:")
    for fn, tags in db_tags.items():
        print(f"{fn}: {tags}")

if __name__ == '__main__':
    check_db_tags()
