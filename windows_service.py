#!/usr/bin/env python3
"""
Windows service installer for the desktop agent
"""

import os
import sys
import platform
import subprocess
import time

def install_as_windows_service():
    """Install the agent as a Windows service"""
    if platform.system() != "Windows":
        print("This script is only for Windows systems")
        return False
    
    try:
        # Try to install pywin32 if not available
        try:
            import win32serviceutil
            import win32service
            import win32event
            import servicemanager
        except ImportError:
            print("Installing required Windows service utilities...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            import win32serviceutil
            import win32service
            import win32event
            import servicemanager
        
        class DesktopMonitoringService(win32serviceutil.ServiceFramework):
            _svc_name_ = "DesktopMonitoringAgent"
            _svc_display_name_ = "Desktop Monitoring Agent"
            _svc_description_ = "Monitors desktop activity and sends data to management server"
            
            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                self.is_alive = True
                
            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                self.is_alive = False
                win32event.SetEvent(self.hWaitStop)
                
            def SvcDoRun(self):
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                self.main()
                
            def main(self):
                """Main service loop"""
                try:
                    # Get the executable path
                    if getattr(sys, 'frozen', False):
                        # Running as compiled executable
                        agent_path = sys.executable
                    else:
                        # Running as script
                        agent_path = os.path.join(os.path.dirname(__file__), "desktop_agent.py")
                    
                    while self.is_alive:
                        try:
                            # Start the agent process
                            process = subprocess.Popen(
                                [sys.executable, agent_path] if not getattr(sys, 'frozen', False) else [agent_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            
                            # Monitor the process
                            while self.is_alive and process.poll() is None:
                                time.sleep(1)
                            
                            if process.poll() is not None and self.is_alive:
                                # Process died, restart it
                                servicemanager.LogMsg(
                                    servicemanager.EVENTLOG_WARNING_TYPE,
                                    servicemanager.PYS_SERVICE_STARTED,
                                    (self._svc_name_, 'Agent process died, restarting...')
                                )
                                time.sleep(5)  # Wait before restart
                            else:
                                # Service is stopping
                                process.terminate()
                                
                        except Exception as e:
                            servicemanager.LogMsg(
                                servicemanager.EVENTLOG_ERROR_TYPE,
                                servicemanager.PYS_SERVICE_STARTED,
                                (self._svc_name_, f'Error in service loop: {str(e)}')
                            )
                            time.sleep(10)
                            
                except Exception as e:
                    servicemanager.LogMsg(
                        servicemanager.EVENTLOG_ERROR_TYPE,
                        servicemanager.PYS_SERVICE_STARTED,
                        (self._svc_name_, f'Fatal service error: {str(e)}')
                    )
        
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(DesktopMonitoringService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(DesktopMonitoringService)
        
        return True
        
    except Exception as e:
        print(f"Error setting up Windows service: {e}")
        return False

def create_startup_registry_entry():
    """Create Windows startup registry entry as fallback"""
    try:
        import winreg
        
        # Get executable path
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "desktop_agent.py"))
        
        # Open registry key for startup programs
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # Set the registry value
        winreg.SetValueEx(
            key,
            "DesktopMonitoringAgent",
            0,
            winreg.REG_SZ,
            f'"{exe_path}"'
        )
        
        winreg.CloseKey(key)
        print("Startup registry entry created successfully")
        return True
        
    except Exception as e:
        print(f"Error creating startup registry entry: {e}")
        return False

def remove_startup_registry_entry():
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
            winreg.DeleteValue(key, "DesktopMonitoringAgent")
            print("Startup registry entry removed")
        except FileNotFoundError:
            print("Startup registry entry was not found")
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        print(f"Error removing startup registry entry: {e}")
        return False

def main():
    """Main function"""
    if platform.system() != "Windows":
        print("This script is only for Windows systems")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "install":
            print("Installing Desktop Monitoring Agent as Windows service...")
            if install_as_windows_service():
                print("Service installed successfully")
                print("Starting service...")
                subprocess.run(["sc", "start", "DesktopMonitoringAgent"])
            else:
                print("Service installation failed, trying startup registry entry...")
                create_startup_registry_entry()
                
        elif command == "remove" or command == "uninstall":
            print("Removing Desktop Monitoring Agent service...")
            try:
                subprocess.run(["sc", "stop", "DesktopMonitoringAgent"])
                subprocess.run(["sc", "delete", "DesktopMonitoringAgent"])
                print("Service removed")
            except:
                pass
            remove_startup_registry_entry()
            
        elif command == "start":
            subprocess.run(["sc", "start", "DesktopMonitoringAgent"])
            
        elif command == "stop":
            subprocess.run(["sc", "stop", "DesktopMonitoringAgent"])
            
        else:
            print("Usage: windows_service.py [install|remove|start|stop]")
    else:
        # Run as service
        install_as_windows_service()

if __name__ == "__main__":
    main()
