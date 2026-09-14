:: lilybook.cmd - runs lilybook inside WSL from a Windows CMD/Explorer.
::
:: usage (inside a book directory): lilybook [target ...]     e.g. lilybook booklet
::
:: Setup (once):
::   1. install WSL with Ubuntu:            wsl --install
::   2. inside WSL install the tools:       sudo apt install make lilypond latexmk texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-german
::   3. inside WSL clone lilybook_maker and add it to the PATH in ~/.bashrc:
::        export PATH="$PATH:$HOME/lilybook_maker"
::   4. put the directory containing this lilybook.cmd on the Windows PATH (User Path suffices)
::
:: WSL maps the current Windows directory automatically (c:\books\x -> /mnt/c/books/x).
@echo off
wsl bash -lc "lilybook %*"
