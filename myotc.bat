@echo off
setlocal
set myotc=%~dp0%src\myotc.py
call %~dp0%vars.bat
python %myotc% -I %~dp0\snippets %*

