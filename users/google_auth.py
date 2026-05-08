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
import os

User = get_user_model()
logger = logging.getLogger(__name__)


def validate_token_format(token):
    """
    Validate that token has the correct JWT format (3 parts separated by dots).
    Returns: (is_valid, error_message)
    """
    if not isinstance(token, str):
        return False, "Token must be a string"
    
    parts = token.split('.')
    if len(parts) != 3:
        return False, f"Invalid token format. Expected 3 parts separated by dots, got {len(parts)}"
    
    # Check each part is not empty
    for i, part in enumerate(parts):
        if not part:
            return False, f"Token part {i+1} is empty"
    
    return True, None


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Google OAuth login endpoint
    Expects: { "token": "google_id_token", "user_type": "buyer|seller" } or { "credential": "google_id_token", "user_type": "buyer|seller" }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    # Support both 'token' and 'credential' keys (different Google libraries use different keys)
    token = request.data.get('token') or request.data.get('credential')
    user_type = request.data.get('user_type', 'buyer')  # Default to buyer if not specified
    
    if not token:
        logger.error("No token provided in request")
        return Response(
            {
                'error': 'Google token is required',
                'detail': 'Please provide either "token" or "credential" in request body with a valid Google ID token'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate token format first
    is_valid, error_msg = validate_token_format(token)
    if not is_valid:
        logger.error(f"Invalid token format: {error_msg}")
        return Response(
            {
                'error': 'Invalid token format',
                'detail': error_msg + '. Please provide a valid Google ID token from Google OAuth.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get client ID from settings
        client_id = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('client_id')
        
        if not client_id:
            logger.error("GOOGLE_CLIENT_ID not configured")
            return Response(
                {
                    'error': 'Google OAuth not configured on server',
                    'detail': 'GOOGLE_CLIENT_ID environment variable is not set. Please contact support.'
                },
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
        
        # Determine intended merchant status
        is_merchant_intended = user_type == 'seller'
        
        if not user:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # Link Google account to existing user
                logger.info(f"Linking Google account to existing user: {email}")
                user.google_id = google_id
                user.email_verified = True
                # If they intended to be a seller and aren't yet, update them
                if is_merchant_intended and not user.is_merchant:
                    user.is_merchant = True
                    # Create seller profile if it doesn't exist
                    if not hasattr(user, 'seller_profile'):
                        from .models import SellerProfile
                        SellerProfile.objects.get_or_create(user=user)
                user.save()
            else:
                # Create new user
                logger.info(f"Creating new user for: {email} with user_type: {user_type}")
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
                    is_merchant=is_merchant_intended,
                )
                user.set_unusable_password()
                user.save()
                
                # Create seller profile if merchant
                if is_merchant_intended:
                    from .models import SellerProfile
                    SellerProfile.objects.get_or_create(user=user)
                
                logger.info(f"New user created: {username} as {'seller' if is_merchant_intended else 'buyer'}")
        else:
            # User exists by Google ID, update merchant status if needed
            if is_merchant_intended and not user.is_merchant:
                user.is_merchant = True
                from .models import SellerProfile
                SellerProfile.objects.get_or_create(user=user)
                user.save()
                logger.info(f"Updated existing Google user {user.username} to merchant")
        
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
                'is_staff': user.is_staff,
                'email_verified': user.email_verified,
            }
        }
        
        logger.info(f"Login successful for: {email}")
        return Response(response_data)
        
    except ValueError as e:
        error_str = str(e)
        logger.error(f"Invalid Google token: {error_str}")
        return Response(
            {
                'error': 'Invalid Google token',
                'detail': f"{error_str}. Make sure you are sending a valid Google ID token, not a test token."
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}", exc_info=True)
        return Response(
            {
                'error': 'Authentication failed',
                'detail': f'An unexpected error occurred during authentication. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def google_config_check(request):
    """
    Debug endpoint to check if Google OAuth is configured
    """
    client_id = settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('APP', {}).get('client_id')
    
    return Response({
        'google_oauth_configured': bool(client_id),
        'client_id_preview': client_id[:20] + '...' if client_id else None,
        'message': 'Google OAuth is configured' if client_id else 'GOOGLE_CLIENT_ID environment variable is not set'
    })
