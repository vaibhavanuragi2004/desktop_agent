# Desktop Monitoring System

A comprehensive desktop monitoring solution consisting of a Python-based desktop agent and Django backend server for employee activity tracking and administrative oversight.

## Features

### Desktop Agent
- **Cross-platform compatibility** - Works on Windows, macOS, and Linux
- **Screenshot capture** - Periodic desktop screenshots with configurable intervals
- **Activity logging** - Tracks keystroke counts, mouse clicks, and application usage
- **Background operation** - Runs silently without user interference
- **Secure authentication** - Token-based authentication with pairing codes
- **Persistent operation** - Survives system restarts and user logouts
- **Remote configuration** - Settings managed from web dashboard

### Backend Server
- **Django REST API** - Secure endpoints for agent communication
- **User management** - Admin interface for user and agent management
- **Data storage** - Screenshots and activity logs with metadata
- **Real-time monitoring** - Agent status tracking and heartbeat monitoring
- **Access control** - Granular permissions and monitoring toggles

## Quick Start

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd monitoring_backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start development server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. **Access admin interface:**
   - Open http://localhost:8000/admin
   - Login with superuser credentials
   - Create user accounts and generate pairing tokens

### Agent Setup

#### For Development/Testing

1. **Install agent dependencies:**
   ```bash
   pip install -r requirements_agent.txt
   