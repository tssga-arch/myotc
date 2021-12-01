@echo off
call %~dp0%vars.bat

pip install --proxy=%proxy% --only-binary=cryptography,netifaces python-openstackclient
pip install --proxy=%proxy% otcextensions
