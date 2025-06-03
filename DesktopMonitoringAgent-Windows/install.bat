@echo off
echo Installing Desktop Monitoring Agent for Windows...

rem Create installation directory
set INSTALL_DIR=%ProgramFiles%\Desktop Monitoring Agent
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

rem Copy executable
copy "DesktopMonitoringAgent.exe" "%INSTALL_DIR%\"

rem Add to Windows startup
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "DesktopMonitoringAgent" /t REG_SZ /d ""%INSTALL_DIR%\DesktopMonitoringAgent.exe"" /f

echo Installation complete! The agent will start automatically at login.
pause
