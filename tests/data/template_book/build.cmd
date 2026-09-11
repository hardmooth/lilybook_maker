:: Songbook builder (Windows)
::
:: This builds the songbook, assuming you have lilybook_maker installed:
::  https://github.com/hardmooth/lilybook_maker
::
:: usage (either of the following):
::   double click on this script (or run it in CMD)
::   build.cmd [further options for create_pdf.py, e.g. --full --booklet]
::
:: Setup:
::   1. clone the lilybook_maker
::   2. add lilybook_maker to PATH variable (User Path suffices)
::      https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/

:: Ensure `_gitshort` contains the short commit SHA for inclusion in LaTeX (see inc/intro.tex).
:: If `git` isn't available or fails, write 'unknown' as a fallback.
git rev-parse --short HEAD > _gitshort 2>nul
if %errorlevel% neq 0 (
	echo unknown > _gitshort
)

:: run lilybook_maker - it will detect the LyTeX-File and build the book
:: all parameters given to this script are forwarded
lilybook.cmd --include=scores,inc %*

:: keep this CMD open
pause
