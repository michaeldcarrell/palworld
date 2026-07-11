---
name: sync-palworld-settings
description: Push edits made in the tracked, human-readable PalWorldSettings.reference.ini into the real single-line PalWorldSettings.ini that the Palworld dedicated server reads. Use after editing rates/toggles in the reference file, since the real file's OptionSettings=(...) must stay one line and is gitignored (lives in server-files/, the live game volume).
---

# Sync Palworld settings

The reference file (`PalWorldSettings.reference.ini`, tracked in git) is a
readable, grouped, commented copy of the same `OptionSettings=(...)` block
that lives in the real file the server reads:
`server-files/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini` (untracked,
part of the gitignored `server-files/` volume).

When the user asks to sync, apply, or push settings from the reference file
into the real one:

1. Run `python3 .claude/skills/sync-palworld-settings/sync.py --dry-run` from
   the repo root and show the user the diff (changed keys, anything skipped,
   anything only present in one file).
2. If the diff looks right, run the same command without `--dry-run` to
   write it. The script backs up the real file to `PalWorldSettings.ini.bak`
   before overwriting.
3. Tell the user to restart the container for the new settings to take
   effect: `docker compose restart palworld` (or `docker compose up -d` if
   the container isn't running) — Unreal Engine only reads this ini at
   server start.

Notes:
- `AdminPassword` and `ServerPassword` are intentionally redacted in the
  reference file (`<redacted-see-real-ini>`) and are always skipped by the
  script — the real file's live secrets are never overwritten by it. To
  change a password, edit the real ini directly or the `.env` file
  (`ADMIN_PASSWORD` / `SERVER_PASSWORD`) plus recreate the container.
- Keys that exist in only one of the two files are reported as warnings, not
  applied automatically — surface these to the user rather than guessing
  what to do with them.
- Never hand-edit the real ini's `OptionSettings=(...)` line directly when
  this skill is available; edit the reference copy and re-run the sync so
  the change stays reviewable in git.
