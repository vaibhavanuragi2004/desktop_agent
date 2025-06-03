#!/usr/bin/env python3
"""
Simple web dashboard server for Desktop Monitoring System
Serves the HTML dashboard and provides basic API endpoints
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

# Add Django backend to path for database access
backend_dir = Path(__file__).parent / "monitoring_backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoring_backend.settings')
    try:
        import django
        django.setup()
        from django.contrib.auth.models import User
        from monitoring.models import MonitoringProfile, AgentStatus, Screenshot, ActivityLog, PairingToken
        DJANGO_AVAILABLE = True
    except Exception as e:
        print(f"Django not available: {e}")
        DJANGO_AVAILABLE = False
else:
    DJANGO_AVAILABLE = False

class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler for the dashboard"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # API endpoints
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard':
            # Serve the dashboard HTML
            self.serve_dashboard()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        try:
            with open('web_dashboard.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except FileNotFoundError:
            self.send_error(404, "Dashboard HTML file not found")
    
    def handle_api_request(self, parsed_path):
        """Handle API requests"""
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # Add CORS headers
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        try:
            if path == '/api/users':
                response = self.get_users()
            elif path == '/api/stats':
                response = self.get_dashboard_stats()
            elif path == '/api/activity':
                response = self.get_recent_activity()
            elif path == '/api/create-user' and self.command == 'POST':
                response = self.create_user()
            elif path == '/api/toggle-monitoring' and self.command == 'POST':
                response = self.toggle_monitoring()
            elif path == '/api/generate-token' and self.command == 'POST':
                response = self.generate_pairing_token()
            else:
                response = {'error': 'Endpoint not found'}
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def get_users(self):
        """Get list of users"""
        if not DJANGO_AVAILABLE:
            return self.get_mock_users()
        
        try:
            users = []
            for user in User.objects.all():
                # Get monitoring profile
                profile = getattr(user, 'monitoring_profile', None)
                
                # Get agent status
                status = getattr(user, 'agent_status', None)
                
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'monitoring_enabled': profile.monitoring_enabled if profile else False,
                    'status': 'online' if status and status.is_online() else 'offline',
                    'agent_version': status.agent_version if status else 'N/A',
                    'last_seen': status.last_seen.isoformat() if status else None
                }
                users.append(user_data)
            
            return {'users': users}
            
        except Exception as e:
            return {'error': f'Database error: {str(e)}'}
    
    def get_mock_users(self):
        """Get mock users when Django is not available"""
        return {
            'users': [
                {
                    'id': 1,
                    'username': 'john.doe',
                    'email': 'john@company.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'monitoring_enabled': True,
                    'status': 'online',
                    'agent_version': '2.0.0',
                    'last_seen': (datetime.now() - timedelta(minutes=2)).isoformat()
                },
                {
                    'id': 2,
                    'username': 'jane.smith',
                    'email': 'jane@company.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'monitoring_enabled': True,
                    'status': 'offline',
                    'agent_version': '2.0.0',
                    'last_seen': (datetime.now() - timedelta(minutes=15)).isoformat()
                }
            ]
        }
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        if not DJANGO_AVAILABLE:
            return self.get_mock_stats()
        
        try:
            total_users = User.objects.count()
            
            # Count online agents (last seen within 10 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=10)
            online_agents = AgentStatus.objects.filter(last_seen__gte=cutoff_time).count()
            
            # Count screenshots today
            today = datetime.now().date()
            screenshots_today = Screenshot.objects.filter(captured_at__date=today).count()
            
            # Count activity logs today
            activities_today = ActivityLog.objects.filter(timestamp_start__date=today).count()
            
            return {
                'total_users': total_users,
                'online_agents': online_agents,
                'screenshots_today': screenshots_today,
                'activities_logged': activities_today
            }
            
        except Exception as e:
            return {'error': f'Database error: {str(e)}'}
    
    def get_mock_stats(self):
        """Get mock statistics when Django is not available"""
        return {
            'total_users': 12,
            'online_agents': 8,
            'screenshots_today': 145,
            'activities_logged': 2341
        }
    
    def get_recent_activity(self):
        """Get recent activity"""
        if not DJANGO_AVAILABLE:
            return self.get_mock_activity()
        
        try:
            activities = []
            
            # Recent screenshots
            recent_screenshots = Screenshot.objects.select_related('user').order_by('-uploaded_at')[:5]
            for screenshot in recent_screenshots:
                activities.append({
                    'user': screenshot.user.username,
                    'action': 'Screenshot uploaded',
                    'timestamp': screenshot.uploaded_at.isoformat(),
                    'type': 'screenshot'
                })
            
            # Recent status changes
            recent_status = AgentStatus.objects.select_related('user').order_by('-last_seen')[:5]
            for status in recent_status:
                activities.append({
                    'user': status.user.username,
                    'action': f'Agent status: {status.status}',
                    'timestamp': status.last_seen.isoformat(),
                    'type': 'status'
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {'activities': activities[:10]}  # Return latest 10
            
        except Exception as e:
            return {'error': f'Database error: {str(e)}'}
    
    def get_mock_activity(self):
        """Get mock activity when Django is not available"""
        return {
            'activities': [
                {
                    'user': 'john.doe',
                    'action': 'Screenshot uploaded',
                    'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'type': 'screenshot'
                },
                {
                    'user': 'jane.smith',
                    'action': 'Agent went offline',
                    'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                    'type': 'status'
                }
            ]
        }
    
    def create_user(self):
        """Create a new user"""
        if not DJANGO_AVAILABLE:
            return {'error': 'Django backend not available'}
        
        try:
            # Read POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            user_data = json.loads(post_data.decode('utf-8'))
            
            # Create user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data.get('email', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                password=user_data['password']
            )
            
            return {'success': True, 'user_id': user.id}
            
        except Exception as e:
            return {'error': f'Failed to create user: {str(e)}'}
    
    def toggle_monitoring(self):
        """Toggle monitoring for a user"""
        if not DJANGO_AVAILABLE:
            return {'error': 'Django backend not available'}
        
        try:
            # Read POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data['user_id']
            enabled = data['enabled']
            
            user = User.objects.get(id=user_id)
            profile = user.monitoring_profile
            profile.monitoring_enabled = enabled
            profile.save()
            
            return {'success': True}
            
        except Exception as e:
            return {'error': f'Failed to toggle monitoring: {str(e)}'}
    
    def generate_pairing_token(self):
        """Generate a pairing token for a user"""
        if not DJANGO_AVAILABLE:
            return {'error': 'Django backend not available'}
        
        try:
            # Read POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data['user_id']
            user = User.objects.get(id=user_id)
            
            # Create pairing token
            pairing_token = PairingToken.objects.create(user=user)
            
            return {
                'success': True,
                'token': pairing_token.token,
                'expires_at': pairing_token.expires_at.isoformat()
            }
            
        except Exception as e:
            return {'error': f'Failed to generate token: {str(e)}'}

def run_dashboard_server(port=5000):
    """Run the dashboard server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"Desktop Monitoring Dashboard Server")
    print(f"Server running on http://localhost:{port}")
    print(f"Dashboard URL: http://localhost:{port}/dashboard")
    
    if DJANGO_AVAILABLE:
        print("Django backend: Connected")
    else:
        print("Django backend: Not available (using mock data)")
    
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard server...")
        httpd.shutdown()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Desktop Monitoring Dashboard Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on (default: 5000)')
    parser.add_argument('--check-django', action='store_true', help='Check Django backend connection')
    
    args = parser.parse_args()
    
    if args.check_django:
        if DJANGO_AVAILABLE:
            print("Django backend is available and configured correctly")
            try:
                user_count = User.objects.count()
                print(f"Found {user_count} users in database")
            except Exception as e:
                print(f"Database error: {e}")
        else:
            print("Django backend is not available")
        return
    
    # Run the dashboard server
    run_dashboard_server(args.port)

if __name__ == "__main__":
    main()
