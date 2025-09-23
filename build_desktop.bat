@echo off
setlocal
REM Build desktop GUI executable (Windows)

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
pyinstaller --clean --noconfirm app_main.spec

REM Copy additional required files to the dist directory
if exist dist\VFS-Desktop (
    REM Copy OpenCV cascade files if they exist
    if exist "C:\Program Files\Python*\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml" (
        copy "C:\Program Files\Python*\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml" "dist\VFS-Desktop\"
    )
    
    REM Create data directories
    mkdir "dist\VFS-Desktop\info" 2>nul
    mkdir "dist\VFS-Desktop\documents" 2>nul
    mkdir "dist\VFS-Desktop\logs" 2>nul
    
    REM Copy initial data files if they exist
    if exist clients.csv copy clients.csv "dist\VFS-Desktop\"
    if exist proxies.txt copy proxies.txt "dist\VFS-Desktop\"
    if exist config.py copy config.py "dist\VFS-Desktop\"
)

echo.
echo Build complete. Executable is under dist\VFS-Desktop\VFS-Desktop.exe
echo.
echo Note: The first run may take longer as Playwright downloads browser binaries.
endlocal


