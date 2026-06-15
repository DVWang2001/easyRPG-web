@echo off
chcp 65001 >/dev/null
python "%~dp0easyrpg_web_build.py" %*
pause
