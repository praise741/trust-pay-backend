from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from deals.models import Deal

User = get_user_model()


class BuyerDashboardTests(TestCase):
    """Test buyer dashboard functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com'
        )
        
        # Create test deals for buyer
        self.buyer_email = 'buyer@example.com'
        
        Deal.objects.create(
            seller=self.seller,
            slug='deal-1',
            item_description='Item 1',
            amount=Decimal('1000.00'),
            buyer_email=self.buyer_email,
            status='COMPLETED'
        )
        Deal.objects.create(
            seller=self.seller,
            slug='deal-2',
            item_description='Item 2',
            amount=Decimal('2000.00'),
            buyer_email=self.buyer_email,
            status='SHIPPED'
        )
        Deal.objects.create(
            seller=self.seller,
            slug='deal-3',
            item_description='Item 3',
            amount=Decimal('3000.00'),
            buyer_email=self.buyer_email,
            status='DISPUTED'
        )
        
    def test_buyer_dashboard_by_email(self):
        """Test buyer can view dashboard by email"""
        data = {'email': self.buyer_email}
        response = self.client.post('/api/buyer/dashboard/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.buyer_email)
        self.assertEqual(response.data['total_orders'], 3)
        self.assertEqual(response.data['completed_orders'], 1)
        self.assertEqual(response.data['pending_orders'], 1)  # SHIPPED
        self.assertEqual(response.data['disputed_orders'], 1)
        self.assertEqual(len(response.data['orders']), 3)
        
    def test_buyer_dashboard_no_orders(self):
        """Test buyer dashboard with no orders"""
        data = {'email': 'noorders@example.com'}
        response = self.client.post('/api/buyer/dashboard/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 0)
        self.assertEqual(len(response.data['orders']), 0)
        
    def test_buyer_dashboard_missing_email(self):
        """Test buyer dashboard requires email"""
        response = self.client.post('/api/buyer/dashboard/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
    def test_buyer_order_detail(self):
        """Test buyer can view order details"""
        response = self.client.get('/api/buyer/orders/deal-1/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'deal-1')
        self.assertEqual(response.data['item_description'], 'Item 1')
        
    def test_buyer_orders_by_phone(self):
        """Test buyer can lookup orders by phone"""
        buyer_phone = '08012345678'
        
        Deal.objects.create(
            seller=self.seller,
            slug='deal-phone-1',
            item_description='Phone Order',
            amount=Decimal('5000.00'),
            buyer_phone=buyer_phone
        )
        
        data = {'phone': buyer_phone}
        response = self.client.post('/api/buyer/orders-by-phone/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], buyer_phone)
        self.assertEqual(response.data['total_orders'], 1)


class OrderTrackingTests(TestCase):
    """Test order tracking functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com'
        )
        
        self.deal = Deal.objects.create(
            seller=self.seller,
            slug='tracked-deal',
            item_description='Tracked Item',
            amount=Decimal('5000.00'),
            buyer_email='buyer@example.com',
            buyer_name='John Doe',
            delivery_address='123 Main St, Lagos',
            tracking_number='TRK123456',
            status='SHIPPED'
        )
        
    def test_get_tracking_info(self):
        """Test buyer can get tracking information"""
        response = self.client.get(f'/api/buyer/orders/{self.deal.slug}/tracking/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tracking_number'], 'TRK123456')
        self.assertEqual(response.data['delivery_address'], '123 Main St, Lagos')
        self.assertIn('status_display', response.data)
        self.assertIn('can_confirm', response.data)
        self.assertIn('can_dispute', response.data)
        
    def test_tracking_status_display(self):
        """Test tracking info shows human-readable status"""
        response = self.client.get(f'/api/buyer/orders/{self.deal.slug}/tracking/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status_display'], 'Shipped - In Transit')
        
    def test_can_confirm_flag(self):
        """Test can_confirm flag is correct"""
        response = self.client.get(f'/api/buyer/orders/{self.deal.slug}/tracking/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['can_confirm'])
        
    def test_can_dispute_flag(self):
        """Test can_dispute flag is correct"""
        response = self.client.get(f'/api/buyer/orders/{self.deal.slug}/tracking/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['can_dispute'])


class TrackingNumberUpdateTests(TestCase):
    """Test tracking number update functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com'
        )
        self.client.force_authenticate(user=self.seller)
        
        self.deal = Deal.objects.create(
            seller=self.seller,
            slug='update-tracking-deal',
            item_description='Test Item',
            amount=Decimal('5000.00'),
            status='SHIPPED'
        )
        
    def test_update_tracking_number(self):
        """Test seller can update tracking number"""
        data = {'tracking_number': 'NEW-TRK-789'}
        response = self.client.put(f'/api/deals/{self.deal.slug}/tracking/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tracking_number'], 'NEW-TRK-789')
        
        # Verify in database
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.tracking_number, 'NEW-TRK-789')
        
    def test_update_tracking_requires_auth(self):
        """Test updating tracking requires authentication"""
        client = APIClient()
        data = {'tracking_number': 'NEW-TRK-789'}
        response = client.put(f'/api/deals/{self.deal.slug}/tracking/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_update_tracking_only_seller(self):
        """Test only seller can update tracking"""
        other_user = User.objects.create_user(
            username='other',
            password='testpass123',
            email='other@example.com'
        )
        client = APIClient()
        client.force_authenticate(user=other_user)
        
        data = {'tracking_number': 'NEW-TRK-789'}
        response = client.put(f'/api/deals/{self.deal.slug}/tracking/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_update_tracking_requires_number(self):
        """Test updating tracking requires tracking number"""
        response = self.client.put(f'/api/deals/{self.deal.slug}/tracking/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
