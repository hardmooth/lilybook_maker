:: This script tries 
:: 
:: usage
::   1. 
::  
:: 
:: Setup:
::   1. clone this source folder
::   2. add the older to PATH variable (User Path suffices)
::      https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/
::   3. if you want, create a shortcut of this CMD in your book folder


:: simply run the python PDF builder (it will detect your LyTeX-File and build the book)
:: forward all parameters given to this CMD to the python PDF builder: %*
python %~dp0\create_pdf.py %*

:: uncomment the following line to keep CMD open
pause
