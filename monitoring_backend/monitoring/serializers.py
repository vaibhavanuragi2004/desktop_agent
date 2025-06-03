"""
Serializers for the monitoring API
"""

from rest_framework import serializers
from django.utils import timezone
from .models import MonitoringProfile, Screenshot, ActivityLog


class PairingRequestSerializer(serializers.Serializer):
    """Serializer for agent pairing requests"""
    pairing_token = serializers.CharField(max_length=32)
    device_info = serializers.JSONField(required=False, default=dict)


class SettingsSerializer(serializers.ModelSerializer):
    """Serializer for monitoring settings"""
    
    class Meta:
        model = MonitoringProfile
        fields = [
            'screenshot_interval_seconds',
            'activity_log_interval_seconds',
            'enable_screenshot_capture',
            'enable_keystroke_logging',
            'enable_mouse_logging',
            'monitoring_enabled',
            'admin_access_active'
        ]


class ScreenshotUploadSerializer(serializers.Serializer):
    """Serializer for screenshot uploads"""
    image = serializers.ImageField()
    active_window_title_at_capture = serializers.CharField(max_length=500, required=False, default='')
    captured_at = serializers.DateTimeField(required=False, default=timezone.now)
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Maximum size is 50MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise serializers.ValidationError("Unsupported image format. Use JPEG, PNG, GIF, or WebP.")
        
        return value


class ActivityLogSerializer(serializers.Serializer):
    """Serializer for activity log data"""
    timestamp_start = serializers.DateTimeField()
    timestamp_end = serializers.DateTimeField()
    application_name = serializers.CharField(max_length=300, required=False, default='')
    window_title = serializers.CharField(max_length=500, required=False, default='')
    url = serializers.URLField(max_length=1000, required=False, allow_null=True)
    keystrokes = serializers.IntegerField(min_value=0, default=0)
    mouse_clicks = serializers.IntegerField(min_value=0, default=0)
    
    def validate(self, data):
        """Validate activity log data"""
        if data['timestamp_end'] <= data['timestamp_start']:
            raise serializers.ValidationError("timestamp_end must be after timestamp_start")
        
        # Check duration (max 24 hours)
        duration = data['timestamp_end'] - data['timestamp_start']
        if duration.total_seconds() > 24 * 3600:
            raise serializers.ValidationError("Activity log duration cannot exceed 24 hours")
        
        return data


class StatusUpdateSerializer(serializers.Serializer):
    """Serializer for agent status updates"""
    status = serializers.CharField(max_length=50)
    agent_version = serializers.CharField(max_length=50, required=False, default='')
    os_info = serializers.CharField(max_length=200, required=False, default='')


class ScreenshotSerializer(serializers.ModelSerializer):
    """Serializer for screenshot data (for admin views)"""
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Screenshot
        fields = [
            'id', 'user', 'image', 'active_window_title',
            'captured_at', 'uploaded_at', 'file_size',
            'image_width', 'image_height'
        ]


class ActivityLogReadSerializer(serializers.ModelSerializer):
    """Serializer for activity log data (for admin views)"""
    user = serializers.StringRelatedField()
    duration_seconds = serializers.ReadOnlyField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'timestamp_start', 'timestamp_end',
            'application_name', 'window_title', 'url',
            'keystrokes', 'mouse_clicks', 'duration_seconds',
            'created_at'
        ]
