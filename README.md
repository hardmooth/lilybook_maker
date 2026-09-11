# lilybook_maker

Lilybook maker will create a songbook PDF(s) from Lilypond and LaTeX.
It was originally developed on Windows and also runs on Linux (tested with Ubuntu, TeX Live, LilyPond 2.24).

It is developed in bundle with https://github.com/hardmooth/lilybook_template - simply fork this to get your own songbook started.

# Usage

## Setup/Prerequisites (Windows)

* install tools
    * LaTeX - for Windows that's via https://miktex.org/download
    * Lilypond - http://lilypond.org/download.de.html
    * python (I am currently working with version 3.6) - https://www.python.org/downloads/
    * git (either of the following)
        * at least command line git: https://git-scm.com/download/win
        * easier access via TortoiseGit: https://tortoisegit.org/download/
* clone this repository / setup github connection
  1. get a github account
  1. request access to this repo
  1. setup git credentials manager (for windows)
    1. install https://github.com/microsoft/Git-Credential-Manager-Core
    1. activate credentials manager as of https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage

           git config --global credential.helper cache

  1. git clone https://github.com/hardmooth/lilybook_maker.git (I suggest to clone it once and add
  1. create initial configuration:
  
      python setup.py --init

* you can run a check whether the lilybook_maker finds everything (CMD inside the lilybook_maker):

      python setup.py --check

* to store your credentials you can setup an SSH key (if you want to contribute or have future updates)
  see https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/connecting-to-github-with-ssh
  if you're using TortoiseGit, also follow https://medium.com/chaya-thilakumara/tortoisegit-how-to-create-and-upload-your-public-key-to-github-884b7b619329

## Setup/Prerequisites (Linux)

* install tools (Debian/Ubuntu):

      sudo apt install lilypond texlive-latex-base texlive-latex-recommended texlive-latex-extra \
                       texlive-fonts-recommended texlive-fonts-extra texlive-lang-german python3-venv git

  (`texlive-latex-extra`/`texlive-fonts-extra`/`texlive-lang-german` are needed by the packages used in
  the lilybook_template preamble: koma-script, pdfpages, libertine, marvosym, framed, wrapfig, german, ...)
* clone this repository and install the python requirements into a virtual environment
  (`lilybook.sh` picks up `.venv` next to it automatically):

      git clone https://github.com/hardmooth/lilybook_maker.git
      cd lilybook_maker
      python3 -m venv .venv && .venv/bin/pip install -r requirements_py.txt

  alternatively install them system wide (`python3 -m pip install -r requirements_py.txt`) or point
  `LILYBOOK_PYTHON` to an interpreter that has them.
* optionally add the lilybook_maker directory to your `PATH` (e.g. in `~/.bashrc`), so `lilybook.sh`
  and the songbook's `build.sh` find it
* check whether lilybook_maker finds everything:

      ./lilybook.sh --check

  `python setup.py --init` writes a `config.ini` (lilypond directory and pdflatex command). Without it,
  the lilypond/pdflatex found in `PATH` are used, which is usually what you want on Linux.

Differences to Windows: on Linux `pdflatex` is run directly (TeX Live has no `texify`), so
`create_pdf.py` reruns it until table of contents/references are stable and calls `makeindex` itself.
Include directories are passed via `TEXINPUTS` instead of MiKTeX's `--include-directory`.

## creating a PDF

1. either of the following:
    * run from CMD/bash (inside your book directory, next to <your_book_main_file.lytex>:

          python lilybook_maker/create_pdf.py <lytex_file_optional.lytex>
         
    * use the build.cmd inside the songbook (if derived from lilybook_template)
1. during run accept latex updates (e.g. from MikTeX)
1. you should now have a newly created PDF

## options

    --include=scores,inc   include directories for lilypond-book and LaTeX (default: inc, scores, current dir)
    --full                 delete the out/ directory before building
    --booklet              additionally write <book>-booklet.pdf (2 pages per sheet in booklet order,
                           e.g. A5 book -> A4 landscape sheets; print duplex, flip on short edge, fold, staple)
    --strict               abort on the first error
    --check                only check prerequisites

Booklets/2-on-1 can also be created separately with `pdf_transform.py --help`.

## running the tests

    python -m pip install -r requirements_dev.txt   # or: .venv/bin/pip install -r requirements_dev.txt
    python -m pytest

The integration tests build the minimal example book in `tests/data/minimal_book` and are skipped
if lilypond, lilypond-book or pdflatex are not installed.

`tests/test_books.py` additionally builds real books with every command line option
(see issue #4): by default the sibling directories `../lilybook_template` and
`../liederbuch_advent_weihnachten` of this checkout, if they exist. Other books can be given via the
environment variable `LILYBOOK_BOOKS` (directories separated by `:`, on Windows `;`):

    LILYBOOK_BOOKS=/path/to/my_book:/path/to/other_book python -m pytest tests/test_books.py

A book is skipped (with the reason printed by `-ra`) if its directory or one of the LaTeX packages it
uses is missing. The GitHub Actions workflow (`.github/workflows/tests.yml`) runs all of this against
the lilybook_template repository on every push.
