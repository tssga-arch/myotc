#!/bin/sh
. "$(dirname "$0")"/.venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(dirname "$0")
exec python3 "$(dirname "$0")"/src/myotc.py -I "$(dirname "$0")/snippets" "$@"
