@echo off
setlocal
set urotc=%~dp0\src\urotc.py
call %~dp0%vars.bat
call %~dp0%cfg.bat
python %urotc% %*

