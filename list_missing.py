import os
import sys
from pathlib import Path

def get_filenames(path):
    folder = Path(path).resolve()
    if not folder.is_dir():
        print(f"Error: {folder} is not a folder")
        sys.exit(1)
    files = set()
    for item in folder.iterdir():
        if item.is_file():
            files.add(item.name.lower())
    return files

def main():
    folder_a = input('In folder: ')
    folder_b = input('But not in folder: ')
    files_a = get_filenames(folder_a)
    files_b = get_filenames(folder_b)
    only_in_a = sorted(files_a - files_b)
    if not only_in_a:
        print("No files found that exist only in the first folder.")
        return
    print(f"Files in {folder_a}")
    print("But missing from {folder_b}")
    for norm_name in only_in_a:
        print(norm_name)

if __name__ == "__main__":
    main()

