@echo off
chcp 65001 >nul
python "%~dp0easyrpg_web_gui.py"
rem close the terminal on normal exit; pause only when python exits with an error
if errorlevel 1 pause
