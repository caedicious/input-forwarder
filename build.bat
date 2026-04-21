@echo off
setlocal enableextensions

REM ===========================================================================
REM Input Forwarder — full build script.
REM
REM  1. Freezes sender.pyw and receiver.pyw into standalone .exe files via
REM     PyInstaller (output: dist\).
REM  2. Invokes Inno Setup's ISCC.exe to compile a single user-facing
REM     installer (output: installer\Output\InputForwarderSetup.exe).
REM
REM Prerequisites (install once on the build machine):
REM   - Python 3.10+ with pip on PATH
REM   - pip install -r requirements.txt
REM   - pip install pyinstaller
REM   - Inno Setup 6  (https://jrsoftware.org/isdl.php)
REM
REM See BUILDING.md for details.
REM ===========================================================================

pushd "%~dp0"

echo.
echo === [1/3] Cleaning previous build artifacts ===
if exist build   rmdir /S /Q build
if exist dist    rmdir /S /Q dist
if exist "installer\Output" rmdir /S /Q "installer\Output"
del /Q *.spec 2>nul

echo.
echo === [2/3] Building .exe files with PyInstaller ===

pyinstaller --noconfirm --onefile --windowed ^
    --name InputForwarderSender ^
    --collect-submodules pynput ^
    --collect-submodules pystray ^
    --collect-submodules PIL ^
    sender.pyw
if errorlevel 1 goto :error

pyinstaller --noconfirm --onefile --windowed ^
    --name InputForwarderReceiver ^
    receiver.pyw
if errorlevel 1 goto :error

echo.
echo === [3/3] Compiling installer with Inno Setup ===

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"      set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo.
    echo [WARN] Inno Setup 6 not found. Install from https://jrsoftware.org/isdl.php
    echo        The .exe files are in dist\ but no installer was built.
    goto :end
)

"%ISCC%" "installer\InputForwarder.iss"
if errorlevel 1 goto :error

echo.
echo =====================================================================
echo  Build complete.
echo   Installer: installer\Output\InputForwarderSetup.exe
echo   Raw exes:  dist\InputForwarderSender.exe, dist\InputForwarderReceiver.exe
echo =====================================================================
goto :end

:error
echo.
echo [ERROR] Build failed. See messages above.
popd
exit /b 1

:end
popd
endlocal
