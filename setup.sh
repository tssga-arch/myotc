#!/bin/sh
target=$(dirname "$0")
cd "$target"

python3 -m venv --system-site-packages .venv
. .venv/bin/activate
pip install --only-binary=cryptography,netifaces python-openstackclient otcextensions
pip install passlib

# sphinx related dependancies
pip install docutils sphinx
pip install myst-parser sphinx-autodoc2 sphinx-argparse
