@echo off
setlocal
set urotc=%~dp0\dist\urotc.exe
call %~dp0%cfg.bat
%urotc% %*

