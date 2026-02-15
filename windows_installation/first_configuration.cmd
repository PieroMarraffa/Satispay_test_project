@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
REM Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Project root = parent directory of script dir
for %%I in ("%SCRIPT_DIR%\..") do set PROJECT_ROOT=%%~fI

set REQ_FILE=%SCRIPT_DIR%\requirements.txt
set PY_SCRIPT=%SCRIPT_DIR%\first_configuration_win.py
set VENV_DIR=%PROJECT_ROOT%\.venv

REM ----------------------------------------
REM Find Python command
REM ----------------------------------------

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set PYTHON=python
    goto :python_found
)

where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
    set PYTHON=python3
    goto :python_found
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set PYTHON=py -3
    goto :python_found
)

echo ❌ Python not found. Install Python 3: https://www.python.org/downloads/
exit /b 1

:python_found
echo ℹ️  Using Python: %PYTHON%

REM ----------------------------------------
REM Create venv if missing
REM ----------------------------------------

if not exist "%VENV_DIR%" (
    echo ℹ️  Creating virtualenv at %VENV_DIR%
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment.
        exit /b 1
    )
)

REM ----------------------------------------
REM Detect venv python
REM ----------------------------------------

if exist "%VENV_DIR%\Scripts\python.exe" (
    set VENV_PY=%VENV_DIR%\Scripts\python.exe
) else (
    echo ❌ Could not find venv python interpreter.
    exit /b 1
)

REM ----------------------------------------
REM Install dependencies
REM ----------------------------------------

echo ℹ️  Installing dependencies from %REQ_FILE% into venv
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo ❌ Failed to install dependencies.
    exit /b 1
)

echo ✅ Dependencies installed.

REM ----------------------------------------
REM Run python script
REM ----------------------------------------

echo ℹ️  Running: %PY_SCRIPT%
"%VENV_PY%" "%PY_SCRIPT%"
if errorlevel 1 (
    echo ❌ Script execution failed.
    exit /b 1
)

echo ✅ Script completed successfully.
exit /b 0