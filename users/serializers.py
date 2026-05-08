from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SellerProfile

User = get_user_model()


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
                  'bank_account_number', 'bank_code', 'bank_account_name', 'is_merchant']
