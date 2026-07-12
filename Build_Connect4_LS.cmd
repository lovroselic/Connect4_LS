@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "ANACONDA_ROOT=%USERPROFILE%\anaconda3"
set "ACTIVATE_BAT=%ANACONDA_ROOT%\Scripts\activate.bat"

cd /d "%PROJECT_ROOT%"

echo.
echo ============================================
echo  Connect4_LS release build launcher
echo ============================================
echo Project: %PROJECT_ROOT%
echo.

if not exist "%ACTIVATE_BAT%" (
    echo ERROR: Anaconda activation script was not found:
    echo   %ACTIVATE_BAT%
    echo.
    pause
    exit /b 1
)

call "%ACTIVATE_BAT%" Connect4_LS

if errorlevel 1 (
    echo.
    echo ERROR: Could not activate Conda environment Connect4_LS.
    echo.
    pause
    exit /b 1
)

echo Active Python:
where python
python --version
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%build_release.ps1"

set "BUILD_EXIT_CODE=%ERRORLEVEL%"

echo.
if "%BUILD_EXIT_CODE%"=="0" (
    echo Build completed successfully.
) else (
    echo Build failed with exit code %BUILD_EXIT_CODE%.
)

echo.
pause
exit /b %BUILD_EXIT_CODE%
