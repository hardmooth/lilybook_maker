# lilybook_maker

Lilybook maker will create a songbook PDF(s) from Lilypond and LaTeX.
It is mainly developed to run on Windows, but might also run on other OS.

# Usage

## Setup/Prerequisites

* install 
    * LaTeX - for Windows that's via https://miktex.org/download
    * Lilypond - http://lilypond.org/download.de.html
    * python (I am currently working with version 3.6) - https://www.python.org/downloads/
    * git (either of the following)
        * at least command line git: https://git-scm.com/download/win
        * easier access via TortoiseGit: https://tortoisegit.org/download/

* clone this repository (e.g. as submodule of your book files)
  1. get a github account
  1. request access to this repo
  1. setup git credentials manager (for windows)
    1. install https://github.com/microsoft/Git-Credential-Manager-Core
    1. activate credentials manager as of https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage

           git config --global credential.helper cache

  1. git clone https://github.com/hardmooth/lilybook_maker.git

* you can run a check whether the lilybook_maker finds everything:

      python setup.py --check

* to store your credentials you can setup an SSH key
  see https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/connecting-to-github-with-ssh
  if you're using TortoiseGit, also follow https://medium.com/chaya-thilakumara/tortoisegit-how-to-create-and-upload-your-public-key-to-github-884b7b619329

## creating a PDF

1. run from CMD/bash (inside your book directory, next to <your_book_main_file.lytex>:

       python lilybook_maker/create_pdf.py <lytex_file_optional.lytex>

1. during run accept latex updates (e.g. from MikTeX)
1. you should now have a newly created PDF
