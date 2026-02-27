import os
import shutil
from pathlib import Path
import unicodedata
import last_folder_helper

dry_run = False
move_not_copy = False
list_path = 'list.txt'

def normalize_title(title):
    title = title.strip()
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.lower()
    allowed = [c for c in title if c.isalnum() or c.isspace()]
    title = ''.join(allowed)
    title = ' '.join(title.split())
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

def load_wanted_titles(list_path):
    with open(list_path, encoding='utf-8', errors='replace') as f:
        return [line.strip() for line in f if line.strip()]

def find_best_match(wanted, source_path):
    norm_wanted = normalize_title(wanted)
    best_match = None
    best_score = 0.0
    for file in source_path.iterdir():
        if not file.is_file():
            continue
        norm_file = normalize_title(file.stem)
        score = title_similarity(norm_wanted, norm_file)
        if score > best_score:
            best_score = score
            best_match = file
    return best_match, best_score

def transfer_file(src, target_path):
    if move_not_copy:
        shutil.move(src, target_path / src.name)
    else:
        shutil.copy2(src, target_path / src.name)

def process_titles(wanted_titles, source_path, target_path):
    found_count = 0
    not_found = []
    for wanted in wanted_titles:
        if not normalize_title(wanted):
            continue
        best_match, best_score = find_best_match(wanted, source_path)
        if best_score >= 0.92 and best_match:
            try:
                if not dry_run:
                    transfer_file(best_match, target_path)
                print(f"✓  {wanted}")
                print(f"   → found as: {best_match.name}")
                print(f"   (similarity: {best_score:.3f})")
                found_count += 1
            except Exception as e:
                print(f"✗  {wanted}")
                print(f"   Copy/move failed: {e}")
                not_found.append(wanted)
        else:
            print(f"✗  {wanted}")
            if best_score > 0.6 and best_match:
                print(f"   Closest was: {best_match.name} ({best_score:.3f})")
            not_found.append(wanted)
    return found_count, not_found

def print_summary(found_count, total, not_found):
    print(f"Finished.")
    print(f"Copied {found_count} of {total}.")
    if not_found:
        print("Not found titles:")
        for title in not_found:
            print(f"  - {title}")

def main(source_dir, target_dir):
    print('Files will be moved' if move_not_copy else 'Files will be copied')
    if not os.path.isfile(list_path):
        print(f"Error: Cannot find the list file {list_path}")
        return
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    if not source_path.is_dir():
        print(f"Error: Source folder not found: {source_dir}")
        return
    target_path.mkdir(parents=True, exist_ok=True)
    wanted_titles = load_wanted_titles(list_path)
    print(f"Found {len(wanted_titles)} titles in the list")
    found_count, not_found = process_titles(wanted_titles, source_path, target_path)
    print_summary(found_count, len(wanted_titles), not_found)

if __name__ == "__main__":
    default_source = last_folder_helper.get_last_folder()
    user_input = input(f"Folder with origin files ({default_source}): ").strip()
    source_dir = user_input or default_source or '.'
    last_folder_helper.save_last_folder(source_dir)
    target_dir = input("Destination folder: ").strip() or '.'
    main(source_dir, target_dir)

