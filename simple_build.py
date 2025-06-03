#!/usr/bin/env python3
"""
Simple, robust build script for Desktop Monitoring Agent
Handles cross-platform builds without complex dependencies
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class SimpleBuild:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        
        # Clean build directories
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
    
    def install_dependencies(self):
        """Install basic build dependencies"""
        print("Installing build dependencies...")
        
        # Core dependencies that work on all platforms
        core_deps = [
            "pyinstaller",
            "pillow", 
            "requests",
            "pynput",
            "schedule",
            "mss",
            "psutil"
        ]
        
        for dep in core_deps:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=False)  # Don't fail if one package fails
    
    def build_executable(self):
        """Build executable with minimal dependencies"""
        print(f"Building executable for {platform.system()}...")
        
        # Basic PyInstaller command that works everywhere
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name", "DesktopMonitoringAgent",
            "--add-data", f"{self.root_dir / 'requirements_agent.txt'};.",
            # Core hidden imports that should be available
            "--hidden-import", "requests",
            "--hidden-import", "PIL",
            "--hidden-import", "mss", 
            "--hidden-import", "schedule",
            "--hidden-import", "psutil",
            "--hidden-import", "json",
            "--hidden-import", "datetime",
            "--hidden-import", "threading",
            "--hidden-import", "logging",
            str(self.root_dir / "desktop_agent.py")
        ]
        
        # Add platform-specific options only if safe
        if platform.system() == "Windows":
            cmd.extend(["--windowed"])
            if (self.root_dir / "agent_icon.ico").exists():
                cmd.extend(["--icon", str(self.root_dir / "agent_icon.ico")])
        else:
            cmd.extend(["--console"])
            if (self.root_dir / "agent_icon.icns").exists():
                cmd.extend(["--icon", str(self.root_dir / "agent_icon.icns")])
        
        # Try to add pynput if available
        try:
            import pynput
            cmd.extend(["--hidden-import", "pynput"])
            print("Added pynput support")
        except ImportError:
            print("Warning: pynput not available - keyboard/mouse monitoring disabled")
        
        print("Running PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
        
        print("Build successful!")
        return True
    
    def create_simple_package(self):
        """Create a simple package for distribution"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return self.create_macos_package()
        elif system == "Windows":  # Windows
            return self.create_windows_package()
        else:  # Linux and others
            return self.create_linux_package()
    
    def create_macos_package(self):
        """Create simple macOS package"""
        print("Creating macOS package...")
        
        package_dir = self.root_dir / "DesktopMonitoringAgent-macOS"
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / "DesktopMonitoringAgent"
        if exe_path.exists():
            shutil.copy2(exe_path, package_dir / "DesktopMonitoringAgent")
            os.chmod(package_dir / "DesktopMonitoringAgent", 0o755)
        
        # Create simple installer script
        installer = package_dir / "install.sh"
        installer_content = '''#!/bin/bash
echo "Installing Desktop Monitoring Agent..."

# Create application directory
sudo mkdir -p /Applications/DesktopMonitoringAgent.app/Contents/MacOS/
sudo cp DesktopMonitoringAgent /Applications/DesktopMonitoringAgent.app/Contents/MacOS/
sudo chmod +x /Applications/DesktopMonitoringAgent.app/Contents/MacOS/DesktopMonitoringAgent

# Create launch agent
cat > ~/Library/LaunchAgents/com.company.desktop-monitoring-agent.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.desktop-monitoring-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/DesktopMonitoringAgent.app/Contents/MacOS/DesktopMonitoringAgent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.company.desktop-monitoring-agent.plist

echo "Installation complete!"
'''
        installer.write_text(installer_content)
        os.chmod(installer, 0o755)
        
        # Create README
        readme = package_dir / "README.txt"
        readme.write_text("""Desktop Monitoring Agent for macOS

Installation:
1. Run: chmod +x install.sh
2. Run: ./install.sh
3. The agent will start automatically

The agent will run in the background and start automatically at login.
""")
        
        # Create DMG if possible
        try:
            subprocess.run([
                "hdiutil", "create", "-srcfolder", str(package_dir),
                "-volname", "Desktop Monitoring Agent",
                str(self.root_dir / "DesktopMonitoringAgent-macOS.dmg")
            ], check=True)
            print("DMG created successfully!")
            return self.root_dir / "DesktopMonitoringAgent-macOS.dmg"
        except:
            print("DMG creation failed - package folder created instead")
            return package_dir
    
    def create_windows_package(self):
        """Create simple Windows package"""
        print("Creating Windows package...")
        
        package_dir = self.root_dir / "DesktopMonitoringAgent-Windows"
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / "DesktopMonitoringAgent.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, package_dir / "DesktopMonitoringAgent.exe")
        
        # Create installer batch file
        installer = package_dir / "install.bat"
        installer_content = '''@echo off
echo Installing Desktop Monitoring Agent...

rem Create program directory
if not exist "%ProgramFiles%\\DesktopMonitoringAgent" mkdir "%ProgramFiles%\\DesktopMonitoringAgent"
copy DesktopMonitoringAgent.exe "%ProgramFiles%\\DesktopMonitoringAgent\\"

rem Add to startup
reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "DesktopMonitoringAgent" /t REG_SZ /d "\"%ProgramFiles%\\DesktopMonitoringAgent\\DesktopMonitoringAgent.exe\"" /f

echo Installation complete!
echo The agent will start at next login.
pause
'''
        installer.write_text(installer_content)
        
        # Create uninstaller
        uninstaller = package_dir / "uninstall.bat"
        uninstaller_content = '''@echo off
echo Uninstalling Desktop Monitoring Agent...

taskkill /f /im DesktopMonitoringAgent.exe 2>nul
reg delete "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "DesktopMonitoringAgent" /f
rmdir /s /q "%ProgramFiles%\\DesktopMonitoringAgent"

echo Uninstallation complete!
pause
'''
        uninstaller.write_text(uninstaller_content)
        
        # Create README
        readme = package_dir / "README.txt"
        readme.write_text("""Desktop Monitoring Agent for Windows

Installation:
1. Right-click install.bat and select "Run as administrator"
2. Follow the prompts
3. The agent will start automatically at next login

Uninstallation:
1. Right-click uninstall.bat and select "Run as administrator"

The agent runs in the background and starts automatically with Windows.
""")
        
        print("Windows package created successfully!")
        return package_dir
    
    def create_linux_package(self):
        """Create simple Linux package"""
        print("Creating Linux package...")
        
        package_dir = self.root_dir / "DesktopMonitoringAgent-Linux"
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.dist_dir / "DesktopMonitoringAgent"
        if exe_path.exists():
            shutil.copy2(exe_path, package_dir / "DesktopMonitoringAgent")
            os.chmod(package_dir / "DesktopMonitoringAgent", 0o755)
        
        # Create installer script
        installer = package_dir / "install.sh"
        installer_content = '''#!/bin/bash
echo "Installing Desktop Monitoring Agent..."

# Copy to local bin
mkdir -p ~/.local/bin
cp DesktopMonitoringAgent ~/.local/bin/
chmod +x ~/.local/bin/DesktopMonitoringAgent

# Create systemd user service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/desktop-monitoring-agent.service << EOF
[Unit]
Description=Desktop Monitoring Agent
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/DesktopMonitoringAgent
Restart=always
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

# Enable and start the service
systemctl --user daemon-reload
systemctl --user enable desktop-monitoring-agent.service
systemctl --user start desktop-monitoring-agent.service

echo "Installation complete!"
'''
        installer.write_text(installer_content)
        os.chmod(installer, 0o755)
        
        # Create README
        readme = package_dir / "README.txt"
        readme.write_text("""Desktop Monitoring Agent for Linux

Installation:
1. Run: chmod +x install.sh
2. Run: ./install.sh
3. The agent will start automatically

The agent runs as a user service and starts automatically at login.
""")
        
        print("Linux package created successfully!")
        return package_dir
    
    def build(self):
        """Main build process"""
        print("=== Simple Desktop Agent Build ===")
        print(f"Platform: {platform.system()}")
        
        try:
            # Install dependencies
            self.install_dependencies()
            
            # Build executable
            if not self.build_executable():
                print("Build failed!")
                return False
            
            # Create package
            package = self.create_simple_package()
            
            print(f"\n=== Build Complete ===")
            print(f"Package created: {package}")
            print("\nTo install:")
            
            if platform.system() == "Windows":
                print("1. Run install.bat as Administrator")
            else:
                print("1. chmod +x install.sh")
                print("2. ./install.sh")
            
            return True
            
        except Exception as e:
            print(f"Build error: {e}")
            return False

def main():
    builder = SimpleBuild()
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()