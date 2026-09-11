#!/usr/bin/env bash
# Full rebuild of the songbook including the booklet print file (Linux/macOS)
#   document.pdf          - A5, for screen
#   document-booklet.pdf  - A4 landscape, 2 pages per sheet in booklet order (print duplex, flip on short edge, fold, staple)
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
exec ./build.sh --full --booklet "$@"
