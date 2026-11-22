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
    lilybook scores/my_song.pdf    # a PDF for one score, built from scores/my_song.ly
    lilybook check      # checks tools, LaTeX packages, file encodings and runs the book's check.py
    lilybook full       # clean + pdf
    lilybook clean      # removes out/ and the generated PDFs
    lilybook help       # lists the targets and what was detected

Builds are incremental: unchanged scores are not recompiled. Changes in included Lilypond files
(`default.ly`, `LY-include.ly`, ...) discard the snippet cache automatically, since lilypond-book
would not notice them. Output also goes to `lilybook.log` in the book directory.

A single score is built by lilypond alone, without LaTeX. An invalid `.ly` file makes the build
fail: lilypond prints the error, the exit code is not 0 and no PDF is left behind.

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

    sudo apt install make lilypond latexmk fonts-freefont-ttf texlive-latex-base texlive-latex-recommended \
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

## Container (podman or docker)

The container image holds the complete toolchain. The host needs neither lilypond nor LaTeX nor
make. It needs podman or docker, which you have to set up once, before the first build.

### Set up podman or docker (once)

Linux (Debian/Ubuntu):

    sudo apt install podman

Windows:

1. Enable hardware virtualization in the BIOS/UEFI (Intel VT-x or AMD-V), if it is off.
2. Install WSL 2. Run `wsl --install` in an administrator CMD and reboot.
3. Install Podman (https://podman.io) or Podman Desktop. When the installer asks for the
   virtualization provider, choose **WSL**. Hyper-V needs Windows Pro or Enterprise and
   administrator rights. kubectl and Compose are not needed.
4. Create and start the Podman machine. Podman Desktop offers this on its first start. On the
   command line it is `podman machine init`, then `podman machine start`.
5. Put the lilybook_maker checkout on the Windows `PATH`, so that `lilybook-container.cmd` is found.

Docker Desktop works instead of podman. Set `LILYBOOK_ENGINE=docker` in that case.

On both systems, check the engine before the first build:

    podman run --rm docker.io/library/hello-world

It must print a greeting. On Windows the Podman machine has to be running for every build. After a
reboot start it again with `podman machine start` or through Podman Desktop. A stopped machine
shows as the error `Cannot connect to Podman`.

### Build a book

`lilybook-container` takes the same targets and variables as `lilybook`. Run it inside a book
directory, on Windows from CMD or PowerShell:

    lilybook-container                # builds <book>.pdf
    lilybook-container booklet
    lilybook-container scores/my_song.pdf    # one score
    lilybook-container --rebuild      # rebuilds the image first, e.g. after a git pull
    lilybook-container --help         # lists all targets, variables and options

The first run builds the image `lilybook` from the `Containerfile`. The image installs TeX Live
including `texlive-fonts-extra`, so that build downloads several gigabytes.

The wrapper mounts the current directory as `/book` and runs `lilybook` there. On Linux the
generated files belong to the calling user.

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

`tests/test_container.py` exercises `lilybook-container` on the minimal book. These tests need podman
or docker, but neither lilypond nor LaTeX on the host. They rebuild the image once per run.

    .venv/bin/python -m pytest -m container           # only the container tests
    .venv/bin/python -m pytest -m "not container"     # everything else

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
(up to commit `758f1e7`).
