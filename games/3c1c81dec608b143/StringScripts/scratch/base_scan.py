import os
import json
import sys

def count_tags(filepath):
    tags = ["#Message#", "#Choice#", "Select Face Graphic"]
    counts = {t: 0 for t in tags}
    lines_count = 0
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                lines_count += 1
                for t in tags:
                    if t in line:
                        counts[t] += 1
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    return counts, lines_count

def scan_workspace():
    sys.stdout.reconfigure(encoding='utf-8')
    results = {}
    
    # Files in the root (Map*.txt)
    for f in sorted(os.listdir('.')):
        if f.startswith('Map') and f.endswith('.txt'):
            counts, lines_count = count_tags(f)
            results[f] = {
                "tags": counts,
                "lines": lines_count
            }
            
    # Files in Database
    db_dir = './Database'
    if os.path.exists(db_dir):
        for f in sorted(os.listdir(db_dir)):
            path = os.path.join(db_dir, f)
            if os.path.isfile(path) and f.endswith('.txt'):
                counts, lines_count = count_tags(path)
                results[f"Database/{f}"] = {
                    "tags": counts,
                    "lines": lines_count
                }
                
    # Files in Database/Commons
    commons_dir = './Database/Commons'
    if os.path.exists(commons_dir):
        for f in sorted(os.listdir(commons_dir)):
            path = os.path.join(commons_dir, f)
            if os.path.isfile(path) and f.endswith('.txt'):
                counts, lines_count = count_tags(path)
                results[f"Database/Commons/{f}"] = {
                    "tags": counts,
                    "lines": lines_count
                }

    report_path = 'scratch/base_scan_report.json'
    os.makedirs('scratch', exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"Scan complete. Report saved to {report_path}")
    
    # Print a summary
    total_msgs = sum(r["tags"]["#Message#"] for r in results.values())
    total_choices = sum(r["tags"]["#Choice#"] for r in results.values())
    total_faces = sum(r["tags"]["Select Face Graphic"] for r in results.values())
    total_lines = sum(r["lines"] for r in results.values())
    print(f"Total Lines: {total_lines}")
    print(f"Total #Message#: {total_msgs}")
    print(f"Total #Choice#: {total_choices}")
    print(f"Total Select Face Graphic: {total_faces}")

if __name__ == '__main__':
    scan_workspace()
