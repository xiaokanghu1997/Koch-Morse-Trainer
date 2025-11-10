@echo off
echo =============================================
echo   Koch Morse Trainer Installer Build Script
echo =============================================
echo.

echo [1/3] Using PyInstaller to package Koch.py...
pyinstaller --onefile --windowed --icon=Installer\logo.ico --name="Koch" Koch.py
if %errorlevel% neq 0 (
    echo Error: Koch packaging failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Using PyInstaller to package Create_Koch_Morse_Training_Materials.py...
pyinstaller --onefile --console --icon=Installer\logo.ico --name="Create Koch Morse Training Materials" Create_Koch_Morse_Training_Materials.py
if %errorlevel% neq 0 (
    echo Error: Create_Koch_Morse_Training_Materials packaging failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Using Inno Setup to create the installer...
"D:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer\setup.iss
if %errorlevel% neq 0 (
    echo Error: Installer creation failed!
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Build completed!
echo   Installer location: Build\Koch_Setup_v1.0.0.exe
echo ===================================================
pause