# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repo runs a self-hosted Palworld dedicated server via the
`thijsvanloef/palworld-server-docker` Docker image. It is a sibling repo to
`/home/michael/apps` (which manages other home-server services and has its
own CLAUDE.md); this one is scoped only to the Palworld server.

## Commands

```bash
docker compose up -d          # start the server
docker compose down           # stop
docker compose restart palworld  # restart (required after any settings change)
docker compose logs -f        # tail server logs
```

## Architecture

- `docker-compose.yaml` — single `palworld` service. Game/query ports and
  most server options (player count, RCON, admin/server passwords, name) are
  set via environment variables, some sourced from `.env`
  (`ADMIN_PASSWORD`, `SERVER_PASSWORD` — gitignored, not committed).
- `server-files/` — the container's entire `/palworld` volume (save data,
  binaries, backups, engine config). Gitignored in full; this is live game
  state, not source.
- `PalWorldSettings.reference.ini` — the **only** tracked copy of gameplay
  settings (rates, difficulty, PvP, build limits, etc.). It's a
  human-readable, grouped/commented re-listing of the same
  `OptionSettings=(...)` block found in the real config at
  `server-files/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini`. The real
  file is untracked (lives under gitignored `server-files/`) and its
  `OptionSettings=(...)` must remain a single line — an Unreal Engine ini
  format requirement, not a style choice. `AdminPassword`/`ServerPassword`
  are redacted as `<redacted-see-real-ini>` in the reference copy and are
  never written by the sync tooling; change those via `.env` +
  `docker compose up -d`, or by hand-editing the real ini directly.

### Editing gameplay settings

Never hand-edit the real ini's `OptionSettings=(...)` line directly — edit
`PalWorldSettings.reference.ini` instead, then sync:

```bash
python3 .claude/skills/sync-palworld-settings/sync.py --dry-run   # review the diff
python3 .claude/skills/sync-palworld-settings/sync.py             # apply (backs up real file to PalWorldSettings.ini.bak)
docker compose restart palworld   # required — settings are only read at server start
```

The `sync-palworld-settings` skill (`.claude/skills/sync-palworld-settings/`)
wraps this workflow. Keys present in only one of the two files are reported
as warnings, not auto-applied — surface these to the user rather than
guessing.

### Off-site backups

An external Airflow DAG (`palworld_backup_to_gcs`, in the `/home/michael/apps`
repo) runs hourly and uploads new save tarballs from this container's local
backup dir to GCS — not part of this repo, but worth knowing about when
reasoning about `server-files/backups/`.
