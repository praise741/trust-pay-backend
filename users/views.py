from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSerializer, SellerProfileSerializer, PublicSellerProfileSerializer
from .models import SellerProfile

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class SellerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's seller profile"""
        try:
            profile = SellerProfile.objects.get(user=request.user)
            serializer = SellerProfileSerializer(profile)
            return Response(serializer.data)
        except SellerProfile.DoesNotExist:
            return Response(
                {'error': 'Seller profile not found. Are you registered as a merchant?'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Update current user's seller profile"""
        try:
            profile = SellerProfile.objects.get(user=request.user)
        except SellerProfile.DoesNotExist:
            # Create profile if doesn't exist
            profile = SellerProfile.objects.create(user=request.user)
        
        serializer = SellerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PublicSellerProfileView(generics.RetrieveAPIView):
    """Public view of seller profile by username"""
    permission_classes = [AllowAny]
    serializer_class = PublicSellerProfileSerializer
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    queryset = SellerProfile.objects.all()
