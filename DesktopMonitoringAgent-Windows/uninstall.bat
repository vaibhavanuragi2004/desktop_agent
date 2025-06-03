@echo off
echo Uninstalling Desktop Monitoring Agent...

rem Stop the process
taskkill /f /im "DesktopMonitoringAgent.exe" 2>nul

rem Remove from startup
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "DesktopMonitoringAgent" /f 2>nul

rem Remove installation directory
set INSTALL_DIR=%ProgramFiles%\Desktop Monitoring Agent
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Uninstallation complete!
pause
