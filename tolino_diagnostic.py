import subprocess
import urllib.parse
from copy_to_tolino import run_gio

LIST_ALL_FILES = False

def fetch_gio_listing(mtp_base):
    cmd = ["gio", "list", "-l", mtp_base]
    return run_gio(cmd)

def parse_gio_line(line):
    line = line.rstrip("\n")
    if not line:
        return None, None
    tab_parts = line.split("\t")
    if len(tab_parts) >= 2 and tab_parts[1].isdigit():
        name_encoded = tab_parts[0]
        size = int(tab_parts[1])
        return urllib.parse.unquote(name_encoded), size
    space_parts = line.split(maxsplit=1)
    if len(space_parts) == 2 and space_parts[0].isdigit():
        size = int(space_parts[0])
        name_encoded = space_parts[1]
        return urllib.parse.unquote(name_encoded), size
    return None, None

def is_book_file(filename):
    return filename.lower().endswith(('.epub', '.pdf'))

def collect_files(raw_output, list_all=False):
    files_by_name = {}
    skipped_count = 0
    zero_byte_count = 0
    for raw_line in raw_output.splitlines():
        decoded_name, size = parse_gio_line(raw_line)
        if decoded_name is None or size is None:
            if raw_line.strip():
                print(f"SKIPPED (unexpected format): {repr(raw_line)}")
                skipped_count += 1
            continue
        if size == 0:
            zero_byte_count += 1
            continue
        files_by_name[decoded_name] = size
    return files_by_name, skipped_count, zero_byte_count

def print_diagnostics(files_by_name, skipped_count, zero_byte_count, list_all=False):
    if skipped_count > 0:
        print(f"\n{skipped_count} lines skipped due to unexpected format")
    #if zero_byte_count > 0:
    #    print(f"{zero_byte_count} entries skipped (0 bytes – usually folders)")
    print(f"Total files size > 0 found: {len(files_by_name)}")
    if files_by_name:
        if list_all:
            print("All parsed files (decoded name, size):")
            for name, size in sorted(files_by_name.items()):
                print(f"Size: {size} bytes, name: {name.replace(".epub", "").replace(".pdf", "")[:50]}")
        else:
            print("First 10 book files (decoded name,  size):")
            for i, (name, size) in enumerate(list(files_by_name.items())[:10]):
                print(f"Size: {size} bytes, name: {name.replace(".epub", "").replace(".pdf", "")[:50]}")

def main():
    mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"
    lim = 8
    print("Fetching file list from device...")
    raw_output = fetch_gio_listing(mtp_base)
    print(f"Raw output from gio:")
    lines = raw_output.splitlines()
    for i, line in enumerate(lines[:lim]):
        print(f"Line {i}: {repr(line)}")
    if len(lines) > lim:
        print(f"...")
    print("\nParsed files:")
    files_by_name, skipped, zeros = collect_files(raw_output, list_all=LIST_ALL_FILES)
    print_diagnostics(files_by_name, skipped, zeros, list_all=LIST_ALL_FILES)

if __name__ == "__main__":
    main()

