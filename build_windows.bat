@echo off
REM ===================================================
REM Build MultiLLM-Chat for Windows
REM ===================================================

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo pip install failed.
    pause
    exit /b 1
)

echo Building executable with PyInstaller...
pyinstaller --onefile --windowed ^
    --name "MultiLLM-Chat" ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    --manifest assets\app.manifest ^
    --noconfirm ^
    --clean ^
    main.py

if %errorlevel% neq 0 (
    echo PyInstaller build failed.
    pause
    exit /b 1
)

if not exist installer mkdir installer
copy /Y dist\MultiLLM-Chat.exe installer\

echo Done! Executable at installer\MultiLLM-Chat.exe
pause
