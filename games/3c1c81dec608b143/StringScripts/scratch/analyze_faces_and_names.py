import json
import sys
from collections import Counter

def analyze():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('scratch/all_messages.json', 'r', encoding='utf-8') as f:
        messages = json.load(f)
        
    faces = [m["face"] for m in messages]
    face_counts = Counter(faces)
    
    print("Face Graphic usage count:")
    for face, count in face_counts.most_common():
        print(f"  {face}: {count}")
        
    print("\nSample dialogue per Face Graphic:")
    for face, count in face_counts.most_common():
        print(f"\n--- Face: {face} (Count: {count}) ---")
        samples = [m for m in messages if m["face"] == face]
        for s in samples[:3]:
            text_preview = s["text"].replace('\n', ' \\n ')
            print(f"  [{s['file']}:{s['start_line']}] {text_preview}")

if __name__ == '__main__':
    analyze()
