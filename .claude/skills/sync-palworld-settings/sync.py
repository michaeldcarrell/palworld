#!/usr/bin/env python3
"""
Sync key=value pairs from PalWorldSettings.reference.ini (the tracked,
human-readable copy) into server-files/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini
(the real file the Palworld dedicated server reads).

The real file must keep OptionSettings=(...) as a single line - that's an
Unreal Engine ini format requirement, not a style choice - so this script
rewrites it in place rather than asking anyone to hand-edit that line.

Secrets (AdminPassword, ServerPassword) are intentionally redacted in the
reference copy with the placeholder below, and are always skipped so the
real file's live secrets are never clobbered.
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PATH = REPO_ROOT / "PalWorldSettings.reference.ini"
REAL_PATH = REPO_ROOT / "server-files/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini"
REDACTED_PLACEHOLDER = '"<redacted-see-real-ini>"'


def split_top_level(blob):
    """Split on commas that are not inside quotes or nested parens."""
    parts = []
    current = []
    depth = 0
    in_quotes = False
    for ch in blob:
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
        elif not in_quotes and ch == "(":
            depth += 1
            current.append(ch)
        elif not in_quotes and ch == ")":
            depth -= 1
            current.append(ch)
        elif not in_quotes and ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def parse_entries(blob):
    entries = []
    for part in split_top_level(blob):
        part = part.strip()
        if not part:
            continue
        key, sep, value = part.partition("=")
        if not sep:
            raise SystemExit(f"Could not parse entry (no '='): {part!r}")
        entries.append((key.strip(), value))
    return entries


def load_real(path):
    text = path.read_text()
    match = re.search(r"OptionSettings=\((.*)\)\s*$", text, re.DOTALL)
    if not match:
        raise SystemExit(f"Could not find OptionSettings=(...) block in {path}")
    return text, parse_entries(match.group(1))


def load_reference(path):
    in_block = False
    content_parts = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not in_block:
            if line.startswith("OptionSettings=("):
                in_block = True
                line = line[len("OptionSettings=("):]
            else:
                continue
        if line == ")":
            break
        if not line or line.startswith("#"):
            continue
        content_parts.append(line)
    if not in_block:
        raise SystemExit(f"Could not find OptionSettings=( block in {path}")
    return parse_entries("".join(content_parts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing the real ini file.",
    )
    args = parser.parse_args()

    if not REFERENCE_PATH.exists():
        raise SystemExit(f"Reference file not found: {REFERENCE_PATH}")
    if not REAL_PATH.exists():
        raise SystemExit(f"Real ini file not found: {REAL_PATH}")

    real_text, real_entries = load_real(REAL_PATH)
    ref_entries = load_reference(REFERENCE_PATH)
    ref_map = dict(ref_entries)

    real_keys = {k for k, _ in real_entries}
    ref_only_keys = [k for k in ref_map if k not in real_keys]

    changed = []
    skipped_redacted = []
    new_entries = []
    for key, old_value in real_entries:
        new_value = ref_map.get(key, old_value)
        if new_value == REDACTED_PLACEHOLDER:
            if old_value != new_value:
                skipped_redacted.append(key)
            new_value = old_value
        elif new_value != old_value:
            changed.append((key, old_value, new_value))
        new_entries.append((key, new_value))

    if changed:
        print("Changed:")
        for key, old_value, new_value in changed:
            print(f"  {key}: {old_value} -> {new_value}")
    else:
        print("No changes.")

    if skipped_redacted:
        print("\nSkipped (redacted in reference, real value kept):")
        for key in skipped_redacted:
            print(f"  {key}")

    if ref_only_keys:
        print("\nWarning: keys found in reference but not in real ini (not applied):")
        for key in ref_only_keys:
            print(f"  {key}")

    if args.dry_run:
        print("\nDry run: no files written.")
        return

    if not changed:
        return

    new_block = ",".join(f"{k}={v}" for k, v in new_entries)
    new_text = re.sub(
        r"OptionSettings=\(.*\)\s*$",
        f"OptionSettings=({new_block})",
        real_text,
        flags=re.DOTALL,
    )

    backup_path = REAL_PATH.with_suffix(REAL_PATH.suffix + ".bak")
    backup_path.write_text(real_text)
    REAL_PATH.write_text(new_text)
    print(f"\nWrote {REAL_PATH} (backup saved to {backup_path}).")
    print("Restart the palworld container for the new settings to take effect.")


if __name__ == "__main__":
    sys.exit(main())
