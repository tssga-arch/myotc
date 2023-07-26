@echo off
setlocal
set kurotc=%~dp0\dist\kurotc.exe
call %~dp0%cfg.bat
%kurotc% encode -i


