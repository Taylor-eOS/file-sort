import time
import subprocess
from pathlib import Path
import urllib.parse

COPY_DELAY = 4

def run_gio(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gio command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()

mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"

def list_remote_files():
    out = run_gio(["gio", "list", "-l", mtp_base])
    files_by_name = {}
    skipped_count = 0
    for raw in out.splitlines():
        line = raw.rstrip("\n")
        if not line:
            continue
        tab_parts = line.split("\t")
        if len(tab_parts) >= 2 and tab_parts[1].isdigit():
            name_encoded = tab_parts[0]
            size = int(tab_parts[1])
            decoded_name = urllib.parse.unquote(name_encoded)
            if decoded_name.lower().endswith(('.epub', '.pdf')):
                files_by_name[decoded_name] = size
            continue
        space_parts = line.split(maxsplit=1)
        if len(space_parts) == 2 and space_parts[0].isdigit():
            size = int(space_parts[0])
            name_encoded = space_parts[1]
            decoded_name = urllib.parse.unquote(name_encoded)
            if decoded_name.lower().endswith(('.epub', '.pdf')):
                files_by_name[decoded_name] = size
            continue
        skipped_count += 1
    if skipped_count > 0:
        print(f'WARNING: Failed to parse {skipped_count} lines from device listing')
    return files_by_name

def copy_to_tolino(files_to_send, delay_seconds=COPY_DELAY, randomize=False):
    import random
    print('Reading file list from device...')
    try:
        existing_by_name = list_remote_files()
        print(f'Found {len(existing_by_name)} files already on device')
    except RuntimeError as e:
        print(f'WARNING: Could not read device file list: {e}')
        print('Will attempt to copy all files without skipping duplicates')
        existing_by_name = {}
    files_list = list(files_to_send)
    if randomize:
        random.shuffle(files_list)
        print('Files will be copied in random order')
    copied = 0
    skipped = 0
    failed = 0
    failed_files = []
    total_files = len(files_list)
    for index, local_path_str in enumerate(files_list, 1):
        local_path = Path(local_path_str)
        print(f'{index}/{total_files}')
        if not local_path.is_file():
            print(f'ERROR: Local file not found: {local_path}')
            failed += 1
            failed_files.append(str(local_path))
            continue
        remote_name = local_path.name
        try:
            local_size = local_path.stat().st_size
        except OSError as e:
            print(f'ERROR: Cannot stat local file: {e}')
            failed += 1
            failed_files.append(str(local_path))
            continue
        if remote_name in existing_by_name or any(s == local_size for s in existing_by_name.values()):
            print(f'Skipping, already present by name or size: {remote_name}')
            skipped += 1
            continue
        remote_filename_encoded = urllib.parse.quote(remote_name)
        remote_uri = mtp_base + remote_filename_encoded
        book_name = remote_name.replace(".epub", "").replace(".pdf", "")[:50]
        print(f'Copying {book_name} ({local_size} bytes)')
        cmd = ["gio", "copy", str(local_path), remote_uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  copied')
            copied += 1
            existing_by_name[remote_name] = local_size
            if index < total_files:
                time.sleep(delay_seconds)
        else:
            error_msg = result.stderr.strip()
            print(f'ERROR: copying failed: {error_msg}')
            failed += 1
            failed_files.append(str(local_path))
    print(f'\nFinished: {copied} copied, {skipped} skipped, {failed} failed')
    if failed_files:
        print('Failed files:')
        for f in failed_files:
            print(f"  - {f}")

def ask_yes_no(prompt):
    while True:
        response = input(prompt + " (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print('Please enter y or n')

if __name__ == "__main__":
    while True:
        source_dir_str = input('Folder with files to be copied: ').strip()
        source_dir = Path(source_dir_str)
        if source_dir.is_dir():
            break
        print(f'Error: {source_dir} is not a folder or does not exist')
    epub_files = [str(p) for p in source_dir.glob("*.epub")]
    pdf_files  = [str(p) for p in source_dir.glob("*.pdf")]
    all_files = sorted(epub_files + pdf_files)
    print(f'Delay {COPY_DELAY} seconds')
    if not all_files:
        print('No files found')
    else:
        print(f'Copying {len(all_files)} files')
        randomize = ask_yes_no('Randomize file copying order?')
        copy_to_tolino(all_files, delay_seconds=COPY_DELAY, randomize=randomize)
    print(source_dir_str)
