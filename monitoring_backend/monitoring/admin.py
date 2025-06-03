"""
Django admin configuration for the monitoring app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    MonitoringProfile, PairingToken, AgentToken,
    AgentStatus, Screenshot, ActivityLog
)


@admin.register(MonitoringProfile)
class MonitoringProfileAdmin(admin.ModelAdmin):
    """Admin interface for monitoring profiles"""
    list_display = [
        'user', 'monitoring_enabled', 'admin_access_active',
        'enable_screenshot_capture', 'enable_keystroke_logging',
        'enable_mouse_logging', 'updated_at'
    ]
    list_filter = [
        'monitoring_enabled', 'admin_access_active',
        'enable_screenshot_capture', 'enable_keystroke_logging',
        'enable_mouse_logging', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Monitoring Settings', {
            'fields': (
                'monitoring_enabled',
                'admin_access_active',
                'screenshot_interval_seconds',
                'activity_log_interval_seconds',
            )
        }),
        ('Feature Toggles', {
            'fields': (
                'enable_screenshot_capture',
                'enable_keystroke_logging',
                'enable_mouse_logging',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PairingToken)
class PairingTokenAdmin(admin.ModelAdmin):
    """Admin interface for pairing tokens"""
    list_display = ['token', 'user', 'created_at', 'expires_at', 'used', 'is_valid_display']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['token', 'user__username', 'user__email']
    readonly_fields = ['token', 'created_at', 'used_at']
    
    def is_valid_display(self, obj):
        """Display token validity status"""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')
    is_valid_display.short_description = 'Valid'
    
    actions = ['create_new_tokens']
    
    def create_new_tokens(self, request, queryset):
        """Create new tokens for selected users"""
        count = 0
        for token in queryset:
            if not token.is_valid():
                PairingToken.objects.create(user=token.user)
                count += 1
        
        self.message_user(request, f'{count} new pairing tokens created.')
    create_new_tokens.short_description = 'Create new tokens for selected users'


@admin.register(AgentToken)
class AgentTokenAdmin(admin.ModelAdmin):
    """Admin interface for agent tokens"""
    list_display = ['token_display', 'user', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at', 'last_used']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['token', 'created_at', 'last_used', 'device_info_display']
    
    def token_display(self, obj):
        """Display truncated token"""
        return f"{obj.token[:8]}..."
    token_display.short_description = 'Token'
    
    def device_info_display(self, obj):
        """Display formatted device info"""
        if obj.device_info:
            info_lines = []
            for key, value in obj.device_info.items():
                info_lines.append(f"{key}: {value}")
            return format_html("<br>".join(info_lines))
        return "No device info"
    device_info_display.short_description = 'Device Information'
    
    fieldsets = (
        ('Token Information', {
            'fields': ('user', 'token', 'is_active')
        }),
        ('Device Information', {
            'fields': ('device_info_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AgentStatus)
class AgentStatusAdmin(admin.ModelAdmin):
    """Admin interface for agent status"""
    list_display = ['user', 'status', 'agent_version', 'os_info', 'is_online_display', 'last_seen']
    list_filter = ['status', 'first_seen', 'last_seen']
    search_fields = ['user__username', 'user__email', 'agent_version', 'os_info']
    readonly_fields = ['first_seen', 'last_seen']
    
    def is_online_display(self, obj):
        """Display online status"""
        if obj.is_online():
            return format_html('<span style="color: green;">● Online</span>')
        else:
            return format_html('<span style="color: red;">● Offline</span>')
    is_online_display.short_description = 'Status'


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    """Admin interface for screenshots"""
    list_display = ['id', 'user', 'active_window_title', 'captured_at', 'uploaded_at', 'file_size_display']
    list_filter = ['captured_at', 'uploaded_at', 'user']
    search_fields = ['user__username', 'active_window_title']
    readonly_fields = ['uploaded_at', 'file_size', 'image_width', 'image_height', 'image_preview']
    date_hierarchy = 'captured_at'
    
    def file_size_display(self, obj):
        """Display formatted file size"""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'
    
    fieldsets = (
        ('Screenshot Information', {
            'fields': ('user', 'agent_token', 'image', 'image_preview')
        }),
        ('Metadata', {
            'fields': ('active_window_title', 'captured_at', 'uploaded_at')
        }),
        ('File Information', {
            'fields': ('file_size', 'image_width', 'image_height'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for activity logs"""
    list_display = [
        'id', 'user', 'timestamp_start', 'timestamp_end',
        'application_name', 'keystrokes', 'mouse_clicks', 'duration_display'
    ]
    list_filter = ['timestamp_start', 'user', 'created_at']
    search_fields = ['user__username', 'application_name', 'window_title', 'url']
    readonly_fields = ['created_at', 'duration_display']
    date_hierarchy = 'timestamp_start'
    
    def duration_display(self, obj):
        """Display formatted duration"""
        duration = obj.duration_seconds
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    duration_display.short_description = 'Duration'
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'agent_token', 'timestamp_start', 'timestamp_end', 'duration_display')
        }),
        ('Application Details', {
            'fields': ('application_name', 'window_title', 'url')
        }),
        ('Activity Counts', {
            'fields': ('keystrokes', 'mouse_clicks')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "Desktop Monitoring Administration"
admin.site.site_title = "Desktop Monitoring Admin"
admin.site.index_title = "Welcome to Desktop Monitoring Administration"
