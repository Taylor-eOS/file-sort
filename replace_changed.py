import os
import sys
import shutil
import hashlib
from pathlib import Path
import last_folder_helper

dry_run = False

def md5_of_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            block = f.read(524288)
            if not block:
                break
            h.update(block)
    return h.hexdigest()

def smart_copy_flat(src_dir, dst_dir):
    src = Path(src_dir).expanduser().resolve()
    dst = Path(dst_dir).expanduser().resolve()
    if not src.is_dir():
        print(f"Source is not a directory: {src}")
        sys.exit(1)
    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    replaced = 0
    errors = 0
    for src_path in src.rglob("*"):
        if not src_path.is_file():
            continue
        filename = src_path.name
        dst_path = dst / filename
        if not dst_path.exists():
            copied += 1
            print(f"{'Would create' if dry_run else 'Created  '} {filename}")
            if not dry_run:
                try:
                    shutil.copy2(src_path, dst_path)
                except Exception as e:
                    print(f"Error creating {filename}: {e}")
                    copied -= 1
                    errors += 1
            continue
        try:
            src_md5 = md5_of_file(src_path)
            dst_md5 = md5_of_file(dst_path)
        except Exception as e:
            print(f"Error reading checksums for {filename}: {e}")
            errors += 1
            continue
        if src_md5 == dst_md5:
            skipped += 1
        else:
            replaced += 1
            print(f"{'Would replace' if dry_run else 'Replaced '} {filename}  (different checksum)")
            if not dry_run:
                try:
                    shutil.copy2(src_path, dst_path)
                except Exception as e:
                    print(f"Error replacing {filename}: {e}")
                    replaced -= 1
                    errors += 1
    mode_label = "DRY RUN - " if dry_run else ""
    print(f"\n{mode_label}Summary:")
    print(f"  New files {'to be ' if dry_run else ''}created:     {copied}")
    print(f"  {'Would be replaced' if dry_run else 'Replaced'} (different):  {replaced}")
    print(f"  Skipped (identical):   {skipped}")
    print(f"  Errors:                {errors}")
    print(f"  Total source files:    {copied + replaced + skipped + errors}")

if __name__ == "__main__":
    source = input('Source: ')
    default_destination = last_folder_helper.get_last_folder()
    user_input = input(f"Destination ({default_destination}): ").strip()
    destination_dir = user_input or default_destination
    last_folder_helper.save_last_folder(destination_dir)
    smart_copy_flat(source, destination_dir)
    print(f'Source: {source}, destination: {destination_dir}')

