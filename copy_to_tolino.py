import os
import time
import subprocess
import random
import hashlib
from pathlib import Path

COPY_DELAY = 3
FAIL_RETRIES = 3

def run_gio(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gio command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()

mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"

def calculate_md5(file_path):
    md5_hash = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
    except IOError as e:
        raise RuntimeError(f"Failed to read file for MD5: {file_path}") from e
    return md5_hash.hexdigest()

def calculate_remote_md5(remote_uri):
    result = subprocess.run(["gio", "cat", remote_uri], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read remote file: {remote_uri}\nError: {result.stderr.decode('utf-8', errors='replace').strip()}")
    md5_hash = hashlib.md5()
    md5_hash.update(result.stdout)
    return md5_hash.hexdigest()

def list_remote_files():
    out=run_gio(["gio","list","-l",mtp_base])
    files={}
    for raw in out.splitlines():
        line=raw.rstrip("\n")
        if not line:
            continue
        parts=line.split(maxsplit=1)
        if len(parts)==2 and parts[0].isdigit():
            size=int(parts[0])
            name=parts[1]
        else:
            size=None
            name=line
        name=decode_uri_name(name)
        files[name]=size
    return files

def decode_uri_name(name):
    result=[]
    i=0
    length=len(name)
    while i<length:
        ch=name[i]
        if ch=="%" and i+2<length:
            hexpart=name[i+1:i+3]
            try:
                result.append(chr(int(hexpart,16)))
                i+=3
                continue
            except ValueError:
                pass
        result.append(ch)
        i+=1
    return "".join(result)

def verify_remote_file(remote_uri, expected_md5):
    #wait_seconds(1)
    actual_md5 = calculate_remote_md5(remote_uri)
    if actual_md5 != expected_md5:
        raise RuntimeError(f'MD5 mismatch: expected {expected_md5}, got {actual_md5}')
    return True

def delete_remote_file(remote_uri, max_retries=FAIL_RETRIES, retry_delay=COPY_DELAY):
    cmd = ["gio", "remove", remote_uri]
    last_error = None
    for attempt in range(max_retries):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, None
        error_msg = result.stderr.strip()
        last_error = error_msg
        if attempt < max_retries - 1:
            print(f'  delete failed, retry {attempt + 2}/{max_retries}')
            wait_seconds(retry_delay)
    return False, last_error

def copy_file(local_path, remote_uri, expected_md5, max_retries=FAIL_RETRIES, retry_delay=COPY_DELAY):
    cmd = ["gio", "copy", str(local_path), remote_uri]
    last_error = None
    for attempt in range(max_retries):
        check_result = subprocess.run(["gio", "info", remote_uri], capture_output=True, text=True)
        if check_result.returncode == 0:
            print(f'  file exists on device, deleting first')
            delete_success, delete_error = delete_remote_file(remote_uri, max_retries=max_retries, retry_delay=retry_delay)
            if not delete_success:
                last_error = f"Cannot delete existing file: {delete_error}"
                if attempt < max_retries - 1:
                    print(f'  delete failed, retry {attempt + 2}/{max_retries}')
                    wait_seconds(retry_delay)
                    continue
                return False, last_error
            wait_seconds(retry_delay)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            wait_seconds(retry_delay)
            verification_retries = 3
            for verify_attempt in range(verification_retries):
                try:
                    verify_remote_file(remote_uri, expected_md5)
                    return True, None
                except RuntimeError as e:
                    error_str = str(e)
                    is_read_failure = "Failed to read remote file" in error_str
                    is_md5_mismatch = "MD5 mismatch" in error_str
                    if (is_read_failure or is_md5_mismatch) and verify_attempt < verification_retries - 1:
                        wait_time = retry_delay * (verify_attempt + 1)
                        print(f'  verification failed (attempt {verify_attempt + 1}/{verification_retries}), waiting {wait_time}s')
                        wait_seconds(wait_time)
                        continue
                    return False, error_str
        error_msg = result.stderr.strip()
        last_error = error_msg
        is_cache_error = "couldn't add object to cache" in error_msg.lower()
        if is_cache_error and attempt < max_retries - 1:
            wait_time = retry_delay * (attempt + 1)
            print(f'  device not ready, waiting {wait_time}s before retry {attempt + 2}/{max_retries}')
            wait_seconds(wait_time)
        elif attempt < max_retries - 1:
            print(f'  copy failed, retry {attempt + 2}/{max_retries}')
            wait_seconds(retry_delay)
    return False, last_error

def copy_to_tolino(files_to_send, delay_seconds=COPY_DELAY, randomize=False):
    try:
        existing = list_remote_files()
    except RuntimeError as e:
        print(f'FATAL: Failed to list remote files: {e}')
        print('Cannot proceed safely without knowing what is already on the device.')
        return
    print(f'Found {len(existing)} files already on device')
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
        remote_uri = mtp_base + remote_name
        try:
            local_size = local_path.stat().st_size
        except OSError as e:
            print(f'ERROR: Cannot stat local file: {e}')
            failed += 1
            failed_files.append(str(local_path))
            continue
        if remote_name in existing:
            remote_size = existing[remote_name]
            if remote_size == local_size:
                print(f'Already exists (same size), verifying integrity: {remote_name}')
                try:
                    local_md5 = calculate_md5(local_path)
                    verify_remote_file(remote_uri, local_md5)
                    print(f'  integrity verified, skipping')
                    skipped += 1
                    continue
                except RuntimeError as e:
                    print(f'  integrity check failed: {e}')
                    print(f'  will delete and re-copy')
            else:
                print(f'File exists but size mismatch (local:{local_size} remote:{remote_size}), will delete and re-copy')
            print(f'  deleting existing file')
            delete_success, delete_error = delete_remote_file(remote_uri)
            if not delete_success:
                print(f'ERROR: failed to delete existing file: {delete_error}')
                failed += 1
                failed_files.append(str(local_path))
                continue
            print(f'  file deleted')
            wait_seconds(delay_seconds)
            del existing[remote_name]
        book_name = local_path.name.replace(".epub", "").replace(".pdf", "")[:30]
        print(f'Copying {book_name} ({local_size} bytes)')
        try:
            local_md5 = calculate_md5(local_path)
        except RuntimeError as e:
            print(f'ERROR: {e}')
            failed += 1
            failed_files.append(str(local_path))
            continue
        success, error_msg = copy_file(local_path, remote_uri, local_md5, retry_delay=delay_seconds)
        if success:
            print(f'  checksum verified')
            copied += 1
            existing[remote_name] = local_size
        else:
            print(f'ERROR: copying failed: {error_msg}')
            failed += 1
            failed_files.append(str(local_path))
        wait_seconds(delay_seconds)
    print(f'\nFinished: {copied} copied, {skipped} skipped, {failed} failed')
    if failed_files:
        print('Failed files:')
        for f in failed_files:
            print(f"  - {f}")

def wait_seconds(seconds):
    if False: print(f'Wait {seconds} seconds')
    time.sleep(seconds)

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
        print(f'Error: {source_dir} is not a folder or does not exist, try again')
    epub_files = [str(p) for p in source_dir.glob("*.epub")]
    pdf_files  = [str(p) for p in source_dir.glob("*.pdf")]
    all_files = sorted(epub_files + pdf_files)
    if not all_files:
        print('No epub or pdf files found in the folder?')
    else:
        print(f'Found {len(all_files)} files to process')
        randomize = ask_yes_no('Randomize file copying order?')
        copy_to_tolino(all_files, delay_seconds=COPY_DELAY, randomize=randomize)
    print(f'{source_dir_str}')
