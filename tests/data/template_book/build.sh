#!/usr/bin/env bash
# Songbook builder (Linux/macOS)
#
# This builds the songbook, assuming you have lilybook_maker installed:
#  https://github.com/hardmooth/lilybook_maker
#
# usage (inside the songbook directory):
#   ./build.sh [further options for create_pdf.py, e.g. --full --booklet]
#
# Setup:
#   1. clone the lilybook_maker
#   2. either add lilybook_maker to your PATH or set LILYBOOK_MAKER to its directory

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

# Ensure `_gitshort` contains the short commit SHA for inclusion in LaTeX (see inc/intro.tex).
# If `git` isn't available or fails, write 'unknown' as a fallback.
git rev-parse --short HEAD > _gitshort 2>/dev/null || echo unknown > _gitshort

# run lilybook_maker - it will detect the LyTeX-File and build the book
"$LILYBOOK" --include=scores,inc "$@"
