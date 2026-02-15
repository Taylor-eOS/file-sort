import time
import subprocess
from pathlib import Path

COPY_DELAY = 4

def run_gio(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gio command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()

mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"

def copy_to_tolino(files_to_send, delay_seconds=COPY_DELAY, randomize=False):
    import random
    files_list = list(files_to_send)
    if randomize:
        random.shuffle(files_list)
        print('Files will be copied in random order')
    copied = 0
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
        remote_uri = mtp_base + remote_name
        try:
            local_size = local_path.stat().st_size
        except OSError as e:
            print(f'ERROR: Cannot stat local file: {e}')
            failed += 1
            failed_files.append(str(local_path))
            continue
        book_name = local_path.name.replace(".epub", "").replace(".pdf", "")[:50]
        print(f'Copying {book_name} ({local_size} bytes)')
        cmd = ["gio", "copy", str(local_path), remote_uri]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'  copied')
            copied += 1
            if index < total_files:
                time.sleep(delay_seconds)
        else:
            error_msg = result.stderr.strip()
            print(f'ERROR: copying failed: {error_msg}')
            failed += 1
            failed_files.append(str(local_path))
    print(f'\nFinished: {copied} copied, {failed} failed')
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
        print('No epub or pdf files found')
    else:
        print(f'Copying {len(all_files)} files')
        randomize = ask_yes_no('Randomize file copying order?')
        copy_to_tolino(all_files, delay_seconds=COPY_DELAY, randomize=randomize)

