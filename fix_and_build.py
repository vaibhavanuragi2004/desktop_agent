#!/usr/bin/env python3
"""
Fixed build script that handles missing dependencies gracefully
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def install_basic_deps():
    """Install only the essential dependencies that work everywhere"""
    deps = [
        "pyinstaller>=5.0",
        "pillow>=9.0.0", 
        "requests>=2.25.0",
        "schedule>=1.1.0",
        "mss>=6.0.0",
        "psutil>=5.8.0"
    ]
    
    print("Installing core dependencies...")
    for dep in deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            print(f"✓ {dep}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")

def create_spec_file():
    """Create a custom PyInstaller spec file"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_agent.py'],
    pathex=[],
    binaries=[],
    datas=[('requirements_agent.txt', '.')],
    hiddenimports=[
        'requests',
        'PIL',
        'PIL.Image',
        'mss',
        'schedule',
        'psutil',
        'json',
        'datetime',
        'threading',
        'logging',
        'platform',
        'hashlib',
        'uuid',
        'io',
        'time',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Try to add optional imports safely
try:
    import pynput
    a.hiddenimports.extend(['pynput', 'pynput.keyboard', 'pynput.mouse'])
except ImportError:
    pass

# Platform-specific imports
import platform
if platform.system() == "Windows":
    try:
        import win32api
        a.hiddenimports.extend(['win32api', 'win32gui', 'win32process'])
    except ImportError:
        pass
elif platform.system() == "Linux":
    try:
        import Xlib
        a.hiddenimports.extend(['Xlib', 'Xlib.display'])
    except ImportError:
        pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DesktopMonitoringAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('agent.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created custom spec file")

def build_with_spec():
    """Build using the custom spec file"""
    print("Building executable...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean", "--noconfirm", "agent.spec"
        ], capture_output=True, text=True, check=True)
        
        print("Build successful!")
        return True
        
    except subprocess.CalledProcessError as e:
        print("Build failed:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_packages():
    """Create distribution packages"""
    system = platform.system()
    dist_dir = Path("dist")
    
    if system == "Darwin":  # macOS
        create_macos_package(dist_dir)
    elif system == "Windows":
        create_windows_package(dist_dir)
    else:  # Linux
        create_linux_package(dist_dir)

def create_macos_package(dist_dir):
    """Create macOS package"""
    package_name = "DesktopMonitoringAgent-macOS"
    package_dir = Path(package_name)
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    exe_file = dist_dir / "DesktopMonitoringAgent"
    if exe_file.exists():
        shutil.copy2(exe_file, package_dir / "DesktopMonitoringAgent")
        os.chmod(package_dir / "DesktopMonitoringAgent", 0o755)
    
    # Create installer
    installer_script = f'''#!/bin/bash
echo "Installing Desktop Monitoring Agent for macOS..."

# Create app directory
sudo mkdir -p "/Applications/Desktop Monitoring Agent.app/Contents/MacOS"
sudo cp DesktopMonitoringAgent "/Applications/Desktop Monitoring Agent.app/Contents/MacOS/"
sudo chmod +x "/Applications/Desktop Monitoring Agent.app/Contents/MacOS/DesktopMonitoringAgent"

# Create Info.plist
sudo tee "/Applications/Desktop Monitoring Agent.app/Contents/Info.plist" > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>DesktopMonitoringAgent</string>
    <key>CFBundleIdentifier</key>
    <string>com.company.desktop-monitoring-agent</string>
    <key>CFBundleName</key>
    <string>Desktop Monitoring Agent</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

# Create launch agent
mkdir -p ~/Library/LaunchAgents
tee ~/Library/LaunchAgents/com.company.desktop-monitoring-agent.plist > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.desktop-monitoring-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Desktop Monitoring Agent.app/Contents/MacOS/DesktopMonitoringAgent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the agent
launchctl load ~/Library/LaunchAgents/com.company.desktop-monitoring-agent.plist

echo "Installation complete! The agent will start automatically."
'''
    
    installer_file = package_dir / "install.sh"
    installer_file.write_text(installer_script)
    os.chmod(installer_file, 0o755)
    
    # Create DMG if hdiutil is available
    try:
        dmg_name = f"{package_name}.dmg"
        subprocess.run([
            "hdiutil", "create", "-srcfolder", str(package_dir),
            "-volname", "Desktop Monitoring Agent",
            dmg_name
        ], check=True)
        print(f"✓ Created {dmg_name}")
    except:
        print(f"✓ Created {package_dir} (DMG creation not available)")

def create_windows_package(dist_dir):
    """Create Windows package"""
    package_name = "DesktopMonitoringAgent-Windows"
    package_dir = Path(package_name)
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    exe_file = dist_dir / "DesktopMonitoringAgent.exe"
    if exe_file.exists():
        shutil.copy2(exe_file, package_dir / "DesktopMonitoringAgent.exe")
    
    # Create installer
    installer_bat = f'''@echo off
echo Installing Desktop Monitoring Agent for Windows...

rem Create installation directory
set INSTALL_DIR=%ProgramFiles%\\Desktop Monitoring Agent
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

rem Copy executable
copy "DesktopMonitoringAgent.exe" "%INSTALL_DIR%\\"

rem Add to Windows startup
reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "DesktopMonitoringAgent" /t REG_SZ /d "\"%INSTALL_DIR%\\DesktopMonitoringAgent.exe\"" /f

echo Installation complete! The agent will start automatically at login.
pause
'''
    
    (package_dir / "install.bat").write_text(installer_bat)
    
    # Create uninstaller
    uninstaller_bat = f'''@echo off
echo Uninstalling Desktop Monitoring Agent...

rem Stop the process
taskkill /f /im "DesktopMonitoringAgent.exe" 2>nul

rem Remove from startup
reg delete "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "DesktopMonitoringAgent" /f 2>nul

rem Remove installation directory
set INSTALL_DIR=%ProgramFiles%\\Desktop Monitoring Agent
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Uninstallation complete!
pause
'''
    
    (package_dir / "uninstall.bat").write_text(uninstaller_bat)
    
    print(f"✓ Created {package_dir}")

def create_linux_package(dist_dir):
    """Create Linux package"""
    package_name = "DesktopMonitoringAgent-Linux"
    package_dir = Path(package_name)
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    exe_file = dist_dir / "DesktopMonitoringAgent"
    if exe_file.exists():
        shutil.copy2(exe_file, package_dir / "DesktopMonitoringAgent")
        os.chmod(package_dir / "DesktopMonitoringAgent", 0o755)
    
    # Create installer
    installer_script = f'''#!/bin/bash
echo "Installing Desktop Monitoring Agent for Linux..."

# Create local installation
mkdir -p ~/.local/bin
cp DesktopMonitoringAgent ~/.local/bin/
chmod +x ~/.local/bin/DesktopMonitoringAgent

# Create systemd user service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/desktop-monitoring-agent.service <<EOF
[Unit]
Description=Desktop Monitoring Agent
After=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/DesktopMonitoringAgent
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

# Enable and start service
systemctl --user daemon-reload
systemctl --user enable desktop-monitoring-agent.service
systemctl --user start desktop-monitoring-agent.service

echo "Installation complete! The agent is now running."
'''
    
    installer_file = package_dir / "install.sh"
    installer_file.write_text(installer_script)
    os.chmod(installer_file, 0o755)
    
    print(f"✓ Created {package_dir}")

def main():
    print("=== Fixed Desktop Monitoring Agent Builder ===")
    
    # Clean previous builds
    for dir_name in ["build", "dist", "__pycache__"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
    
    # Remove old spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
    
    # Install dependencies
    install_basic_deps()
    
    # Create and use custom spec file
    create_spec_file()
    
    # Build executable
    if build_with_spec():
        create_packages()
        
        print("\n=== Build Complete ===")
        print(f"Platform: {platform.system()}")
        print("Package created successfully!")
        
        if platform.system() == "Darwin":
            print("To install on macOS: ./install.sh")
        elif platform.system() == "Windows":
            print("To install on Windows: Right-click install.bat → Run as administrator")
        else:
            print("To install on Linux: ./install.sh")
    else:
        print("Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()