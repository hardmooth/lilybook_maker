:: lilybook-container.cmd - runs lilybook inside a container from a Windows CMD/Explorer.
::
:: usage (inside a book directory):
::   lilybook-container [target ...]              e.g. lilybook-container booklet
::   lilybook-container scores/my_song.pdf        build one song from scores/my_song.ly
::   lilybook-container --rebuild [target ...]    rebuild the image first (after a git pull)
::   lilybook-container --help                    list all targets, variables and options
::
:: A single song is built by lilypond alone, as a PDF next to its .ly file. An invalid .ly file makes
:: the build fail: lilypond prints the error, the exit code is not 0 and no PDF is left behind.
::
:: Setup (once, see "Container" in README.md for the details):
::   1. enable hardware virtualization in the BIOS/UEFI and install WSL 2 (wsl --install)
::   2. install Podman or Podman Desktop and choose WSL as the virtualization provider
::   3. create and start the Podman machine:  podman machine init   then   podman machine start
::   4. put the directory containing this file on the Windows PATH (User Path suffices)
:: The Podman machine has to be running for every build.
::
:: Set LILYBOOK_ENGINE=docker to use docker instead of podman.
:: The image is built from the Containerfile next to this file on the first run.
@echo off
setlocal
if "%LILYBOOK_ENGINE%"=="" set LILYBOOK_ENGINE=podman
if "%LILYBOOK_IMAGE%"=="" set LILYBOOK_IMAGE=lilybook

if "%~1"=="--help" goto usage
if "%~1"=="-h" goto usage

set ARGS=%*
set REBUILD=0
:: %1 would split VARIABLE=value at the "=", so --rebuild is cut out of the complete argument string
if "%~1"=="--rebuild" (
    set REBUILD=1
    set ARGS=%ARGS:--rebuild=%
)

:run
if "%REBUILD%"=="1" goto build
%LILYBOOK_ENGINE% image inspect %LILYBOOK_IMAGE% >nul 2>nul
if not errorlevel 1 goto start
:build
%LILYBOOK_ENGINE% build -t %LILYBOOK_IMAGE% -f "%~dp0Containerfile" "%~dp0."
if errorlevel 1 exit /b 1
:start
%LILYBOOK_ENGINE% run --rm -v "%cd%":/book %LILYBOOK_IMAGE% %ARGS%
exit /b %errorlevel%

:: the target list repeats the "##" comments of lilybook.mk
:usage
echo usage: lilybook-container [--rebuild] [target ...] [VARIABLE=value ...]
echo.
echo Builds the book in the current directory inside a container (podman or docker).
echo.
echo options:
echo   --help, -h          show this help
echo   --rebuild           rebuild the container image first, e.g. after a git pull
echo.
echo targets:
echo   pdf                 build ^<book^>.pdf (default)
echo   booklet             build ^<book^>-booklet.pdf: 2 pages per sheet in booklet order (print duplex, flip on short edge)
echo   scores              build a PDF next to every single score
echo   full                clean and rebuild everything
echo   clean               remove out/ and the generated PDFs
echo   help                show the targets and what lilybook detects in the current directory
echo   check               check tools, LaTeX packages, encodings, check.py
echo   scores/^<song^>.pdf   build one score from scores/^<song^>.ly with lilypond alone
echo.
echo variables:
echo   STRICT=1            fail on LaTeX errors (default: keep going and list them)
echo   LYTEX=^<file^>        main file (default: the single *.lytex in the directory)
echo   INCLUDES="a b"      include directories (default: every directory with .ly or .tex files)
echo   OUT=^<dir^>           directory for intermediate files (default: out)
echo   BOOKLET_PAPER=^<p^>   sheet size of the booklet (default: a4paper)
echo.
echo environment:
echo   LILYBOOK_ENGINE     podman or docker (default: podman)
echo   LILYBOOK_IMAGE      image name (default: lilybook)
echo.
echo A book may define more targets in its own book.mk.
exit /b 0
