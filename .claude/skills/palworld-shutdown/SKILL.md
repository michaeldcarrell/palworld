---
name: palworld-shutdown
description: Gracefully shut down the Palworld dedicated server for maintenance — warns online players via RCON countdown, lets the world save and the process exit, then stops the compose service so it doesn't auto-restart. Use when the user wants to take the server down for maintenance, updates, or config changes.
---

# Palworld maintenance shutdown

Use this when the user wants to take the Palworld server down for
maintenance (settings changes, updates, host reboot, etc.) without abruptly
kicking online players or risking unsaved progress.

## Why not just `docker compose down`

The container has `restart: unless-stopped` in `docker-compose.yaml`. If the
game process inside exits on its own (e.g. via an RCON shutdown command),
Docker's restart policy will bring the container right back up unless it is
also explicitly stopped with `docker compose stop`/`down`. This skill's
script handles both halves: the graceful in-game shutdown *and* the
explicit compose stop that makes the down-time actually stick.

## Usage

```bash
.claude/skills/palworld-shutdown/shutdown.sh [seconds] [message]
```

- `seconds` (default `900`, i.e. 15 minutes): countdown broadcast to
  players in-game before the server saves and exits. Give players a
  reasonable warning — don't use 0 or a very short value if anyone might be
  online.
- `message` (default `"Server restarting for maintenance"`): shown to
  players during the countdown.

The script:
1. Checks the `palworld` container is running (no-ops if it's already down).
2. Sends `Shutdown <seconds> <message>` via the container's built-in
   `rcon-cli` (already configured inside the image — no extra RCON client
   or exposed port needed).
3. Polls until the container's process exits (countdown + a 15s buffer).
4. Runs `docker compose stop palworld` regardless, to guarantee the
   container lands in a stopped state and won't auto-restart.

When maintenance is done, bring it back with `docker compose up -d` (or
`docker compose start palworld`) from the repo root — this skill only
handles the shutdown half, not restarting.

## Notes

- This talks to RCON via `docker exec palworld rcon-cli ...`, using the
  `rcon.yaml` already baked into the container — nothing needs to be
  exposed on the host or added to `.env`.
- If the container isn't running, the script exits cleanly with a message
  instead of erroring.
