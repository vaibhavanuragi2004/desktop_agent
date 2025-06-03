@echo off
REM Windows Packaging Script for Desktop Monitoring Agent
REM This script creates an .exe file for Windows distribution

echo === Windows Packaging Script ===
echo Building Desktop Monitoring Agent for Windows

REM Configuration
set APP_NAME=DesktopMonitoringAgent
set VERSION=2.0.0
set EXE_NAME=%APP_NAME%-%VERSION%.exe

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec
if exist %EXE_NAME% del %EXE_NAME%

REM Install dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements_agent.txt
python -m pip install pyinstaller pywin32

REM Build the executable
echo Building executable with PyInstaller...
pyinstaller --onefile ^
    --noconsole ^
    --name %APP_NAME% ^
    --add-data "windows_service.py;." ^
    --hidden-import "pynput.keyboard._win32" ^
    --hidden-import "pynput.mouse._win32" ^
    --hidden-import "win32serviceutil" ^
    --hidden-import "win32service" ^
    --hidden-import "win32event" ^
    --icon "agent_icon.ico" ^
    desktop_agent.py

REM Check if build was successful
if not exist "dist\%APP_NAME%.exe" (
    echo Error: Build failed - executable not found
    exit /b 1
)

REM Copy executable to final name
copy "dist\%APP_NAME%.exe" "%EXE_NAME%"

REM Create service installer batch file
echo Creating service installer...
(
echo @echo off
echo REM Service Installer for Desktop Monitoring Agent
echo.
echo echo Installing Desktop Monitoring Agent as Windows Service...
echo.
echo REM Check for admin privileges
echo net session ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Administrator privileges required
echo     echo Please run this installer as Administrator
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Install the service
echo "%~dp0%APP_NAME%.exe" --install
echo if errorlevel 1 ^(
echo     echo Service installation failed
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Start the service
echo sc start %APP_NAME%
echo if errorlevel 1 ^(
echo     echo Warning: Service start failed - you may need to start it manually
echo ^)
echo.
echo echo Service installed successfully!
echo echo The agent will now start automatically with Windows.
echo pause
) > install_service.bat

REM Create service uninstaller batch file
echo Creating service uninstaller...
(
echo @echo off
echo REM Service Uninstaller for Desktop Monitoring Agent
echo.
echo echo Uninstalling Desktop Monitoring Agent Service...
echo.
echo REM Check for admin privileges
echo net session ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo Error: Administrator privileges required
echo     echo Please run this uninstaller as Administrator
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Stop the service
echo sc stop %APP_NAME%
echo.
echo REM Uninstall the service
echo "%~dp0%APP_NAME%.exe" --remove
echo if errorlevel 1 ^(
echo     echo Service removal failed
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Service uninstalled successfully!
echo pause
) > uninstall_service.bat

REM Create README file
echo Creating README...
(
echo Desktop Monitoring Agent v%VERSION%
echo.
echo Installation Instructions:
echo 1. Copy %APP_NAME%.exe to a permanent location ^(e.g., C:\Program Files\%APP_NAME%\^)
echo 2. Run install_service.bat as Administrator to install as a Windows service
echo 3. The agent will start automatically and prompt for initial setup
echo.
echo Manual Installation:
echo 1. Simply run %APP_NAME%.exe
echo 2. Follow the setup wizard to pair with your monitoring server
echo.
echo Service Management:
echo - To install service: run install_service.bat as Administrator
echo - To uninstall service: run uninstall_service.bat as Administrator
echo - To start service manually: sc start %APP_NAME%
echo - To stop service manually: sc stop %APP_NAME%
echo.
echo Files included:
echo - %APP_NAME%.exe - Main application
echo - install_service.bat - Service installer
echo - uninstall_service.bat - Service uninstaller
echo - README.txt - This file
echo.
echo Support: contact your system administrator
) > README.txt

REM Create installer package directory
echo Creating installer package...
set PACKAGE_DIR=%APP_NAME%-%VERSION%-Windows
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%

REM Copy files to package directory
copy %EXE_NAME% %PACKAGE_DIR%\%APP_NAME%.exe
copy install_service.bat %PACKAGE_DIR%\
copy uninstall_service.bat %PACKAGE_DIR%\
copy README.txt %PACKAGE_DIR%\

REM Create zip file if 7-Zip is available
where 7z >nul 2>&1
if %errorlevel% equ 0 (
    echo Creating ZIP archive...
    7z a -tzip %PACKAGE_DIR%.zip %PACKAGE_DIR%\*
    echo ZIP archive created: %PACKAGE_DIR%.zip
) else (
    echo 7-Zip not found - ZIP archive not created
    echo Package directory created: %PACKAGE_DIR%\
)

REM Clean up build artifacts
rmdir /s /q build
rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo === Build Complete ===
echo Executable created: %EXE_NAME%
echo Package directory: %PACKAGE_DIR%\
echo.
echo Distribution files:
if exist %PACKAGE_DIR%.zip (
    echo   - %PACKAGE_DIR%.zip ^(for distribution^)
)
echo   - %PACKAGE_DIR%\ ^(installer package^)
echo   - %EXE_NAME% ^(standalone executable^)
echo.
echo Installation:
echo   1. Extract/copy files to target system
echo   2. Run install_service.bat as Administrator
echo   3. Follow setup instructions when prompted
echo.
pause
