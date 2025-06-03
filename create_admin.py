#!/usr/bin/env python3
"""
Quick admin user creation script for Django backend
"""

import os
import sys
import django
from pathlib import Path

# Add the monitoring_backend directory to the path
backend_dir = Path(__file__).parent / "monitoring_backend"
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoring_backend.settings')
django.setup()

from django.contrib.auth.models import User
from monitoring.models import MonitoringProfile, PairingToken

def create_admin_user():
    """Create admin user and setup initial data"""
    print("Desktop Monitoring System - Admin Setup")
    print("=" * 40)
    
    # Check if admin user already exists
    if User.objects.filter(is_superuser=True).exists():
        print("Admin user already exists!")
        admin_user = User.objects.filter(is_superuser=True).first()
        print(f"Existing admin: {admin_user.username}")
    else:
        # Create admin user
        print("Creating admin user...")
        username = input("Admin username (default: admin): ").strip() or "admin"
        email = input("Admin email: ").strip()
        
        while True:
            password = input("Admin password: ").strip()
            if len(password) >= 8:
                break
            print("Password must be at least 8 characters long")
        
        admin_user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"Admin user created: {username}")
    
    return admin_user

def create_test_user():
    """Create a test user for monitoring"""
    print("\nCreate a test user for monitoring? (y/n): ", end="")
    create_test = input().strip().lower()
    
    if create_test in ['y', 'yes']:
        username = input("Test user username (default: testuser): ").strip() or "testuser"
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            test_user = User.objects.get(username=username)
            print(f"Test user already exists: {username}")
        else:
            email = input("Test user email (optional): ").strip()
            password = input("Test user password (default: testpass123): ").strip() or "testpass123"
            
            test_user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            print(f"Test user created: {username}")
        
        # Create pairing token
        pairing_token = PairingToken.objects.create(user=test_user)
        print(f"Pairing token for {username}: {pairing_token.token}")
        print(f"Token expires: {pairing_token.expires_at}")
        
        return test_user
    
    return None

def display_setup_info(admin_user, test_user=None):
    """Display setup information"""
    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n1. Start the Django server:")
    print("   cd monitoring_backend")
    print("   python manage.py runserver 0.0.0.0:8000")
    
    print("\n2. Access the admin interface:")
    print("   URL: http://localhost:8000/admin")
    print(f"   Username: {admin_user.username}")
    print("   Password: [your admin password]")
    
    if test_user:
        print(f"\n3. Test user created:")
        print(f"   Username: {test_user.username}")
        
        # Get the latest pairing token
        latest_token = PairingToken.objects.filter(user=test_user).order_by('-created_at').first()
        if latest_token:
            print(f"   Pairing token: {latest_token.token}")
            print(f"   Token expires: {latest_token.expires_at}")
    
    print("\n4. To create more users and pairing tokens:")
    print("   - Use the admin interface")
    print("   - Or create users programmatically")
    
    print("\n5. Agent setup:")
    print("   - Build the desktop agent")
    print("   - Run it on target machines")
    print("   - Use the pairing token to connect")

def show_api_info():
    """Show API endpoint information"""
    print("\n" + "=" * 50)
    print("API ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("POST", "/api/v1/monitoring/pair-agent/", "Pair agent with server"),
        ("GET", "/api/v1/monitoring/get-settings/", "Get monitoring settings"),
        ("POST", "/api/v1/monitoring/upload-screenshot/", "Upload screenshot"),
        ("POST", "/api/v1/monitoring/log-activity/", "Log activity data"),
        ("POST", "/api/v1/monitoring/update-status/", "Update agent status"),
        ("POST", "/api/v1/monitoring/create-pairing-token/", "Create pairing token (admin)"),
        ("POST", "/api/v1/monitoring/toggle-monitoring/", "Toggle monitoring (admin)")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:40} - {description}")

def main():
    """Main function"""
    try:
        # Create admin user
        admin_user = create_admin_user()
        
        # Create test user
        test_user = create_test_user()
        
        # Display setup info
        display_setup_info(admin_user, test_user)
        
        # Show API info
        show_api_info()
        
        print("\nSetup completed successfully!")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
