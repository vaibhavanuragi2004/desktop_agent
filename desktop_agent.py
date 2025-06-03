#!/usr/bin/env python3
"""
Desktop Monitoring Agent
A cross-platform desktop monitoring agent that captures screenshots and activity data
and sends them to a Django backend server.
"""

import requests
import time
import os
import sys
import json
import signal
import subprocess
from datetime import datetime, timedelta
import mss
from PIL import Image
import io
import platform
import schedule
import threading
import logging
from logging.handlers import RotatingFileHandler
import socket
import hashlib
import uuid

# Optional imports with fallback handling
PYNPUT_AVAILABLE = False
try:
    from pynput import keyboard, mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    pass

PYAUTOGUI_AVAILABLE = False
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pass

# Agent Configuration
APP_NAME = "DesktopMonitoringAgent"
AGENT_VERSION = "2.0.0"
CONFIG_FILENAME = "agent_config.json"
LOG_FILENAME = "agent.log"

class DesktopAgent:
    def __init__(self):
        self.setup_directories()
        self.setup_logging()
        self.load_config()
        
        # Thread management
        self.stop_event = threading.Event()
        self.threads = []
        
        # Activity tracking
        self.activity_lock = threading.Lock()
        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.last_activity_log = datetime.now()
        
        # Listeners
        self.keyboard_listener = None
        self.mouse_listener = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info(f"Desktop Agent {AGENT_VERSION} initialized")
        
    def setup_directories(self):
        """Setup application data directories"""
        home = os.path.expanduser("~")
        
        if platform.system() == "Windows":
            self.app_data_dir = os.path.join(os.environ.get('APPDATA', 
                os.path.join(home, 'AppData', 'Roaming')), APP_NAME)
        elif platform.system() == "Darwin":
            self.app_data_dir = os.path.join(home, "Library", "Application Support", APP_NAME)
        else:
            self.app_data_dir = os.path.join(home, ".config", APP_NAME.lower())
        
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.app_data_dir, CONFIG_FILENAME)
        self.log_file = os.path.join(self.app_data_dir, LOG_FILENAME)
        self.screenshots_dir = os.path.join(self.app_data_dir, "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger('DesktopAgent')
        self.logger.setLevel(logging.INFO)
        
        # Create rotating file handler
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Also log to console in debug mode
        if '--debug' in sys.argv:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "server_url": "http://127.0.0.1:8000",
            "api_base_path": "/api/v1/monitoring/",
            "agent_token": None,
            "user_pk": None,
            "screenshot_interval_seconds": 300,
            "activity_log_interval_seconds": 60,
            "enable_screenshot_capture": True,
            "enable_keystroke_logging": True,
            "enable_mouse_logging": True,
            "monitoring_active": False,
            "first_run_complete": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                self.logger.info("Configuration loaded from file")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        self.config = default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Configuration saved")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def get_device_info(self):
        """Get device information for pairing"""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "architecture": platform.architecture()[0],
            "agent_version": AGENT_VERSION
        }
    
    def pair_with_server(self, pairing_code):
        """Pair agent with server using pairing code"""
        try:
            url = f"{self.config['server_url']}{self.config['api_base_path']}pair-agent/"
            
            payload = {
                "pairing_token": pairing_code,
                "device_info": self.get_device_info()
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.config['agent_token'] = data['agent_token']
                self.config['user_pk'] = data['user_pk']
                self.config['first_run_complete'] = True
                self.save_config()
                self.logger.info("Successfully paired with server")
                return True
            else:
                error_msg = response.json().get('error', 'Unknown error')
                self.logger.error(f"Pairing failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during pairing: {e}")
            return False
    
    def get_auth_headers(self):
        """Get authentication headers for API requests"""
        if not self.config.get('agent_token'):
            return None
        return {'Authorization': f"AgentToken {self.config['agent_token']}"}
    
    def fetch_settings_from_server(self):
        """Fetch monitoring settings from server"""
        try:
            headers = self.get_auth_headers()
            if not headers:
                return False
            
            url = f"{self.config['server_url']}{self.config['api_base_path']}get-settings/"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                settings = response.json()
                
                # Update configuration with server settings
                self.config.update({
                    'user_pk': settings.get('user_pk', self.config['user_pk']),
                    'screenshot_interval_seconds': settings.get('screenshot_interval_seconds', 300),
                    'activity_log_interval_seconds': settings.get('activity_log_interval_seconds', 60),
                    'enable_screenshot_capture': settings.get('enable_screenshot_capture', True),
                    'enable_keystroke_logging': settings.get('enable_keystroke_logging', True),
                    'enable_mouse_logging': settings.get('enable_mouse_logging', True),
                    'monitoring_active': any([
                        settings.get('enable_screenshot_capture', False),
                        settings.get('enable_keystroke_logging', False),
                        settings.get('enable_mouse_logging', False)
                    ])
                })
                
                self.save_config()
                self.logger.info("Settings updated from server")
                return True
            else:
                self.logger.error(f"Failed to fetch settings: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fetching settings: {e}")
            return False
    
    def capture_screenshot(self):
        """Capture and upload screenshot"""
        if not self.config.get('enable_screenshot_capture'):
            return
        
        try:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Get active window title
                window_title = self.get_active_window_title()
                
                # Save to temporary file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = os.path.join(self.screenshots_dir, f"screenshot_{timestamp}.png")
                img.save(temp_path, "PNG")
                
                # Upload to server
                self.upload_screenshot(temp_path, window_title)
                
                # Clean up temporary file
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
    
    def get_active_window_title(self):
        """Get active window title (cross-platform)"""
        try:
            if platform.system() == "Windows":
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                
                hwnd = user32.GetForegroundWindow()
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                
                return buff.value
                
            elif platform.system() == "Darwin":
                # macOS
                script = '''
                tell application "System Events"
                    name of first application process whose frontmost is true
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
                
            elif PYAUTOGUI_AVAILABLE:
                return pyautogui.getActiveWindow().title if pyautogui.getActiveWindow() else "Unknown"
                
        except Exception as e:
            self.logger.error(f"Error getting active window: {e}")
        
        return "Unknown"
    
    def upload_screenshot(self, image_path, window_title):
        """Upload screenshot to server"""
        try:
            headers = self.get_auth_headers()
            if not headers:
                return False
            
            url = f"{self.config['server_url']}{self.config['api_base_path']}upload-screenshot/"
            
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {
                    'active_window_title_at_capture': window_title,
                    'captured_at': datetime.now().isoformat()
                }
                
                response = requests.post(url, files=files, data=data, 
                                       headers=headers, timeout=60)
            
            if response.status_code == 200:
                self.logger.info("Screenshot uploaded successfully")
                return True
            else:
                self.logger.error(f"Screenshot upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error uploading screenshot: {e}")
            return False
    
    def log_activity(self):
        """Log and upload activity data"""
        if not (self.config.get('enable_keystroke_logging') or 
                self.config.get('enable_mouse_logging')):
            return
        
        try:
            current_time = datetime.now()
            
            with self.activity_lock:
                activity_data = {
                    "timestamp_start": self.last_activity_log.isoformat(),
                    "timestamp_end": current_time.isoformat(),
                    "application_name": self.get_active_window_title(),
                    "window_title": self.get_active_window_title(),
                    "url": None,  # Could be implemented for browser detection
                    "keystrokes": self.keystroke_count if self.config.get('enable_keystroke_logging') else 0,
                    "mouse_clicks": self.mouse_click_count if self.config.get('enable_mouse_logging') else 0
                }
                
                # Reset counters
                self.keystroke_count = 0
                self.mouse_click_count = 0
                self.last_activity_log = current_time
            
            # Upload to server
            self.upload_activity(activity_data)
            
        except Exception as e:
            self.logger.error(f"Error logging activity: {e}")
    
    def upload_activity(self, activity_data):
        """Upload activity data to server"""
        try:
            headers = self.get_auth_headers()
            if not headers:
                return False
            
            headers['Content-Type'] = 'application/json'
            url = f"{self.config['server_url']}{self.config['api_base_path']}log-activity/"
            
            response = requests.post(url, json=activity_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.debug("Activity logged successfully")
                return True
            else:
                self.logger.error(f"Activity logging failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error uploading activity: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat/status update to server"""
        try:
            headers = self.get_auth_headers()
            if not headers:
                return False
            
            headers['Content-Type'] = 'application/json'
            url = f"{self.config['server_url']}{self.config['api_base_path']}update-status/"
            
            status_data = {
                "status": "running",
                "agent_version": AGENT_VERSION,
                "os_info": f"{platform.system()} {platform.release()}"
            }
            
            response = requests.post(url, json=status_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.logger.debug("Heartbeat sent successfully")
                return True
            else:
                self.logger.error(f"Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            return False
    
    def on_key_press(self, key):
        """Keyboard event handler"""
        if self.config.get('enable_keystroke_logging'):
            with self.activity_lock:
                self.keystroke_count += 1
    
    def on_mouse_click(self, x, y, button, pressed):
        """Mouse event handler"""
        if pressed and self.config.get('enable_mouse_logging'):
            with self.activity_lock:
                self.mouse_click_count += 1
    
    def start_input_listeners(self):
        """Start keyboard and mouse listeners"""
        if not PYNPUT_AVAILABLE:
            self.logger.warning("pynput not available, input monitoring disabled")
            return
        
        try:
            if self.config.get('enable_keystroke_logging'):
                self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
                self.keyboard_listener.start()
                self.logger.info("Keyboard listener started")
            
            if self.config.get('enable_mouse_logging'):
                self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
                self.mouse_listener.start()
                self.logger.info("Mouse listener started")
                
        except Exception as e:
            self.logger.error(f"Error starting input listeners: {e}")
    
    def stop_input_listeners(self):
        """Stop keyboard and mouse listeners"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        self.logger.info("Input listeners stopped")
    
    def setup_schedules(self):
        """Setup scheduled tasks"""
        # Screenshot capture
        if self.config.get('enable_screenshot_capture'):
            schedule.every(self.config['screenshot_interval_seconds']).seconds.do(
                self.capture_screenshot
            )
        
        # Activity logging
        if (self.config.get('enable_keystroke_logging') or 
            self.config.get('enable_mouse_logging')):
            schedule.every(self.config['activity_log_interval_seconds']).seconds.do(
                self.log_activity
            )
        
        # Heartbeat
        schedule.every(300).seconds.do(self.send_heartbeat)  # Every 5 minutes
        
        # Settings refresh
        schedule.every(3600).seconds.do(self.fetch_settings_from_server)  # Every hour
    
    def scheduler_thread(self):
        """Thread function for running scheduled tasks"""
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def show_gui_prompt(self, title, message):
        """Show GUI prompt using tkinter"""
        try:
            import tkinter as tk
            from tkinter import simpledialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            result = simpledialog.askstring(title, message, parent=root)
            root.destroy()
            
            return result.strip() if result else None
            
        except ImportError:
            self.logger.error("tkinter not available for GUI prompt")
            return None
        except Exception as e:
            self.logger.error(f"GUI prompt error: {e}")
            return None
    
    def show_gui_message(self, title, message, msg_type="info"):
        """Show GUI message using tkinter"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            if msg_type == "info":
                messagebox.showinfo(title, message, parent=root)
            elif msg_type == "warning":
                messagebox.showwarning(title, message, parent=root)
            elif msg_type == "error":
                messagebox.showerror(title, message, parent=root)
            
            root.destroy()
            
        except Exception as e:
            self.logger.error(f"GUI message error: {e}")
    
    def initial_setup(self):
        """Handle initial setup and pairing"""
        if not self.config.get('first_run_complete') or not self.config.get('agent_token'):
            self.logger.info("Starting initial setup")
            
            pairing_code = self.show_gui_prompt(
                "Agent Setup",
                "Please enter the pairing code from your web dashboard:"
            )
            
            if not pairing_code:
                self.logger.error("No pairing code provided")
                self.show_gui_message(
                    "Setup Error",
                    "Pairing code is required. Agent will exit.",
                    "error"
                )
                return False
            
            if self.pair_with_server(pairing_code):
                self.show_gui_message(
                    "Setup Complete",
                    "Agent successfully paired with server. Monitoring will begin.",
                    "info"
                )
                return True
            else:
                self.show_gui_message(
                    "Setup Failed",
                    "Failed to pair with server. Please check the pairing code and try again.",
                    "error"
                )
                return False
        
        return True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating shutdown")
        
        # Set stop event
        self.stop_event.set()
        
        # Stop input listeners
        self.stop_input_listeners()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.logger.info("Agent shutdown complete")
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        self.logger.info("Starting Desktop Monitoring Agent")
        
        # Initial setup if needed
        if not self.initial_setup():
            sys.exit(1)
        
        # Fetch initial settings
        if not self.fetch_settings_from_server():
            self.logger.warning("Failed to fetch initial settings, using defaults")
        
        # Check if monitoring is active
        if not self.config.get('monitoring_active'):
            self.logger.info("Monitoring is disabled by server settings")
            return
        
        # Start input listeners
        self.start_input_listeners()
        
        # Setup scheduled tasks
        self.setup_schedules()
        
        # Start scheduler thread
        scheduler = threading.Thread(target=self.scheduler_thread, daemon=True)
        scheduler.start()
        self.threads.append(scheduler)
        
        # Show monitoring notification
        self.show_gui_message(
            "Monitoring Active",
            "Desktop monitoring is now active as per company policy.",
            "info"
        )
        
        self.logger.info("Agent fully initialized and running")
        
        # Main loop
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()

def main():
    """Main entry point"""
    agent = DesktopAgent()
    agent.run()

if __name__ == "__main__":
    main()
