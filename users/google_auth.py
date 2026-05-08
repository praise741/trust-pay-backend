from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Google OAuth login endpoint
    Expects: { "token": "google_id_token" } or { "credential": "google_id_token" }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    # Support both 'token' and 'credential' keys (different Google libraries use different keys)
    token = request.data.get('token') or request.data.get('credential')
    
    if not token:
        logger.error("No token provided in request")
        return Response(
            {
                'error': 'Google token is required',
                'detail': 'Please provide either "token" or "credential" in request body'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get client ID from settings
        client_id = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('client_id')
        
        if not client_id:
            logger.error("GOOGLE_CLIENT_ID not configured")
            return Response(
                {'error': 'Google OAuth not configured on server'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"Verifying token with client_id: {client_id[:20]}...")
        
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            client_id
        )
        
        # Verify the token is for our app
        if idinfo['aud'] != client_id:
            logger.error("Token audience mismatch")
            return Response(
                {'error': 'Invalid token audience'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user info from Google
        google_id = idinfo['sub']
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        given_name = idinfo.get('given_name', '')
        family_name = idinfo.get('family_name', '')
        picture = idinfo.get('picture', '')
        
        if not email:
            logger.error("Email not provided by Google")
            return Response(
                {'error': 'Email not provided by Google'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Google auth successful for email: {email}")
        
        # Check if user exists with this Google ID
        user = User.objects.filter(google_id=google_id).first()
        
        if not user:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # Link Google account to existing user
                logger.info(f"Linking Google account to existing user: {email}")
                user.google_id = google_id
                user.email_verified = True
                user.save()
            else:
                # Create new user
                logger.info(f"Creating new user for: {email}")
                username = email.split('@')[0]
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    google_id=google_id,
                    first_name=given_name,
                    last_name=family_name,
                    email_verified=True,
                )
                user.set_unusable_password()
                user.save()
                
                logger.info(f"New user created: {username}")
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_merchant': user.is_merchant,
                'email_verified': user.email_verified,
            }
        }
        
        logger.info(f"Login successful for: {email}")
        return Response(response_data)
        
    except ValueError as e:
        logger.error(f"Invalid Google token: {str(e)}")
        return Response(
            {
                'error': 'Invalid Google token',
                'detail': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return Response(
            {
                'error': 'Authentication failed',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
