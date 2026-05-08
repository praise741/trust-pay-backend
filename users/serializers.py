from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import SellerProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include user data and support email login"""
    
    def validate(self, attrs):
        # Allow login with email or username
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            # Check if username is actually an email
            if "@" in username:
                try:
                    user = User.objects.get(email=username)
                    attrs["username"] = user.username
                except User.DoesNotExist:
                    pass

        data = super().validate(attrs)
        
        # Add custom user data
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'phone': self.user.phone,
            'is_merchant': self.user.is_merchant,
            'is_staff': self.user.is_staff,
            'email_verified': self.user.email_verified,
        }
        
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'phone', 'bank_name',
                  'bank_account_number', 'bank_code', 'bank_account_name', 'is_merchant']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create seller profile if merchant
        if validated_data.get('is_merchant', False):
            SellerProfile.objects.create(user=user)
        
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'bank_name',
                  'bank_account_number', 'bank_code', 'bank_account_name', 'is_merchant', 'is_staff']


class SellerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = SellerProfile
        fields = '__all__'
        read_only_fields = ['total_deals', 'completed_deals', 'is_verified']


class PublicSellerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = SellerProfile
        fields = ['username', 'email', 'business_name', 'business_description',
                  'profile_photo', 'instagram_handle', 'whatsapp_number',
                  'twitter_handle', 'website_url', 'is_verified',
                  'total_deals', 'completed_deals', 'completion_rate']
