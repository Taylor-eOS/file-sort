import time
import random
import subprocess
import tempfile
from pathlib import Path
import urllib.parse
from copy_to_tolino import list_remote_files, copy_to_tolino, ask_yes_no
from settings import mtp_base, COPY_DELAY

def delete_remote_file(remote_name, delay_seconds):
    remote_filename_encoded = urllib.parse.quote(remote_name)
    remote_uri = mtp_base + remote_filename_encoded
    with tempfile.NamedTemporaryFile(suffix=Path(remote_name).suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(["gio", "copy", str(tmp_path), remote_uri], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        time.sleep(delay_seconds)
    finally:
        tmp_path.unlink(missing_ok=True)

def copy_to_tolino(files_to_send, delay_seconds, randomize):
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
    replaced = 0
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
        needs_delete = False
        if remote_name in existing_by_name:
            if existing_by_name[remote_name] == local_size:
                print(f'Skipping, already present: {remote_name}')
                skipped += 1
                continue
            needs_delete = True
        remote_filename_encoded = urllib.parse.quote(remote_name)
        remote_uri = mtp_base + remote_filename_encoded
        book_name = remote_name.replace(".epub", "").replace(".pdf", "")[:50]
        if needs_delete:
            print(f'Deleting outdated remote: {book_name}')
            try:
                delete_remote_file(remote_name, delay_seconds)
            except RuntimeError as e:
                print(f'ERROR: delete-via-copy failed: {e}')
                failed += 1
                failed_files.append(str(local_path))
                continue
            print(f'Replacing {book_name} ({local_size} bytes)')
        else:
            print(f'Copying {book_name} ({local_size} bytes)')
        cmd = ["gio", "copy", str(local_path), remote_uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  copied')
            if needs_delete:
                replaced += 1
            else:
                copied += 1
            existing_by_name[remote_name] = local_size
            if index < total_files:
                time.sleep(delay_seconds)
        else:
            error_msg = result.stderr.strip()
            print(f'ERROR: copying failed: {error_msg}')
            failed += 1
            failed_files.append(str(local_path))
    print(f'\nFinished: {copied} new, {replaced} replaced, {skipped} skipped, {failed} failed')
    if failed_files:
        print('Failed files:')
        for f in failed_files:
            print(f"  - {f}")

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
        copy_to_tolino(all_files, COPY_DELAY, randomize)
    print(source_dir_str)
