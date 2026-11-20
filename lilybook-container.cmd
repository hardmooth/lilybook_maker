:: lilybook-container.cmd - runs lilybook inside a container from a Windows CMD/Explorer.
::
:: usage (inside a book directory):
::   lilybook-container [target ...]              e.g. lilybook-container booklet
::   lilybook-container --rebuild [target ...]    rebuild the image first (after a git pull)
::
:: Setup (once):
::   1. install Podman Desktop (or Docker Desktop) and start it
::   2. put the directory containing this file on the Windows PATH (User Path suffices)
::
:: Set LILYBOOK_ENGINE=docker to use docker instead of podman.
:: The image is built from the Containerfile next to this file on the first run.
@echo off
setlocal
if "%LILYBOOK_ENGINE%"=="" set LILYBOOK_ENGINE=podman
if "%LILYBOOK_IMAGE%"=="" set LILYBOOK_IMAGE=lilybook

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
