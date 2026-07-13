#!/usr/bin/env bash
# Show currently connected Palworld players (name, playeruid, steamid).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

docker compose exec palworld rcon-cli ShowPlayers
