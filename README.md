# lilybook_maker

Lilybook maker will create a songbook PDF(s) from Lilypond and LaTeX.
It is mainly developed to run on Windows, but should 

# Usage

## Setup/Prerequisites

* clone this repository (e.g. as submodule of your book files)
  1. get a github account
  1. request access to this repo
  1. git clone https://github.com/hardmooth/lilybook_maker.git
* install LaTeX and Lilypond
* you can run a check whether the lilybook_maker finds everything:

    python setup.py --check

* to store your credentials you can setup an SSH key
  see https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/connecting-to-github-with-ssh

## creating a PDF

1. run from CMD/bash (inside your book directory, next to <your_book_main_file.lytex>:

    python lilybook_maker/create_pdf.py <lytex_file_optional.lytex>

1. during run accept latex updates (e.g. from MikTeX)
1. you should now have a newly created PDF
