:: Full rebuild of the songbook including the booklet print file (Windows)
::   document.pdf          - A5, for screen
::   document-booklet.pdf  - A4 landscape, 2 pages per sheet in booklet order (print duplex, flip on short edge, fold, staple)
call build.cmd --full --booklet %*
