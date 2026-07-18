#!/usr/bin/env bash
# Gracefully shuts down the Palworld dedicated server for maintenance:
# broadcasts a countdown warning to online players via RCON, lets the
# server save and exit on its own, then explicitly stops the compose
# service so Docker's `restart: unless-stopped` policy doesn't just bring
# it back up again.
set -euo pipefail

SECONDS_UNTIL_SHUTDOWN="${1:-900}"
MESSAGE="${2:-Server restarting for maintenance}"
COMPOSE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

if ! docker inspect -f '{{.State.Running}}' palworld 2>/dev/null | grep -q true; then
  echo "palworld container is not running; nothing to shut down."
  exit 0
fi

echo "Sending RCON shutdown: ${SECONDS_UNTIL_SHUTDOWN}s countdown, message: \"${MESSAGE}\""
# rcon-cli treats each CLI argument as its own separate RCON command (see
# `rcon-cli --help`'s "command1 command2" example) rather than splitting one
# command's arguments for us. The whole "Shutdown <seconds> <message>" must
# be passed as a single argument or it silently runs "Shutdown" bare
# (defaulting to a ~30s countdown) followed by two bogus commands.
docker exec palworld rcon-cli "Shutdown ${SECONDS_UNTIL_SHUTDOWN} ${MESSAGE}"

# Give the in-game countdown/save a buffer beyond the requested delay before
# we poll, then confirm the container has actually stopped.
BUFFER=15
DEADLINE=$((SECONDS_UNTIL_SHUTDOWN + BUFFER))
echo "Waiting up to ${DEADLINE}s for the server to save and exit..."
elapsed=0
while [ "$elapsed" -lt "$DEADLINE" ]; do
  if ! docker inspect -f '{{.State.Running}}' palworld 2>/dev/null | grep -q true; then
    break
  fi
  sleep 5
  elapsed=$((elapsed + 5))
done

echo "Stopping the compose service to prevent auto-restart (restart: unless-stopped)..."
(cd "$COMPOSE_DIR" && docker compose stop palworld)

echo "Palworld server is stopped and safe for maintenance."
