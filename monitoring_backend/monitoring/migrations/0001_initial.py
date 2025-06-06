# Generated by Django 4.2.7 on 2024-01-01 12:00

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import monitoring.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=128, unique=True)),
                ('device_info', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agent Token',
                'verbose_name_plural': 'Agent Tokens',
            },
        ),
        migrations.CreateModel(
            name='MonitoringProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('screenshot_interval_seconds', models.IntegerField(default=300)),
                ('activity_log_interval_seconds', models.IntegerField(default=60)),
                ('enable_screenshot_capture', models.BooleanField(default=True)),
                ('enable_keystroke_logging', models.BooleanField(default=True)),
                ('enable_mouse_logging', models.BooleanField(default=True)),
                ('monitoring_enabled', models.BooleanField(default=True)),
                ('admin_access_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='monitoring_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Monitoring Profile',
                'verbose_name_plural': 'Monitoring Profiles',
            },
        ),
        migrations.CreateModel(
            name='PairingToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=32, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used', models.BooleanField(default=False)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pairing_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pairing Token',
                'verbose_name_plural': 'Pairing Tokens',
            },
        ),
        migrations.CreateModel(
            name='Screenshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='screenshots/%Y/%m/%d/')),
                ('active_window_title', models.CharField(blank=True, max_length=500)),
                ('captured_at', models.DateTimeField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('file_size', models.PositiveIntegerField(blank=True, null=True)),
                ('image_width', models.PositiveIntegerField(blank=True, null=True)),
                ('image_height', models.PositiveIntegerField(blank=True, null=True)),
                ('agent_token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenshots', to='monitoring.agenttoken')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screenshots', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Screenshot',
                'verbose_name_plural': 'Screenshots',
                'ordering': ['-captured_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='unknown', max_length=50)),
                ('agent_version', models.CharField(blank=True, max_length=50)),
                ('os_info', models.CharField(blank=True, max_length=200)),
                ('last_seen', models.DateTimeField(auto_now=True)),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('agent_token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status', to='monitoring.agenttoken')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_status', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agent Status',
                'verbose_name_plural': 'Agent Statuses',
            },
        ),
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp_start', models.DateTimeField()),
                ('timestamp_end', models.DateTimeField()),
                ('application_name', models.CharField(blank=True, max_length=300)),
                ('window_title', models.CharField(blank=True, max_length=500)),
                ('url', models.URLField(blank=True, max_length=1000, null=True)),
                ('keystrokes', models.PositiveIntegerField(default=0)),
                ('mouse_clicks', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('agent_token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='monitoring.agenttoken')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Activity Log',
                'verbose_name_plural': 'Activity Logs',
                'ordering': ['-timestamp_start'],
            },
        ),
    ]
