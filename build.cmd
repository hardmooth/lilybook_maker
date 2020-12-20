:: Songbook builder
::
:: This builds the songbook, assuming you have lilybook_maker installed:
::  https://github.com/hardmooth/lilybook_maker
:: 
:: usage (inside a songbook directory):
::   double click on this script (or run it in CMD)
:: 
:: Setup:
::   1. clone the lilybook_maker
::   2. add lilybook_maker to PATH variable (User Path suffices)
::      https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/
::   3. fork the lilybook_template
::   4. copy this build.cmd to your songbook directory

:: simply run lilybook_maker (it will detect your LyTeX-File and build the book)
lilybook.cmd

:: keep this CMD open
pause
