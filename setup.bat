@echo off
setlocal
call %~dp0%vars.bat

if "%proxy%"=="" (
  set proxy=
) else (
  set proxy=--proxy=%proxy%
)
pip install %proxy% --only-binary=cryptography,netifaces python-openstackclient
pip install %proxy% otcextensions
pip install %proxy% passlib
pip install %proxy% pyinstaller

