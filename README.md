# lilybook_maker

Builds songbook PDFs from Lilypond scores and a LaTeX main file (`.lytex`, processed by lilypond-book).

One checkout of lilybook_maker builds any number of books. The books contain only their sources
(scores, texts, includes), all build logic lives here in `lilybook.mk`. A fix here is a `git pull`
away for every book.

Books built with it:
* https://github.com/hardmooth/lilybook_template - the template to start your own book from
* https://github.com/hardmooth/liederbuch_advent_weihnachten
* https://github.com/hardmooth/Kommersbuch_KSG_Chemnitz

# Usage

Inside a book directory (next to the `.lytex` file):

    lilybook            # builds <book>.pdf (same as: lilybook pdf)
    lilybook booklet    # additionally <book>-booklet.pdf: 2 pages per sheet in booklet order
                        #   (A5 book -> A4 landscape; print duplex, flip on short edge, fold, staple)
    lilybook scores     # a PDF next to every single score
    lilybook check      # checks tools, LaTeX packages, file encodings and runs the book's check.py
    lilybook full       # clean + pdf
    lilybook clean      # removes out/ and the generated PDFs
    lilybook help       # lists the targets and what was detected

Builds are incremental: unchanged scores are not recompiled. Changes in included Lilypond files
(`default.ly`, `LY-include.ly`, ...) discard the snippet cache automatically, since lilypond-book
would not notice them. Output also goes to `lilybook.log` in the book directory.

Options are make variables, e.g. `lilybook booklet STRICT=1`:

| variable   | default                                              | meaning                                         |
|------------|------------------------------------------------------|-------------------------------------------------|
| `LYTEX`    | the single `*.lytex` in the book directory           | main file                                       |
| `INCLUDES` | every top level directory with `.ly` or `.tex` files | include directories for lilypond-book and LaTeX |
| `OUT`      | `out`                                                | directory for snippets and LaTeX intermediates  |
| `STRICT`   | unset                                                | `STRICT=1`: fail on LaTeX errors (default: keep going and list them) |
| `BOOKLET_PAPER` | `a4paper`                                       | sheet size of the booklet                       |

A book that needs different settings permanently puts them into an optional `book.mk`
(e.g. `INCLUDES := scores texts inc`). Most books need none.

If the sources use `\input{_gitshort}` (see the template's `inc/intro.tex`), the short git commit of
the book is written to `_gitshort` before each build.

# Setup

## Linux (Debian/Ubuntu)

    sudo apt install make lilypond latexmk texlive-latex-base texlive-latex-recommended \
                     texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-german
    git clone https://github.com/hardmooth/lilybook_maker.git ~/lilybook_maker
    echo 'export PATH="$PATH:$HOME/lilybook_maker"' >> ~/.bashrc

`texlive-latex-base` plus `pdfpages` (in `texlive-latex-recommended`) is enough for a plain book;
the template's preamble needs the other packages (koma-script, libertine, marvosym, framed, ...).
`lilybook check` tells you what is missing.

## Windows

The build runs inside WSL (Windows Subsystem for Linux), which gives you the same toolchain as on
Linux. Frescobaldi, editors and PDF viewers stay on the Windows side and work on the same files.

1. `wsl --install` (Ubuntu), then inside WSL do the Linux setup above
2. put the lilybook_maker checkout (the Windows clone, or `\\wsl$\Ubuntu\home\<you>\lilybook_maker`)
   on the Windows `PATH`, so that `lilybook.cmd` is found
3. inside a book directory run `lilybook`, `lilybook booklet`, ... from CMD or PowerShell.
   `lilybook.cmd` forwards to `wsl bash -lc "lilybook ..."`; WSL maps the current directory itself.

Keeping the books inside the WSL file system (`~/books/...`) makes lilypond noticeably faster than
building on `/mnt/c/...`, but both work.

# Starting a new book

Fork https://github.com/hardmooth/lilybook_template. Its layout is what `lilybook` expects:

    document.lytex       main file: title page, table of contents, chapters, \lilypondfile{...} per song
    inc/                 LaTeX preamble, intro text, logo
    scores/              one .ly per song, all including scores/default.ly for the common layout
    check.py             optional book specific checks, run by `lilybook check` and before each build

# Running the tests

    python3 -m venv .venv && .venv/bin/pip install -r requirements_dev.txt
    .venv/bin/python -m pytest

`tests/test_lilybook.py` exercises every target and variable on the minimal book in
`tests/data/minimal_book`. `tests/test_books.py` builds real books: by default
`tests/data/template_book` (a snapshot of lilybook_template) and the sibling directories
`../lilybook_template`, `../liederbuch_advent_weihnachten` and `../Kommersbuch_KSG_Chemnitz` of this
checkout, if they exist. Other books can be given via `LILYBOOK_BOOKS` (directories separated by `:`):

    LILYBOOK_BOOKS=/path/to/my_book .venv/bin/python -m pytest tests/test_books.py

A book is skipped (with the reason shown by `-ra`) if its directory, the toolchain or one of its
LaTeX packages is missing. The GitHub Actions workflow (`.github/workflows/tests.yml`) runs
everything against the template snapshot on every push.

To refresh the snapshot from a lilybook_template checkout:

    rm -rf tests/data/template_book && mkdir tests/data/template_book
    (cd ../lilybook_template && git ls-files -z) | (cd ../lilybook_template && xargs -0 -I{} cp --parents {} "$OLDPWD/tests/data/template_book/")

# History

Up to 2026 lilybook_maker was a Python tool (`create_pdf.py`) with its own LaTeX rerun loop,
booklet generation via pypdf and Windows specific MiKTeX handling. It was replaced by this
Makefile on top of latexmk and pdfpages; the Python version is available in the git history
(branch `linux_compatibility`).
