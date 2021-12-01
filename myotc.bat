@echo off
set myotc=%~dp0%myotc.py
call %~dp0%vars.bat
python %myotc% %*

