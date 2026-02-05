import os
import re
import shutil
from pathlib import Path
import unicodedata

dry_run = False
move_not_copy = False
list_path = 'list.txt'

def normalize_title(title):
    title = title.strip()
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

def title_similarity(a, b):
    if not a or not b:
        return 0
    if a == b:
        return 1.0
    len_a = len(a)
    len_b = len(b)
    if abs(len_a - len_b) > 3:
        return 0.0
    distance = 0
    i = j = 0
    while i < len_a and j < len_b:
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            distance += 1
            if len_a > len_b:
                i += 1
            elif len_b > len_a:
                j += 1
            else:
                i += 1
                j += 1
            if distance > 3:
                return 0.0
    distance += abs(len_a - i) + abs(len_b - j)
    max_len = max(len_a, len_b)
    similarity = 1.0 - (distance / max_len)
    return similarity if similarity > 0 else 0.0

print('Files will be moved' if move_not_copy else 'Files will be copied')
#list_path = input("Text file with file name list: ").strip()
source_dir = input("Folder with origin files: ").strip()
target_dir = input("Destination folder: ").strip()
if not os.path.isfile(list_path):
    print(f"Error: Cannot find the list file {list_path}")
    exit(1)
source_path = Path(source_dir)
target_path = Path(target_dir)
if not source_path.is_dir():
    print(f"Error: Source folder not found: {source_dir}")
    exit(1)
target_path.mkdir(parents=True, exist_ok=True)
with open(list_path, encoding='utf-8', errors='replace') as f:
    wanted_titles = [line.strip() for line in f if line.strip()]
print(f"Found {len(wanted_titles)} titles in the list")
found_count = 0
not_found = []
for wanted in wanted_titles:
    norm_wanted = normalize_title(wanted)
    if not norm_wanted:
        continue
    best_match = None
    best_score = 0.0
    best_filename = ""
    for file in source_path.iterdir():
        if not file.is_file():
            continue
        norm_file = normalize_title(file.stem)
        score = title_similarity(norm_wanted, norm_file)
        if score > best_score:
            best_score = score
            best_match = file
            best_filename = file.name
    if best_score >= 0.92 and best_match:
        try:
            if not dry_run:
                if move_not_copy:
                    shutil.move(best_match, target_path / best_match.name)
                else:
                    shutil.copy2(best_match, target_path / best_match.name)
            print(f"✓  {wanted}")
            print(f"   → found as: {best_filename}")
            print(f"   (similarity: {best_score:.3f})")
            found_count += 1
        except Exception as e:
            print(f"✗  {wanted}")
            print(f"   Copy/move failed: {e}")
    else:
        print(f"✗  {wanted}")
        if best_score > 0.6:
            print(f"   Closest was: {best_filename} ({best_score:.3f})")
        not_found.append(wanted)
print(f"Finished.")
print(f"Copied {found_count} of {len(wanted_titles)}.")
if not_found:
    print("Not found titles:")
    for title in not_found:
        print(f"  - {title}")

