#!/bin/sh
. "$(dirname "$0")"/.venv/bin/activate
exec python3 "$@"
