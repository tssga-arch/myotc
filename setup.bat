@echo off
setlocal
call %~dp0%vars.bat

pip install --proxy=%proxy% --only-binary=cryptography,netifaces python-openstackclient
pip install --proxy=%proxy% otcextensions
pip install --proxy=%proxy% passlib
pip install --proxy=%proxy% pyinstaller

