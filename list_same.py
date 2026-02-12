import hashlib
from pathlib import Path
from collections import defaultdict
from replace_changed import md5_of_file

def find_identical_files(folder1_path, folder2_path):
    folder1 = Path(folder1_path).expanduser().resolve()
    folder2 = Path(folder2_path).expanduser().resolve()
    files1 = [p for p in folder1.iterdir() if p.is_file()]
    files2 = [p for p in folder2.iterdir() if p.is_file()]
    print(f"Found {len(files1)} files in first folder")
    print(f"Found {len(files2)} files in second folder")
    size_to_paths = defaultdict(list)
    for p in files1 + files2:
        try:
            size = p.stat().st_size
            size_to_paths[size].append(p)
        except:
            pass
    matches = []
    for size, paths in size_to_paths.items():
        if len(paths) < 2:
            continue
        checksum_to_paths = defaultdict(list)
        for p in paths:
            cs = md5_of_file(p)
            checksum_to_paths[cs].append(p)
        for cs, group in checksum_to_paths.items():
            if len(group) >= 2:
                matches.append(group)
    return matches, folder1, folder2

def show_matches(groups, folder1, folder2):
    if not groups:
        print("\nNo identical files found.")
        return
    print(f"\nFound {len(groups)} group(s) of identical files:\n")
    for i, group in enumerate(groups, 1):
        size = group[0].stat().st_size
        size_kb = size / 1024
        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
        print(f"Group {i} – {size_str}")
        for p in group:
            if p.is_relative_to(folder1):
                print(f"  Folder 1: {p.name}")
            else:
                print(f"  Folder 2: {p.name}")
        print()

def main():
    folder1 = input("First folder: ").strip()
    folder2 = input("Second folder: ").strip()
    groups, f1, f2 = find_identical_files(folder1, folder2)
    show_matches(groups, f1, f2)

if __name__ == "__main__":
    main()

