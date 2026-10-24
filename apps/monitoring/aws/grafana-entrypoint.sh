#!/bin/sh
set -eu
mkdir -p "$GF_PATHS_DATA" "$GF_PATHS_LOGS" "$GF_PATHS_PLUGINS"
exec /run.sh "$@"
