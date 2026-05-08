from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from .models import SellerProfile

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Google OAuth login endpoint
    Expects: { "token": "google_id_token" }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'Google token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
        )
        
        # Get user info from Google
        google_id = idinfo['sub']
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        given_name = idinfo.get('given_name', '')
        
        if not email:
            return Response(
                {'error': 'Email not provided by Google'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists with this Google ID
        user = User.objects.filter(google_id=google_id).first()
        
        if not user:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.email_verified = True
                user.save()
            else:
                # Create new user
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
                    email_verified=True,
                )
                user.set_unusable_password()
                user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_merchant': user.is_merchant,
                'email_verified': user.email_verified,
            }
        })
        
    except ValueError as e:
        return Response(
            {'error': f'Invalid Google token: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Authentication failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
