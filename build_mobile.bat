@echo off
setlocal
REM Build mobile Flask service executable (Windows)

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

REM Install Playwright browsers for the build environment
python -m playwright install chromium
python -m playwright install-deps chromium

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build the executable
pyinstaller --clean --noconfirm mobile_app.spec

REM Copy additional required files to the dist directory
if exist dist\VFS-Mobile (
    REM Create data directories
    mkdir "dist\VFS-Mobile\info" 2>nul
    mkdir "dist\VFS-Mobile\documents" 2>nul
    mkdir "dist\VFS-Mobile\logs" 2>nul
    
    REM Copy initial data files if they exist
    if exist clients.csv copy clients.csv "dist\VFS-Mobile\"
    if exist proxies.txt copy proxies.txt "dist\VFS-Mobile\"
    if exist config.py copy config.py "dist\VFS-Mobile\"
)

echo.
echo Build complete. Executable is under dist\VFS-Mobile\VFS-Mobile.exe
echo.
echo Note: The first run may take longer as Playwright downloads browser binaries.
endlocal


