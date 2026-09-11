#!/usr/bin/env bash
# Songbook builder (Linux/macOS counterpart of build.cmd)
#
# This builds the songbook, assuming you have lilybook_maker installed:
#  https://github.com/hardmooth/lilybook_maker
#
# usage (inside a songbook directory):
#   ./build.sh [options for create_pdf.py]
#
# Setup:
#   1. clone the lilybook_maker
#   2. either add lilybook_maker to your PATH or set LILYBOOK_MAKER to its directory
#   3. fork the lilybook_template
#   4. copy this build.sh to your songbook directory (chmod +x build.sh)

set -u
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

if [ -n "${LILYBOOK_MAKER:-}" ]; then
    LILYBOOK="$LILYBOOK_MAKER/lilybook.sh"
elif command -v lilybook.sh >/dev/null 2>&1; then
    LILYBOOK="lilybook.sh"
elif [ -x "./lilybook_maker/lilybook.sh" ]; then
    LILYBOOK="./lilybook_maker/lilybook.sh"
elif [ -x "../lilybook_maker/lilybook.sh" ]; then
    LILYBOOK="../lilybook_maker/lilybook.sh"
else
    echo "lilybook_maker not found. Add it to PATH or set LILYBOOK_MAKER=/path/to/lilybook_maker" >&2
    exit 2
fi

# simply run lilybook_maker (it will detect your LyTeX-File and build the book)
"$LILYBOOK" "$@"
