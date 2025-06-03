#!/usr/bin/env python3
"""
Cross-platform service installer for Desktop Monitoring Agent
Handles installation as a system service on Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path

class ServiceInstaller:
    """Cross-platform service installer"""
    
    def __init__(self):
        self.system = platform.system()
        self.app_name = "DesktopMonitoringAgent"
        self.service_name = "desktop-monitoring-agent"
        self.bundle_id = "com.company.desktopagent"
        
        # Get executable path
        if getattr(sys, 'frozen', False):
            self.executable_path = sys.executable
        else:
            self.executable_path = os.path.abspath("desktop_agent.py")
    
    def install(self):
        """Install service for the current platform"""
        print(f"Installing Desktop Monitoring Agent service on {self.system}...")
        
        if self.system == "Windows":
            return self.install_windows_service()
        elif self.system == "Darwin":
            return self.install_macos_service()
        elif self.system == "Linux":
            return self.install_linux_service()
        else:
            print(f"Unsupported platform: {self.system}")
            return False
    
    def uninstall(self):
        """Uninstall service for the current platform"""
        print(f"Uninstalling Desktop Monitoring Agent service on {self.system}...")
        
        if self.system == "Windows":
            return self.uninstall_windows_service()
        elif self.system == "Darwin":
            return self.uninstall_macos_service()
        elif self.system == "Linux":
            return self.uninstall_linux_service()
        else:
            print(f"Unsupported platform: {self.system}")
            return False
    
    def install_windows_service(self):
        """Install Windows service"""
        try:
            # Try to use the built-in Windows service functionality
            if self.executable_path.endswith('.exe'):
                # Use sc command to install service
                cmd = [
                    'sc', 'create', self.app_name,
                    'binPath=', f'"{self.executable_path}" --service',
                    'start=', 'auto',
                    'DisplayName=', 'Desktop Monitoring Agent',
                    'description=', 'Monitors desktop activity for administrative purposes'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("Windows service installed successfully")
                    
                    # Start the service
                    start_cmd = ['sc', 'start', self.app_name]
                    start_result = subprocess.run(start_cmd, capture_output=True, text=True)
                    
                    if start_result.returncode == 0:
                        print("Service started successfully")
                    else:
                        print("Service installed but failed to start. You can start it manually.")
                    
                    return True
                else:
                    print(f"Failed to install service: {result.stderr}")
                    return self.install_windows_registry_startup()
            else:
                return self.install_windows_registry_startup()
                
        except Exception as e:
            print(f"Error installing Windows service: {e}")
            return self.install_windows_registry_startup()
    
    def install_windows_registry_startup(self):
        """Install as Windows startup program via registry"""
        try:
            import winreg
            
            # Open registry key for startup programs
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Set the registry value
            if self.executable_path.endswith('.py'):
                value = f'"{sys.executable}" "{self.executable_path}"'
            else:
                value = f'"{self.executable_path}"'
            
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            
            print("Windows startup registry entry created successfully")
            print("The agent will start automatically when Windows starts")
            return True
            
        except Exception as e:
            print(f"Error creating Windows startup entry: {e}")
            return False
    
    def uninstall_windows_service(self):
        """Uninstall Windows service"""
        try:
            # Stop service
            stop_cmd = ['sc', 'stop', self.app_name]
            subprocess.run(stop_cmd, capture_output=True, text=True)
            
            # Delete service
            delete_cmd = ['sc', 'delete', self.app_name]
            result = subprocess.run(delete_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Windows service uninstalled successfully")
            else:
                print("Service not found or already removed")
            
            # Also remove registry entry
            self.uninstall_windows_registry_startup()
            return True
            
        except Exception as e:
            print(f"Error uninstalling Windows service: {e}")
            return False
    
    def uninstall_windows_registry_startup(self):
        """Remove Windows startup registry entry"""
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, self.app_name)
                print("Windows startup registry entry removed")
            except FileNotFoundError:
                pass  # Entry doesn't exist
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"Error removing Windows startup entry: {e}")
            return False
    
    def install_macos_service(self):
        """Install macOS LaunchAgent"""
        try:
            home_dir = Path.home()
            launch_agents_dir = home_dir / "Library" / "LaunchAgents"
            plist_path = launch_agents_dir / f"{self.bundle_id}.plist"
            
            # Create directory if it doesn't exist
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            # Create plist content
            if self.executable_path.endswith('.py'):
                program_args = [sys.executable, self.executable_path, '--service']
            else:
                program_args = [self.executable_path, '--service']
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.bundle_id}</string>
    <key>ProgramArguments</key>
    <array>
        {''.join(f'<string>{arg}</string>' for arg in program_args)}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>{home_dir}/Library/Logs/DesktopAgent.log</string>
    <key>StandardErrorPath</key>
    <string>{home_dir}/Library/Logs/DesktopAgent.error.log</string>
    <key>LSUIElement</key>
    <string>1</string>
    <key>ProcessType</key>
    <string>Background</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>"""
            
            # Write plist file
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the service
            result = subprocess.run(['launchctl', 'load', str(plist_path)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"macOS service installed successfully: {plist_path}")
                print("The agent will start automatically when you log in")
                return True
            else:
                print(f"Failed to load service: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"Error installing macOS service: {e}")
            return False
    
    def uninstall_macos_service(self):
        """Uninstall macOS LaunchAgent"""
        try:
            home_dir = Path.home()
            plist_path = home_dir / "Library" / "LaunchAgents" / f"{self.bundle_id}.plist"
            
            if plist_path.exists():
                # Unload the service
                subprocess.run(['launchctl', 'unload', str(plist_path)], 
                             capture_output=True, text=True)
                
                # Remove the plist file
                plist_path.unlink()
                print("macOS service uninstalled successfully")
            else:
                print("macOS service was not installed")
            
            return True
            
        except Exception as e:
            print(f"Error uninstalling macOS service: {e}")
            return False
    
    def install_linux_service(self):
        """Install Linux systemd user service"""
        try:
            home_dir = Path.home()
            systemd_dir = home_dir / ".config" / "systemd" / "user"
            service_path = systemd_dir / f"{self.service_name}.service"
            
            # Create directory if it doesn't exist
            systemd_dir.mkdir(parents=True, exist_ok=True)
            
            # Create service content
            if self.executable_path.endswith('.py'):
                exec_start = f"{sys.executable} {self.executable_path} --service"
            else:
                exec_start = f"{self.executable_path} --service"
            
            service_content = f"""[Unit]
Description=Desktop Monitoring Agent
After=network.target

[Service]
Type=simple
ExecStart={exec_start}
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
"""
            
            # Write service file
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            commands = [
                ['systemctl', '--user', 'daemon-reload'],
                ['systemctl', '--user', 'enable', f'{self.service_name}.service'],
                ['systemctl', '--user', 'start', f'{self.service_name}.service']
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Warning: Command failed: {' '.join(cmd)}")
                    print(f"Error: {result.stderr}")
            
            # Enable lingering so service starts without login
            subprocess.run(['loginctl', 'enable-linger'], capture_output=True, text=True)
            
            print(f"Linux service installed successfully: {service_path}")
            print("The agent will start automatically at boot")
            return True
            
        except Exception as e:
            print(f"Error installing Linux service: {e}")
            return False
    
    def uninstall_linux_service(self):
        """Uninstall Linux systemd user service"""
        try:
            commands = [
                ['systemctl', '--user', 'stop', f'{self.service_name}.service'],
                ['systemctl', '--user', 'disable', f'{self.service_name}.service']
            ]
            
            for cmd in commands:
                subprocess.run(cmd, capture_output=True, text=True)
            
            # Remove service file
            home_dir = Path.home()
            service_path = home_dir / ".config" / "systemd" / "user" / f"{self.service_name}.service"
            
            if service_path.exists():
                service_path.unlink()
            
            # Reload systemd
            subprocess.run(['systemctl', '--user', 'daemon-reload'], 
                         capture_output=True, text=True)
            
            print("Linux service uninstalled successfully")
            return True
            
        except Exception as e:
            print(f"Error uninstalling Linux service: {e}")
            return False
    
    def check_status(self):
        """Check service status"""
        print(f"Checking service status on {self.system}...")
        
        if self.system == "Windows":
            result = subprocess.run(['sc', 'query', self.app_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Windows service is installed")
                if "RUNNING" in result.stdout:
                    print("Service is currently running")
                else:
                    print("Service is installed but not running")
            else:
                print("Windows service is not installed")
                
        elif self.system == "Darwin":
            home_dir = Path.home()
            plist_path = home_dir / "Library" / "LaunchAgents" / f"{self.bundle_id}.plist"
            if plist_path.exists():
                print("macOS service is installed")
                # Check if loaded
                result = subprocess.run(['launchctl', 'list', self.bundle_id], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("Service is currently loaded")
                else:
                    print("Service is installed but not loaded")
            else:
                print("macOS service is not installed")
                
        elif self.system == "Linux":
            result = subprocess.run(['systemctl', '--user', 'is-active', f'{self.service_name}.service'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Linux service is running")
            else:
                result = subprocess.run(['systemctl', '--user', 'is-enabled', f'{self.service_name}.service'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("Linux service is installed but not running")
                else:
                    print("Linux service is not installed")

def main():
    """Main function"""
    installer = ServiceInstaller()
    
    if len(sys.argv) < 2:
        print("Desktop Monitoring Agent Service Installer")
        print("Usage:")
        print("  python install_service.py install    - Install service")
        print("  python install_service.py uninstall  - Uninstall service")
        print("  python install_service.py status     - Check service status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "install":
        success = installer.install()
        if success:
            print("\nService installation completed successfully!")
            print("The Desktop Monitoring Agent will now start automatically.")
        else:
            print("\nService installation failed!")
            sys.exit(1)
            
    elif command == "uninstall":
        success = installer.uninstall()
        if success:
            print("\nService uninstallation completed successfully!")
        else:
            print("\nService uninstallation failed!")
            sys.exit(1)
            
    elif command == "status":
        installer.check_status()
        
    else:
        print(f"Unknown command: {command}")
        print("Use 'install', 'uninstall', or 'status'")
        sys.exit(1)

if __name__ == "__main__":
    main()
