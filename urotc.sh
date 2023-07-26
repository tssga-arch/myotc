#!/bin/sh

. "$(dirname "$0")"/.venv/bin/activate
. "$(dirname "$0")"/cfg.sh
exec python3 "$(dirname "$0")"/src/urotc.py "$@"
