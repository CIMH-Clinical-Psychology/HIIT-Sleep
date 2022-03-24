:: Check for Python Installation
echo off
python --version 2>NUL
if errorlevel 1 goto errorNoPython


echo "starting spindle analysis"
python spindle_analysis_GUI.py
pause


:: Once done, exit the batch file -- skips executing the errorNoPython section
goto:eof

:errorNoPython
echo.
echo Error^: Python not installed or environment not activated. Make sure to run this command in your anaconda shell.
pause