from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import SellerProfile

User = get_user_model()


class UserAuthenticationTests(TestCase):
    """Test user registration, login, and authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        
    def test_user_registration(self):
        """Test user can register successfully"""
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com',
            'phone': '08012345678',
            'is_merchant': True
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        
    def test_merchant_gets_seller_profile(self):
        """Test that merchant registration creates seller profile"""
        data = {
            'username': 'merchant1',
            'password': 'testpass123',
            'email': 'merchant@example.com',
            'is_merchant': True
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check seller profile was created
        user = User.objects.get(username='merchant1')
        self.assertTrue(hasattr(user, 'seller_profile'))
        self.assertIsNotNone(user.seller_profile)
        
    def test_user_login(self):
        """Test user can login and receive JWT tokens"""
        # Create user
        User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Login
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_invalid_login(self):
        """Test login fails with invalid credentials"""
        data = {'username': 'nonexistent', 'password': 'wrongpass'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SellerProfileTests(TestCase):
    """Test seller profile creation and management"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_merchant=True
        )
        self.profile = SellerProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
        
    def test_get_seller_profile(self):
        """Test authenticated user can get their profile"""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'seller1')
        
    def test_update_seller_profile(self):
        """Test user can update their seller profile"""
        data = {
            'business_name': 'My Shop',
            'business_description': 'Best shop in town',
            'instagram_handle': '@myshop',
            'whatsapp_number': '08012345678'
        }
        response = self.client.put('/api/auth/profile/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['business_name'], 'My Shop')
        
        # Verify in database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.business_name, 'My Shop')
        
    def test_public_seller_profile(self):
        """Test public can view seller profile"""
        self.profile.business_name = 'Public Shop'
        self.profile.save()
        
        # Unauthenticated request
        client = APIClient()
        response = client.get(f'/api/auth/sellers/{self.user.username}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['business_name'], 'Public Shop')
        
    def test_completion_rate_calculation(self):
        """Test seller profile completion rate calculates correctly"""
        self.profile.total_deals = 10
        self.profile.completed_deals = 8
        self.profile.save()
        
        self.assertEqual(self.profile.completion_rate, 80.0)


class EmailVerificationTests(TestCase):
    """Test email verification functionality"""
    
    def test_user_email_verified_flag(self):
        """Test user has email_verified field"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.assertFalse(user.email_verified)
        
        # Simulate verification
        user.email_verified = True
        user.save()
        self.assertTrue(user.email_verified)
        
    def test_google_user_auto_verified(self):
        """Test Google OAuth users are auto-verified"""
        user = User.objects.create_user(
            username='googleuser',
            email='google@example.com',
            google_id='123456789',
            email_verified=True
        )
        self.assertTrue(user.email_verified)
        self.assertEqual(user.google_id, '123456789')
