import os
import time
import subprocess
from pathlib import Path

def run_gio(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        return None
    return result.stdout.strip()
mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"

def list_remote_files():
    out = run_gio(["gio", "list", mtp_base])
    if out is None:
        return set()
    files = set()
    for line in out.splitlines():
        name = line.strip()
        if name:
            files.add(name)
    return files

def copy_to_tolinos(files_to_send, delay_seconds=12):
    existing = list_remote_files()
    print(f"Found {len(existing)} files already on device")
    copied = 0
    skipped = 0
    failed = 0
    for local_path_str in files_to_send:
        local_path = Path(local_path_str)
        if not local_path.is_file():
            print(f"Local file not found: {local_path}")
            failed += 1
            continue
        remote_name = local_path.name
        remote_uri = mtp_base + remote_name
        if remote_name in existing:
            print(f"Already exists, skipping: {remote_name}")
            skipped += 1
            continue
        print(f"Copying {local_path.name} ...")
        cmd = ["gio", "copy", str(local_path), remote_uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  → done")
            copied += 1
        else:
            print(f"  → failed: {result.stderr.strip()}")
            failed += 1
        time.sleep(delay_seconds)
    print(f"\nFinished: {copied} copied, {skipped} skipped, {failed} failed")

if __name__ == "__main__":
    source_dir = input('Source folder: ')
    epub_files = [str(p) for p in source_dir.glob("*.epub")]
    pdf_files  = [str(p) for p in source_dir.glob("*.pdf")]
    all_files = sorted(epub_files + pdf_files)
    if not all_files:
        print("No files found")
    else:
        copy_to_tolinos(all_files, delay_seconds=7)

