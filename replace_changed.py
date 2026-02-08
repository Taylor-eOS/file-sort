import os
import sys
import hashlib
from pathlib import Path
import shutil

def md5_of_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            block = f.read(524288)
            if not block:
                break
            h.update(block)
    return h.hexdigest()

def smart_copy_tree(src_dir, dst_dir):
    src = Path(src_dir).expanduser().resolve()
    dst = Path(dst_dir).expanduser().resolve()
    if not src.is_dir():
        print(f"Source is not a directory: {src}")
        sys.exit(1)
    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    different = 0
    errors = 0
    for src_path in src.rglob("*"):
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(src)
        dst_path = dst / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if not dst_path.exists():
            try:
                shutil.copy2(src_path, dst_path)
                copied += 1
                print(f"Created   {rel}")
            except Exception as e:
                print(f"Error creating {rel}: {e}")
                errors += 1
            continue
        try:
            src_md5 = md5_of_file(src_path)
            dst_md5 = md5_of_file(dst_path)
        except Exception as e:
            print(f"Error reading checksums for {rel}: {e}")
            errors += 1
            continue
        if src_md5 == dst_md5:
            skipped += 1
        else:
            try:
                shutil.copy2(src_path, dst_path)
                different += 1
                print(f"Replaced  {rel}  (different content)")
            except Exception as e:
                print(f"Error replacing {rel}: {e}")
                errors += 1
    print("\nSummary:")
    print(f"  New files created:     {copied}")
    print(f"  Replaced (different):  {different}")
    print(f"  Skipped (identical):   {skipped}")
    print(f"  Errors:                {errors}")
    print(f"  Total source files:    {copied + different + skipped + errors}")

if __name__ == "__main__":
    source = input('Source: ')
    destination = input('Destination: ')
    smart_copy_tree(source, destination)

