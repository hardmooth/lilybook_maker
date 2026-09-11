# Songbook template

This is a template for creating beautifully typed songbooks based on

  * Lilypond (scores)
  * LaTeX (book)

It is developed in bundle with https://github.com/hardmooth/lilybook_maker and mirrors the structure of
https://github.com/hardmooth/liederbuch_advent_weihnachten.
You can fork/copy this template to write your own songbook.

# Files and directories

| path                    | description                                                                       |
|-------------------------|-----------------------------------------------------------------------------------|
| document.lytex          | main book file (title page, table of contents, chapters, songs). Can be renamed.  |
| inc/                    | files included in the book: LaTeX preamble, intro text, logo                      |
| inc/tex-preambel.tex    | shared LaTeX preamble - packages, page geometry, header/footer, song macros       |
| inc/intro.tex           | preface / disclaimer, shows build date and git commit                             |
| inc/logo.svg, logo.pdf  | logo for the title page and the page header                                       |
| scores/                 | Lilypond score files, one song per file. File names without spaces.               |
| scores/default.ly       | common score layout (paper size, staff size, margins), included by every song     |
| scores/_template.ly     | template for a new song - copy and fill in                                        |
| scores/my_sample_song.ly| example song                                                                      |
| check.py                | book specific checks, run automatically by lilybook_maker before each build       |
| build.cmd / build.sh    | builds the book as document.pdf (Windows / Linux)                                 |
| build_full.cmd / .sh    | full rebuild, additionally writes document-booklet.pdf for printing               |
| out/                    | temporary folder, used by lilypond-book and LaTeX (not versioned)                 |
| document.pdf            | created PDF, A5 (after building, not versioned)                                   |
| document-booklet.pdf    | created booklet PDF, A4 landscape, 2 pages per sheet (after build_full)           |

# Building

## single score sheets

Single songs are LY-files in the `scores/` folder. Copy `scores/_template.ly` to start a new one.
Every song includes `default.ly`, so keep `\paper`/`\layout` blocks out of the songs.
You need Lilypond to transform them into a PDF - http://lilypond.org/download.de.html
They can be edited and built for example with the Frescobaldi sheet music editor - https://frescobaldi.org/download

Added songs have to be linked in `document.lytex`:

    \addcontentsline{toc}{section}{Song title}
    \lilypondfile{song_file.ly}

## the whole book

To build the whole book, you'll need either of the following:

* run lilypond-book and then LaTeX on `document.lytex` yourself, or
* use the lilybook_maker, which takes care of that:

      build.cmd          (Windows: double click)
      ./build.sh         (Linux)
      build_full.cmd / ./build_full.sh   (full rebuild + booklet for printing)

  All further options are forwarded to lilybook_maker, e.g. `./build.sh --strict`.

The result is `document.pdf` (or the errors are printed and written to `create_pdf.log`).

## Setup with lilybook_maker

This template and lilybook_maker are developed in bundle to ease the creation of the songbook PDF.

   1. install Lilypond, LaTeX and python (see the lilybook_maker README for your OS)
   2. clone https://github.com/hardmooth/lilybook_maker somewhere centrally
   3. add the cloned lilybook_maker folder to your PATH
      (Windows: https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/ ,
       Linux: `export PATH="$PATH:/path/to/lilybook_maker"` in `~/.bashrc`, or set `LILYBOOK_MAKER=/path/to/lilybook_maker`)
   4. fork/copy this template repository

      **WARNING**: Do not simply clone this template and work on it. You'll later havoc your songbook with git-pull.
   5. run `build.cmd` / `./build.sh` in the songbook folder to create a PDF
   6. write your songbook and build the PDF (see above)

## LaTeX packages

The preamble uses (Debian/Ubuntu package names): koma-script/pdfpages (`texlive-latex-recommended`),
framed, wrapfig, relsize, hyphenat, mathtools (`texlive-latex-extra`), libertine, marvosym
(`texlive-fonts-recommended`, `texlive-fonts-extra`) and german (`texlive-lang-german`).
On Windows MiKTeX installs missing packages on the fly.

# Printing

| file                  | format       | notes                                                                  |
|-----------------------|--------------|------------------------------------------------------------------------|
| document.pdf          | DIN A5       | for screen or A5 printing                                              |
| document-booklet.pdf  | DIN A4 quer  | 2 x A5 per sheet in booklet order: print duplex, flip on short edge, fold, staple |
| scores/*.pdf          | DIN A5       | single songs (have to be compiled with lilypond)                       |
