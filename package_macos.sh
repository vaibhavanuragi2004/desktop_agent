#!/bin/bash

# macOS Packaging Script for Desktop Monitoring Agent
# This script creates a .dmg file for macOS distribution

set -e

echo "=== macOS Packaging Script ==="
echo "Building Desktop Monitoring Agent for macOS"

# Configuration
APP_NAME="DesktopMonitoringAgent"
BUNDLE_ID="com.company.desktopagent"
VERSION="2.0.0"
DMG_NAME="DesktopMonitoringAgent-${VERSION}"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script must be run on macOS"
    exit 1
fi

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec
rm -rf "${APP_NAME}.app"
rm -f "${DMG_NAME}.dmg"

# Install dependencies
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements_agent.txt
python3 -m pip install pyinstaller

# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller --onefile \
    --windowed \
    --name "${APP_NAME}" \
    --add-data "macos_service.plist:." \
    --hidden-import "pynput.keyboard._darwin" \
    --hidden-import "pynput.mouse._darwin" \
    --icon "agent_icon.icns" \
    --osx-bundle-identifier "${BUNDLE_ID}" \
    desktop_agent.py

# Check if build was successful
if [ ! -f "dist/${APP_NAME}" ]; then
    echo "Error: Build failed - executable not found"
    exit 1
fi

# Create .app bundle structure
echo "Creating .app bundle..."
APP_DIR="${APP_NAME}.app"
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

# Copy executable
cp "dist/${APP_NAME}" "${APP_DIR}/Contents/MacOS/"

# Create Info.plist
cat > "${APP_DIR}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSUIElement</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppleEventsUsageDescription</key>
    <string>This app monitors desktop activity for administrative purposes.</string>
    <key>NSCameraUsageDescription</key>
    <string>This app captures screenshots for monitoring purposes.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>This app may monitor audio activity for administrative purposes.</string>
</dict>
</plist>
EOF

# Copy service files
if [ -f "macos_service.plist" ]; then
    cp macos_service.plist "${APP_DIR}/Contents/Resources/"
fi

# Create installer script
cat > "${APP_DIR}/Contents/Resources/install_service.sh" << 'EOF'
#!/bin/bash
# Service installation script for macOS

PLIST_NAME="com.company.desktopagent.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
APP_PATH="$1"

if [ -z "$APP_PATH" ]; then
    APP_PATH="/Applications/DesktopMonitoringAgent.app"
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Create plist file
cat > "$LAUNCH_AGENTS_DIR/$PLIST_NAME" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.desktopagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_PATH/Contents/MacOS/DesktopMonitoringAgent</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/DesktopAgent.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/DesktopAgent.error.log</string>
    <key>LSUIElement</key>
    <string>1</string>
</dict>
</plist>
PLIST_EOF

# Load the service
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "Service installed and started successfully"
EOF

chmod +x "${APP_DIR}/Contents/Resources/install_service.sh"

# Make executable
chmod +x "${APP_DIR}/Contents/MacOS/${APP_NAME}"

echo "App bundle created: ${APP_DIR}"

# Create DMG
echo "Creating DMG file..."

# Create temporary directory for DMG contents
DMG_DIR="dmg_temp"
rm -rf "$DMG_DIR"
mkdir "$DMG_DIR"

# Copy app to DMG directory
cp -R "${APP_DIR}" "$DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << EOF
Desktop Monitoring Agent v${VERSION}

Installation Instructions:
1. Drag DesktopMonitoringAgent.app to the Applications folder
2. Run the app from Applications folder
3. Follow the setup wizard to pair with your monitoring server

For automatic startup:
1. Open Terminal
2. Run: /Applications/DesktopMonitoringAgent.app/Contents/Resources/install_service.sh

Support: contact your system administrator
EOF

# Create DMG
hdiutil create -volname "${APP_NAME} ${VERSION}" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "${DMG_NAME}.dmg"

# Clean up
rm -rf "$DMG_DIR"
rm -rf build dist *.spec

echo "=== Build Complete ==="
echo "DMG file created: ${DMG_NAME}.dmg"
echo "App bundle created: ${APP_DIR}"
echo ""
echo "Distribution files:"
echo "  - ${DMG_NAME}.dmg (for distribution)"
echo "  - ${APP_DIR} (standalone app)"
echo ""
echo "Installation:"
echo "  1. Mount the DMG file"
echo "  2. Drag the app to Applications folder"
echo "  3. Run the app and follow setup instructions"
