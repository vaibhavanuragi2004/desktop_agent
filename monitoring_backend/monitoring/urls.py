"""
URL patterns for the monitoring API
"""

from django.urls import path
from . import views

urlpatterns = [
    # Agent endpoints
    path('pair-agent/', views.pair_agent, name='pair_agent'),
    path('get-settings/', views.get_settings, name='get_settings'),
    path('upload-screenshot/', views.upload_screenshot, name='upload_screenshot'),
    path('log-activity/', views.log_activity, name='log_activity'),
    path('update-status/', views.update_status, name='update_status'),
    
    # Admin endpoints
    path('create-pairing-token/', views.create_pairing_token, name='create_pairing_token'),
    path('toggle-monitoring/', views.toggle_monitoring, name='toggle_monitoring'),
]
