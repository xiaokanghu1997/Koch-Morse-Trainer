@echo off
echo =============================================
echo   Koch Morse Trainer Installer Build Script
echo =============================================
echo.

REM 切换到项目根目录（Installer的上一级）
cd /d "%~dp0.."

echo [1/4] Cleaning previous build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo Previous build artifacts cleaned.
echo.

echo [2/4] Using PyInstaller to package Koch.py...
pyinstaller --onefile ^
    --windowed ^
    --icon=Installer\logo.ico ^
    --name="Koch" ^
    --add-data="Logo;Logo" ^
    --add-data="Echarts;Echarts" ^
    --hidden-import=Statistics ^
    --hidden-import=Statistics_Window ^
    --hidden-import=Config ^
    Koch.py

if %errorlevel% neq 0 (
    echo Error: Koch packaging failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Using PyInstaller to package Create_Koch_Morse_Training_Materials.py...
pyinstaller --onefile ^
    --console ^
    --icon=Installer\logo.ico ^
    --name="Create Koch Morse Training Materials" ^
    --hidden-import=Config ^
    Create_Koch_Morse_Training_Materials.py

if %errorlevel% neq 0 (
    echo Error: Create_Koch_Morse_Training_Materials packaging failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Using Inno Setup to create the installer...
"D:\Program Files (x86)\Inno Setup 6\ISCC.exe" Installer\setup.iss
if %errorlevel% neq 0 (
    echo Error: Installer creation failed!
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Build completed!
echo   Installer location: Build\Koch_Setup_v1.2.6.exe
echo ===================================================
pause