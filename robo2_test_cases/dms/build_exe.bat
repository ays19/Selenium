@echo off
setlocal
pushd "%~dp0"
echo ========================================================
echo Building Robo2mation Test Runner Standalone Windows App
echo ========================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
) else if exist "%~dp0..\..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\..\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" -u "%~dp0build_exe.py"
popd
pause