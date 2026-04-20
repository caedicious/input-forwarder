@echo off
REM Build standalone .exe files with PyInstaller.
REM Untested — may need --hidden-import flags for pynput/pystray.

pyinstaller --noconfirm --onefile --noconsole --name InputForwarderSender sender.pyw
pyinstaller --noconfirm --onefile --noconsole --name InputForwarderReceiver receiver.pyw

echo.
echo Done. Binaries in dist\
