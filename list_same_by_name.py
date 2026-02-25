from pathlib import Path
from replace_changed import md5_of_file

def find_files_in_both(folder1_path, folder2_path):
    folder1 = Path(folder1_path).expanduser().resolve()
    folder2 = Path(folder2_path).expanduser().resolve()
    names1 = {p.name: p for p in folder1.iterdir() if p.is_file()}
    names2 = {p.name: p for p in folder2.iterdir() if p.is_file()}
    print(f"Found {len(names1)} files in first folder")
    print(f"Found {len(names2)} files in second folder")
    shared_names = sorted(set(names1) & set(names2))
    matches = [(names1[n], names2[n]) for n in shared_names]
    return matches, folder1, folder2

def show_matches(pairs, folder1, folder2):
    if not pairs:
        print("No files with the same name found in both folders.")
        return
    print(f"Found {len(pairs)} file(s) present in both folders:\n")
    for p1, p2 in pairs:
        same = md5_of_file(p1) == md5_of_file(p2)
        tag = "identical" if same else "DIFFER"
        size1 = p1.stat().st_size
        size2 = p2.stat().st_size
        size_note = "" if same else f" ({size1} vs {size2} bytes)"
        print(f"  {p1.name}  [{tag}]{size_note}")

def main():
    folder1 = input("First folder to compare: ").strip()
    folder2 = input("Second folder to compare: ").strip()
    pairs, f1, f2 = find_files_in_both(folder1, folder2)
    show_matches(pairs, f1, f2)

if __name__ == "__main__":
    main()
