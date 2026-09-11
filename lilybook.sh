#!/usr/bin/env bash
# Linux/macOS counterpart of lilybook.cmd
#
# usage (inside your songbook directory, next to <your_book>.lytex):
#   /path/to/lilybook_maker/lilybook.sh [options for create_pdf.py] [<your_book>.lytex]
#
# Setup:
#   1. clone this source folder
#   2. optionally add the folder to your PATH (e.g. in ~/.bashrc):
#        export PATH="$PATH:/path/to/lilybook_maker"
#   3. install the python requirements, either system wide
#        python3 -m pip install -r requirements_py.txt
#      or into a virtual environment next to this script (picked up automatically):
#        python3 -m venv .venv && .venv/bin/pip install -r requirements_py.txt
#
# The python interpreter can be overridden with the environment variable LILYBOOK_PYTHON.

set -u

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

if [ -n "${LILYBOOK_PYTHON:-}" ]; then
    PYTHON="$LILYBOOK_PYTHON"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON="python3"
fi

# run the python PDF builder (it will detect your LyTeX-File and build the book)
# and forward all parameters given to this script: "$@"
exec "$PYTHON" "$SCRIPT_DIR/create_pdf.py" "$@"
