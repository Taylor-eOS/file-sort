import os
import unicodedata
from pathlib import Path
from collections import defaultdict

def normalize_title(title):
    title = title.strip()
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = title.lower()
    cleaned = []
    for char in title:
        if char.isalnum() or char.isspace():
            cleaned.append(char)
    title = ''.join(cleaned)
    parts = title.split()
    title = ' '.join(parts)
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

def find_duplicates(folder_path, threshold=0.92):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"Error: Folder not found: {folder_path}")
        return []
    recursive = input("Search subfolders? (y/n): ").strip().lower() == 'y'
    files = [f for f in (folder.rglob("*") if recursive else folder.iterdir()) if f.is_file()]
    print(f"Scanning {len(files)} files for duplicates...")
    duplicate_groups = []
    processed = set()
    for i, file_a in enumerate(files):
        if file_a in processed:
            continue
        norm_a = normalize_title(file_a.stem)
        if not norm_a:
            continue
        group = [file_a]
        for j in range(i + 1, len(files)):
            file_b = files[j]
            if file_b in processed:
                continue
            norm_b = normalize_title(file_b.stem)
            if not norm_b:
                continue
            score = title_similarity(norm_a, norm_b)
            if score >= threshold:
                group.append(file_b)
                processed.add(file_b)
        if len(group) > 1:
            duplicate_groups.append(group)
            processed.add(file_a)
    return duplicate_groups

def display_duplicates(duplicate_groups):
    if not duplicate_groups:
        print("\nNo duplicates found.")
        return
    print(f"\nFound {len(duplicate_groups)} potential duplicates:\n")
    for idx, group in enumerate(duplicate_groups, 1):
        print(f"Group {idx}:")
        sorted_group = sorted(group, key=lambda f: f.stat().st_mtime, reverse=True)
        for file in sorted_group:
            size = file.stat().st_size
            size_kb = size / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
            print(f"  - {file.name} ({size_str})")
        print()

def main():
    folder_path = input("Folder to scan for duplicates: ").strip()
    threshold_input = input("Similarity threshold (0.0-1.0, default 0.92): ").strip()
    if threshold_input:
        try:
            threshold = float(threshold_input)
            if not 0.0 <= threshold <= 1.0:
                print("Invalid threshold, using default 0.92")
                threshold = 0.92
        except ValueError:
            print("Invalid threshold, using default 0.92")
            threshold = 0.92
    else:
        threshold = 0.92
    duplicate_groups = find_duplicates(folder_path, threshold)
    display_duplicates(duplicate_groups)

if __name__ == "__main__":
    main()

