"""
API views for the monitoring application
"""

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

from .models import (
    PairingToken, AgentToken, MonitoringProfile, 
    AgentStatus, Screenshot, ActivityLog
)
from .serializers import (
    PairingRequestSerializer, SettingsSerializer,
    ScreenshotUploadSerializer, ActivityLogSerializer,
    StatusUpdateSerializer
)
from .authentication import AgentTokenAuthentication

logger = logging.getLogger(__name__)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def pair_agent(request):
    """
    Pair an agent with a user account using a pairing token
    """
    serializer = PairingRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    pairing_token = serializer.validated_data['pairing_token']
    device_info = serializer.validated_data.get('device_info', {})
    
    try:
        # Find and validate the pairing token
        token_obj = PairingToken.objects.get(token=pairing_token)
        
        if not token_obj.is_valid():
            return Response(
                {'error': 'Pairing token has expired or been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark token as used
        token_obj.used = True
        token_obj.used_at = timezone.now()
        token_obj.save()
        
        # Create or get agent token
        agent_token, created = AgentToken.objects.get_or_create(
            user=token_obj.user,
            defaults={'device_info': device_info}
        )
        
        # Update device info if token already exists
        if not created:
            agent_token.device_info.update(device_info)
            agent_token.save()
        
        # Create or update agent status
        agent_status, _ = AgentStatus.objects.get_or_create(
            user=token_obj.user,
            defaults={
                'agent_token': agent_token,
                'status': 'paired',
                'agent_version': device_info.get('agent_version', ''),
                'os_info': f"{device_info.get('os', '')} {device_info.get('os_version', '')}".strip()
            }
        )
        
        logger.info(f"Agent paired successfully for user {token_obj.user.username}")
        
        return Response({
            'agent_token': agent_token.token,
            'user_pk': token_obj.user.pk
        }, status=status.HTTP_200_OK)
        
    except PairingToken.DoesNotExist:
        return Response(
            {'error': 'Invalid pairing token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error during agent pairing: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@authentication_classes([AgentTokenAuthentication])
@permission_classes([IsAuthenticated])
def get_settings(request):
    """
    Get monitoring settings for the authenticated agent
    """
    try:
        user = request.user
        profile = get_object_or_404(MonitoringProfile, user=user)
        
        # Check if admin access is active
        if not profile.admin_access_active:
            return Response(
                {'error': 'Admin access is not active for this user'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SettingsSerializer(profile)
        settings_data = serializer.data
        
        # Add user_pk to the response
        settings_data['user_pk'] = user.pk
        
        logger.info(f"Settings retrieved for user {user.username}")
        
        return Response(settings_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving settings for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve settings'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([AgentTokenAuthentication])
@permission_classes([IsAuthenticated])
def upload_screenshot(request):
    """
    Upload a screenshot from the agent
    """
    try:
        # Get the agent token from the request
        agent_token = getattr(request, 'agent_token', None)
        if not agent_token:
            return Response(
                {'error': 'Agent token not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if screenshot capture is enabled
        profile = get_object_or_404(MonitoringProfile, user=request.user)
        if not profile.enable_screenshot_capture or not profile.monitoring_enabled:
            return Response(
                {'error': 'Screenshot capture is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ScreenshotUploadSerializer(data=request.data, files=request.FILES)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid upload data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create screenshot record
        screenshot = Screenshot.objects.create(
            user=request.user,
            agent_token=agent_token,
            image=serializer.validated_data['image'],
            active_window_title=serializer.validated_data.get('active_window_title_at_capture', ''),
            captured_at=serializer.validated_data.get('captured_at', timezone.now())
        )
        
        logger.info(f"Screenshot uploaded for user {request.user.username}, ID: {screenshot.id}")
        
        return Response({
            'message': 'Screenshot uploaded successfully',
            'screenshot_id': screenshot.id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error uploading screenshot for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to upload screenshot'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([AgentTokenAuthentication])
@permission_classes([IsAuthenticated])
def log_activity(request):
    """
    Log activity data from the agent
    """
    try:
        # Get the agent token from the request
        agent_token = getattr(request, 'agent_token', None)
        if not agent_token:
            return Response(
                {'error': 'Agent token not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if activity logging is enabled
        profile = get_object_or_404(MonitoringProfile, user=request.user)
        if not profile.monitoring_enabled:
            return Response(
                {'error': 'Activity logging is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ActivityLogSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid activity data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter out data based on settings
        validated_data = serializer.validated_data
        
        if not profile.enable_keystroke_logging:
            validated_data['keystrokes'] = 0
        
        if not profile.enable_mouse_logging:
            validated_data['mouse_clicks'] = 0
        
        # Create activity log record
        activity_log = ActivityLog.objects.create(
            user=request.user,
            agent_token=agent_token,
            **validated_data
        )
        
        logger.debug(f"Activity logged for user {request.user.username}, ID: {activity_log.id}")
        
        return Response({
            'message': 'Activity logged successfully',
            'log_id': activity_log.id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error logging activity for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to log activity'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@authentication_classes([AgentTokenAuthentication])
@permission_classes([IsAuthenticated])
def update_status(request):
    """
    Update agent status/heartbeat
    """
    try:
        # Get the agent token from the request
        agent_token = getattr(request, 'agent_token', None)
        if not agent_token:
            return Response(
                {'error': 'Agent token not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = StatusUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid status data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update or create agent status
        agent_status, created = AgentStatus.objects.update_or_create(
            user=request.user,
            defaults={
                'agent_token': agent_token,
                'status': serializer.validated_data['status'],
                'agent_version': serializer.validated_data.get('agent_version', ''),
                'os_info': serializer.validated_data.get('os_info', ''),
                'last_seen': timezone.now()
            }
        )
        
        # Update agent token last_used timestamp
        agent_token.last_used = timezone.now()
        agent_token.save()
        
        logger.debug(f"Status updated for user {request.user.username}: {serializer.validated_data['status']}")
        
        return Response({
            'message': 'Agent status acknowledged',
            'server_time': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating status for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to update status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Additional admin API endpoints

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pairing_token(request):
    """
    Create a new pairing token for a user (admin endpoint)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_id = request.data.get('user_id')
    if not user_id:
        return Response(
            {'error': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
        
        # Create pairing token
        pairing_token = PairingToken.objects.create(user=user)
        
        logger.info(f"Pairing token created for user {user.username} by admin {request.user.username}")
        
        return Response({
            'pairing_token': pairing_token.token,
            'expires_at': pairing_token.expires_at.isoformat(),
            'user': user.username
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error creating pairing token: {str(e)}")
        return Response(
            {'error': 'Failed to create pairing token'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_monitoring(request):
    """
    Enable/disable monitoring for a user (admin endpoint)
    """
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_id = request.data.get('user_id')
    enabled = request.data.get('enabled')
    
    if user_id is None or enabled is None:
        return Response(
            {'error': 'user_id and enabled are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
        profile = get_object_or_404(MonitoringProfile, user=user)
        
        profile.monitoring_enabled = bool(enabled)
        profile.save()
        
        logger.info(f"Monitoring {'enabled' if enabled else 'disabled'} for user {user.username} by admin {request.user.username}")
        
        return Response({
            'message': f"Monitoring {'enabled' if enabled else 'disabled'} for user {user.username}",
            'user': user.username,
            'monitoring_enabled': profile.monitoring_enabled
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error toggling monitoring: {str(e)}")
        return Response(
            {'error': 'Failed to toggle monitoring'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
