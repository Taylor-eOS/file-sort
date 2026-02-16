import subprocess
import urllib.parse

def run_gio(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gio command failed: {' '.join(cmd)}\nError: {result.stderr.strip()}")
    return result.stdout.strip()

mtp_base = "mtp://Rakuten_Kobo_Inc._tolino_vision_6/Interner gemeinsamer Speicher/Books/"

print("Fetching file list from device...")
out = run_gio(["gio", "list", "-l", mtp_base])

print("\nRaw output from gio:")
print("=" * 80)
lines = out.splitlines()
for i, line in enumerate(lines[:10]):
    print(f"Line {i}: {repr(line)}")
if len(lines) > 10:
    print(f"... and {len(lines) - 10} more lines")

print("\n\nParsed files:")
print("=" * 80)
files_by_name = {}
skipped_count = 0
ignored_count = 0
for raw in out.splitlines():
    line = raw.rstrip("\n")
    if not line:
        continue
    name_encoded = None
    size = None
    tab_parts = line.split("\t")
    if len(tab_parts) >= 2 and tab_parts[1].isdigit():
        name_encoded = tab_parts[0]
        size = int(tab_parts[1])
    if name_encoded is None:
        space_parts = line.split(maxsplit=1)
        if len(space_parts) == 2 and space_parts[0].isdigit():
            size = int(space_parts[0])
            name_encoded = space_parts[1]
    if name_encoded is None or size is None:
        print(f"SKIPPED (unexpected format): {repr(line)}")
        skipped_count += 1
        continue
    decoded_name = urllib.parse.unquote(name_encoded)
    if not decoded_name.lower().endswith(('.epub', '.pdf')):
        print(f"IGNORED (not a book file): {repr(line)}")
        ignored_count += 1
        continue
    files_by_name[decoded_name] = size

if skipped_count > 0:
    print(f"\n{skipped_count} lines skipped due to unexpected format")
if ignored_count > 0:
    print(f"{ignored_count} non-book files ignored")

print(f"\nTotal book files found: {len(files_by_name)}")
print("\nFirst 10 files (decoded name | size):")
for i, (decoded, size) in enumerate(list(files_by_name.items())[:10]):
    print(f"  Size: {size:>10} bytes | Name: {decoded}")

