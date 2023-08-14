@echo off
setlocal
call %~dp0%..\vars.bat
python %~dp0\findsitepkgs.py > %~dp0\sitedir.bat
call %~dp0\sitedir.bat
echo SITEDIR:%sitedir%
del %~dp0\sitedir.bat
REM ~ set sitedir=%WINPYDIR%\Lib\site-packages
set buildtype=--onefile
rem
rem Usage:
rem mk.bat (opts)
rem 
rem Options:
rem
rem * -1 : generate a single EXE file
rem * -d : generage a single DIR
rem * --openstack : OpenStack predefines

set line=
set BUILD_OPTS=
:loop
REM this loop does NOT handle double quotes "
if NOT "%1" =="" (
  IF "%1"=="-1" (
    SET buildtype=--onefile
    SHIFT
    goto :loop
  )
  IF "%1"=="-d" (
    SET buildtype=--onedir
    SHIFT
    goto :loop
  )
  IF "%1"=="-d" (
    SET buildtype=--onedir
    SHIFT
    goto :loop
  )
  IF "%1"=="--openstack" (
    set BUILD_OPTS=^
      --hidden-import keystoneauth1 ^
      --collect-data keystoneauth1 ^
      --copy-metadata keystoneauth1 ^
      --hidden-import os_service_types ^
      --collect-data os_service_types ^
      --copy-metadata os_service_types ^
      --collect-all openstacksdk ^
      --copy-metadata openstacksdk ^
      --hidden-import keystoneauth1.loading._plugins ^
      --hidden-import keystoneauth1.loading._plugins.identity ^
      --hidden-import keystoneauth1.loading._plugins.identity.generic ^
      --hidden-import dogpile.cache.backends ^
      --hidden-import dogpile.cache.backends.memory ^
      --hidden-import dogpile.cache.backends.null ^
      --hidden-import dogpile.cache.backends.file ^
      --add-data %sitedir%\openstack\config\defaults.json;openstack\config ^
      --add-data %sitedir%\openstack\config\vendors\otc.json;openstack\config\vendors ^
      --add-data %sitedir%\os_service_types\data\service-types.json;os_service_types\data

    SHIFT
    goto :loop
  )
  set line=%line% %1
  SHIFT
  goto :loop
)

echo BUILD:%buildtype%
echo OPTS:%BUILD_OPTS%
echo ARGS:%line%
pyinstaller %buildtype% %BUILD_OPTS% %line%
REM ~ type %sitedir%\openstack\config\defaults.json
REM ~ goto :DONE
REM ~ rd/s/q %~dp0%build
REM ~ rd/s/q %~dp0%dist
REM ~ set build=%~dp0%..\build
REM ~ set dist=%~dp0%..\dist


REM ~ @echo on

REM ~ echo OPTS:%UROTC_OPTS%

  REM ~ urotc.py
REM ~ @echo off
REM ~ --hidden-import MODULENAME, --hiddenimport MODULENAME
REM ~ --collect-submodules MODULENAME
REM ~ --collect-data MODULENAME, --collect-datas MODULENAME
REM ~ --collect-binaries MODULENAME
REM ~ --collect-all MODULENAME
REM ~ --copy-metadata PACKAGENAME
REM ~ --recursive-copy-metadata PACKAGENAME

REM ~ --hidden-import=pytorch
REM ~ --collect-data torch
REM ~ --copy-metadata torch
REM ~ --copy-metadata tqdm
REM ~ --copy-metadata regex
REM ~ --copy-metadata sacremoses
REM ~ --copy-metadata requests
REM ~ --copy-metadata packaging
REM ~ --copy-metadata filelock
REM ~ --copy-metadata numpy
REM ~ --copy-metadata tokenizers
REM ~ --copy-metadata importlib_metadata
REM ~ --hidden-import="sklearn.utils._cython_blas"
REM ~ --hidden-import="sklearn.neighbors.typedefs"
REM ~ --hidden-import="sklearn.neighbors.quad_tree"
REM ~ --hidden-import="sklearn.tree"
REM ~ --hidden-import="sklearn.tree._utils"

:DONE
