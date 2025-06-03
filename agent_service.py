#!/usr/bin/env python3
"""
Cross-platform service wrapper for the desktop agent
"""

import os
import sys
import time
import platform
import subprocess
import threading
from desktop_agent import DesktopAgent

class AgentService:
    """Service wrapper for the desktop agent"""
    
    def __init__(self):
        self.agent = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 5
        
    def start_agent(self):
        """Start the desktop agent"""
        try:
            self.agent = DesktopAgent()
            self.running = True
            self.agent.run()
        except Exception as e:
            print(f"Agent error: {e}")
            self.running = False
            
    def monitor_agent(self):
        """Monitor and restart agent if needed"""
        while True:
            if not self.running and self.restart_count < self.max_restarts:
                print(f"Restarting agent (attempt {self.restart_count + 1})")
                self.restart_count += 1
                
                # Start agent in a new thread
                agent_thread = threading.Thread(target=self.start_agent, daemon=True)
                agent_thread.start()
                
                # Wait before checking again
                time.sleep(30)
            elif self.restart_count >= self.max_restarts:
                print("Max restart attempts reached. Service stopping.")
                break
            else:
                time.sleep(10)
    
    def run_as_service(self):
        """Run as a background service"""
        print("Starting Desktop Monitoring Agent Service")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_agent, daemon=True)
        monitor_thread.start()
        
        # Start the agent initially
        self.start_agent()

def install_windows_service():
    """Install as Windows service"""
    if platform.system() != "Windows":
        return False
    
    try:
        import win32serviceutil
        import win32service
        import win32event
        
        class DesktopAgentService(win32serviceutil.ServiceFramework):
            _svc_name_ = "DesktopMonitoringAgent"
            _svc_display_name_ = "Desktop Monitoring Agent"
            _svc_description_ = "Monitors desktop activity for administrative purposes"
            
            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                self.service = AgentService()
            
            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                win32event.SetEvent(self.hWaitStop)
            
            def SvcDoRun(self):
                self.service.run_as_service()
        
        if len(sys.argv) == 1:
            # Run as service
            win32serviceutil.HandleCommandLine(DesktopAgentService)
        else:
            # Install/remove service
            win32serviceutil.HandleCommandLine(DesktopAgentService)
        
        return True
        
    except ImportError:
        print("Windows service utilities not available")
        return False

def install_macos_service():
    """Install as macOS LaunchAgent"""
    if platform.system() != "Darwin":
        return False
    
    try:
        # Get paths
        home_dir = os.path.expanduser("~")
        launch_agents_dir = os.path.join(home_dir, "Library", "LaunchAgents")
        plist_path = os.path.join(launch_agents_dir, "com.company.desktopagent.plist")
        
        # Ensure directory exists
        os.makedirs(launch_agents_dir, exist_ok=True)
        
        # Get executable path
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
        else:
            executable_path = os.path.abspath(__file__)
        
        # Create plist content
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.desktopagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable_path}</string>
        <string>--service</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{home_dir}/Library/Logs/DesktopAgent.log</string>
    <key>StandardErrorPath</key>
    <string>{home_dir}/Library/Logs/DesktopAgent.error.log</string>
    <key>LSUIElement</key>
    <string>1</string>
</dict>
</plist>"""
        
        # Write plist file
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        # Load the service
        subprocess.run(['launchctl', 'load', plist_path], check=True)
        print(f"macOS service installed: {plist_path}")
        
        return True
        
    except Exception as e:
        print(f"Error installing macOS service: {e}")
        return False

def install_linux_service():
    """Install as Linux systemd service"""
    if platform.system() != "Linux":
        return False
    
    try:
        # Get executable path
        if getattr(sys, 'frozen', False):
            executable_path = sys.executable
        else:
            executable_path = os.path.abspath(__file__)
        
        # Create systemd service file
        service_content = f"""[Unit]
Description=Desktop Monitoring Agent
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
ExecStart={executable_path} --service
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
"""
        
        service_path = f"/home/{os.getenv('USER')}/.config/systemd/user/desktop-agent.service"
        os.makedirs(os.path.dirname(service_path), exist_ok=True)
        
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        # Enable and start service
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'enable', 'desktop-agent.service'], check=True)
        subprocess.run(['systemctl', '--user', 'start', 'desktop-agent.service'], check=True)
        
        print(f"Linux service installed: {service_path}")
        return True
        
    except Exception as e:
        print(f"Error installing Linux service: {e}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--service":
            # Run as service
            service = AgentService()
            service.run_as_service()
            
        elif command == "--install":
            # Install service
            system = platform.system()
            
            if system == "Windows":
                success = install_windows_service()
            elif system == "Darwin":
                success = install_macos_service()
            elif system == "Linux":
                success = install_linux_service()
            else:
                print(f"Service installation not supported on {system}")
                success = False
            
            if success:
                print("Service installed successfully")
            else:
                print("Service installation failed")
                sys.exit(1)
        
        elif command == "--uninstall":
            # Uninstall service (implementation depends on platform)
            print("Service uninstallation not implemented yet")
            
        else:
            print("Unknown command. Use --service, --install, or --uninstall")
            sys.exit(1)
    else:
        # Run directly
        service = AgentService()
        service.run_as_service()

if __name__ == "__main__":
    main()
