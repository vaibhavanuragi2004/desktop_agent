"""
Custom authentication classes for the monitoring API
"""

from django.contrib.auth.models import User
from rest_framework import authentication, exceptions
from .models import AgentToken


class AgentTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for agent tokens
    """
    keyword = 'AgentToken'
    
    def authenticate(self, request):
        """
        Authenticate using agent token
        """
        auth_header = authentication.get_authorization_header(request)
        
        if not auth_header:
            return None
        
        try:
            auth_parts = auth_header.decode('utf-8').split()
        except UnicodeDecodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise exceptions.AuthenticationFailed(msg)
        
        if not auth_parts or auth_parts[0].lower() != self.keyword.lower():
            return None
        
        if len(auth_parts) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_parts) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)
        
        try:
            token = auth_parts[1]
        except UnicodeDecodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise exceptions.AuthenticationFailed(msg)
        
        return self.authenticate_credentials(request, token)
    
    def authenticate_credentials(self, request, key):
        """
        Authenticate the token
        """
        try:
            agent_token = AgentToken.objects.select_related('user').get(
                token=key,
                is_active=True
            )
        except AgentToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token.')
        
        if not agent_token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')
        
        # Check if user has monitoring profile and admin access is active
        if hasattr(agent_token.user, 'monitoring_profile'):
            if not agent_token.user.monitoring_profile.admin_access_active:
                raise exceptions.AuthenticationFailed('Admin access is not active for this user.')
        
        # Store the agent token in the request for later use
        request.agent_token = agent_token
        
        return (agent_token.user, agent_token)
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        return self.keyword
