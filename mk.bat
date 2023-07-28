@echo off
rd/s/q %~dp0%build
rd/s/q %~dp0%dist
del *.spec
set build=%~dp0%scripts\build.bat
set py=%~dp0%py.bat
set prep=%~dp0%scripts\prep.py
set priv=%~dp0%scripts\priv.py
set kurotc=%~dp0%src\kurotc.py

call %build% -1 src\ypp.py
call %build% -1 src\hasher.py
call %py% %prep% %priv% src\kurotc.py
call %build% -1 --openstack src\kurotc.py
call %build% -1 --openstack src\myotc.py

REM ~ call %build% -1 --openstack src\urotc.py

