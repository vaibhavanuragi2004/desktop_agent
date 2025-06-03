"""
Database models for the monitoring application
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import secrets


class MonitoringProfile(models.Model):
    """Extended user profile for monitoring settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='monitoring_profile')
    
    # Monitoring settings
    screenshot_interval_seconds = models.IntegerField(default=300)  # 5 minutes
    activity_log_interval_seconds = models.IntegerField(default=60)  # 1 minute
    enable_screenshot_capture = models.BooleanField(default=True)
    enable_keystroke_logging = models.BooleanField(default=True)
    enable_mouse_logging = models.BooleanField(default=True)
    
    # Administrative settings
    monitoring_enabled = models.BooleanField(default=True)
    admin_access_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Monitoring Profile - {self.user.username}"
    
    class Meta:
        verbose_name = "Monitoring Profile"
        verbose_name_plural = "Monitoring Profiles"


class PairingToken(models.Model):
    """Temporary tokens for agent pairing"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pairing_tokens')
    token = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Generate a random 8-character alphanumeric token"""
        return secrets.token_urlsafe(6)[:8].upper()
    
    def is_valid(self):
        """Check if token is still valid"""
        return not self.used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Pairing Token - {self.token} ({self.user.username})"
    
    class Meta:
        verbose_name = "Pairing Token"
        verbose_name_plural = "Pairing Tokens"


class AgentToken(models.Model):
    """Long-lived tokens for agent authentication"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_tokens')
    token = models.CharField(max_length=128, unique=True)
    device_info = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(64)
    
    def __str__(self):
        return f"Agent Token - {self.user.username} ({self.token[:8]}...)"
    
    class Meta:
        verbose_name = "Agent Token"
        verbose_name_plural = "Agent Tokens"


class AgentStatus(models.Model):
    """Track agent status and heartbeats"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_status')
    agent_token = models.ForeignKey(AgentToken, on_delete=models.CASCADE, related_name='status')
    
    status = models.CharField(max_length=50, default='unknown')
    agent_version = models.CharField(max_length=50, blank=True)
    os_info = models.CharField(max_length=200, blank=True)
    
    last_seen = models.DateTimeField(auto_now=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    
    def is_online(self):
        """Check if agent is considered online (last seen within 10 minutes)"""
        cutoff = timezone.now() - timezone.timedelta(minutes=10)
        return self.last_seen > cutoff
    
    def __str__(self):
        return f"Agent Status - {self.user.username} ({self.status})"
    
    class Meta:
        verbose_name = "Agent Status"
        verbose_name_plural = "Agent Statuses"


class Screenshot(models.Model):
    """Store screenshot data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='screenshots')
    agent_token = models.ForeignKey(AgentToken, on_delete=models.CASCADE, related_name='screenshots')
    
    image = models.ImageField(upload_to='screenshots/%Y/%m/%d/')
    active_window_title = models.CharField(max_length=500, blank=True)
    
    captured_at = models.DateTimeField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # File metadata
    file_size = models.PositiveIntegerField(null=True, blank=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.image and not self.file_size:
            self.file_size = self.image.size
            
        # Get image dimensions if available
        if self.image and hasattr(self.image, 'width') and hasattr(self.image, 'height'):
            self.image_width = self.image.width
            self.image_height = self.image.height
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Screenshot - {self.user.username} at {self.captured_at}"
    
    class Meta:
        verbose_name = "Screenshot"
        verbose_name_plural = "Screenshots"
        ordering = ['-captured_at']


class ActivityLog(models.Model):
    """Store activity log data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    agent_token = models.ForeignKey(AgentToken, on_delete=models.CASCADE, related_name='activity_logs')
    
    timestamp_start = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    
    application_name = models.CharField(max_length=300, blank=True)
    window_title = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=1000, blank=True, null=True)
    
    keystrokes = models.PositiveIntegerField(default=0)
    mouse_clicks = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def duration_seconds(self):
        """Calculate duration of the activity log in seconds"""
        return (self.timestamp_end - self.timestamp_start).total_seconds()
    
    def __str__(self):
        return f"Activity - {self.user.username} ({self.timestamp_start} - {self.timestamp_end})"
    
    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ['-timestamp_start']


# Signal handlers to create related objects
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_monitoring_profile(sender, instance, created, **kwargs):
    """Create monitoring profile when user is created"""
    if created:
        MonitoringProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_monitoring_profile(sender, instance, **kwargs):
    """Save monitoring profile when user is saved"""
    if hasattr(instance, 'monitoring_profile'):
        instance.monitoring_profile.save()
