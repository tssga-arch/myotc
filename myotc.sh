#!/bin/sh
. "$(dirname "$0")"/.venv/bin/activate
exec python3 "$(dirname "$0")"/myotc.py "$@"
