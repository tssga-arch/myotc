@echo off

if NOT "%PKGVER%" == "" goto :DONE

  rem Desired Python version...
  rem https://github.com/winpython/winpython/releases/tag/4.3.20210620
  rem Tested with v3.8
  rem Failed with v3.9
  rem
  set PKGVER=64-38100
  rem
  rem Install to possible locations:
  rem
  rem C:\WPy%PKGVER%
  rem C:\bin\WPy%PKGVER%
  rem %USERPROFILE%\C\WPy%PKGVER%
  rem %~dp0%\WPy%PKGVER%
  rem

  set ENVBAT=scripts\env.bat
  set SDIR=%~dp0

  if NOT EXIST C:\WPy%PKGVER%\%ENVBAT% goto :ls1p1
    set WPYDIR=C:\WPy%PKGVER%
    goto :ls1end
  :ls1p1
  if NOT EXIST C:\bin\WPy%PKGVER%\%ENVBAT% goto :ls1p2
    set WPYDIR=C:\bin\WPy%PKGVER%
    goto :ls1end
  :ls1p2
  if NOT EXIST %USERPROFILE%\C\WPy%PKGVER%\%ENVBAT% goto :ls1p3
    set WPYDIR=%USERPROFILE%\C\WPy%PKGVER%
    goto :ls1end
  :ls1p3
  if NOT EXIST %SDIR%WPy%PKGVER%\%ENVBAT% goto :ls1p4
    set WPYDIR=%SDIR%WPy%PKGVER%
    goto :ls1end
  :ls1p4
    echo No Suitable WinPython Installation found
    set PKGVER=
    goto :DONE
  :ls1end

  REM Note, this modifies HOME variable to %WPYDIR%\settings
  call %WPYDIR%\%ENVBAT%

:DONE

set proxy=10.41.5.36:8080
REM ~ set proxy=sia-lb.telekom.de:8080
set http_proxy=http://%proxy%/
set https_proxy=http://%proxy%/
set MYOTC_OPTS=
REM ~ set proxy=
REM ~ set http_proxy=
REM ~ set https_proxy=
REM ~ set MYOTC_OPTS=-A

set ENVBAT=
set SDIR=
