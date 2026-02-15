import os
import time
import subprocess
import random
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

def copy_file(local_path, remote_uri, max_retries=2, retry_delay=10):
    cmd = ["gio", "copy", str(local_path), remote_uri]
    for attempt in range(max_retries):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, None
        error_msg = result.stderr.strip()
        is_cache_error = "couldn't add object to cache" in error_msg.lower()
        if is_cache_error and attempt < max_retries - 1:
            wait_time = retry_delay * (attempt + 1)
            print(f"  device not ready, waiting {wait_time}s before retry {attempt + 2}/{max_retries}")
            time.sleep(wait_time)
        else:
            return False, error_msg
    return False, error_msg

def copy_to_tolino(files_to_send, delay_seconds=12, randomize=False):
    existing = list_remote_files()
    if existing is None:
        print("Failed to list remote files. Cannot proceed safely.")
        return
    print(f"Found {len(existing)} files already on device")
    files_list = list(files_to_send)
    if randomize:
        random.shuffle(files_list)
        print("Files will be copied in random order")
    copied = 0
    skipped = 0
    failed = 0
    failed_files = []
    for local_path_str in files_list:
        local_path = Path(local_path_str)
        if not local_path.is_file():
            print(f"Local file not found: {local_path}")
            failed += 1
            failed_files.append(str(local_path))
            continue
        remote_name = local_path.name
        remote_uri = mtp_base + remote_name
        if remote_name in existing:
            print(f"Skipping: {remote_name}")
            print(f"  already exists")
            skipped += 1
            continue
        print(f"Copying {local_path.name}")
        success, error_msg = copy_file(local_path, remote_uri)
        if success:
            print(f"  file copied")
            copied += 1
            existing.add(remote_name)
        else:
            print(f"  FAILED: {error_msg}")
            failed += 1
            failed_files.append(str(local_path))
        time.sleep(delay_seconds)
    print(f"\nFinished: {copied} copied, {skipped} skipped, {failed} failed")
    if failed_files:
        print("Failed files:")
        for f in failed_files:
            print(f"  - {f}")

def ask_yes_no(prompt):
    while True:
        response = input(prompt + " (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    while True:
        source_dir_str = input('Folder with files to be copied: ').strip()
        source_dir = Path(source_dir_str)
        if source_dir.is_dir():
            break
        print(f"Error:  '{source_dir}' is not a folder or does not exist, try again")
    epub_files = [str(p) for p in source_dir.glob("*.epub")]
    pdf_files  = [str(p) for p in source_dir.glob("*.pdf")]
    all_files = sorted(epub_files + pdf_files)
    if not all_files:
        print("No epub or pdf files found in the folder")
    else:
        print(f"Found {len(all_files)} files to process")
        randomize = ask_yes_no("Copy files in random order?")
        copy_to_tolino(all_files, delay_seconds=8, randomize=randomize)

