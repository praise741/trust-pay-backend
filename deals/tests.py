from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from decimal import Decimal
from .models import Deal, Transaction, Dispute

User = get_user_model()


class DealCreationTests(TestCase):
    """Test deal creation and basic operations"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_merchant=True,
            bank_name='GTBank',
            bank_account_number='0123456789',
            bank_code='058'
        )
        self.client.force_authenticate(user=self.seller)
        
    def test_create_deal(self):
        """Test seller can create a deal"""
        data = {
            'item_description': 'iPhone 15 Pro',
            'amount': '850000.00',
            'delivery_days': 3,
            'buyer_email': 'buyer@example.com',
            'buyer_phone': '08098765432'
        }
        response = self.client.post('/api/deals/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['item_description'], 'iPhone 15 Pro')
        self.assertEqual(response.data['status'], 'PENDING_PAYMENT')
        self.assertIsNotNone(response.data['slug'])
        
    def test_create_deal_with_new_fields(self):
        """Test deal creation with buyer_name, delivery_address, tracking_number"""
        data = {
            'item_description': 'Architecture Book',
            'amount': '5000.00',
            'delivery_days': 3,
            'buyer_email': 'maxwell@example.com',
            'buyer_phone': '08098765432',
            'buyer_name': 'Maxwell Okafor',
            'delivery_address': '123 Main Street, Victoria Island, Lagos'
        }
        response = self.client.post('/api/deals/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['buyer_name'], 'Maxwell Okafor')
        self.assertEqual(response.data['delivery_address'], '123 Main Street, Victoria Island, Lagos')
        
    def test_list_deals(self):
        """Test seller can list their deals"""
        Deal.objects.create(
            seller=self.seller,
            slug='test-deal-1',
            item_description='Test Item',
            amount=Decimal('1000.00')
        )
        
        response = self.client.get('/api/deals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_get_deal_detail(self):
        """Test can retrieve deal details"""
        deal = Deal.objects.create(
            seller=self.seller,
            slug='test-deal-1',
            item_description='Test Item',
            amount=Decimal('1000.00')
        )
        
        response = self.client.get(f'/api/deals/{deal.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], 'test-deal-1')


class DealLifecycleTests(TestCase):
    """Test complete deal lifecycle"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_merchant=True,
            bank_name='GTBank',
            bank_account_number='0123456789',
            bank_code='058'
        )
        self.deal = Deal.objects.create(
            seller=self.seller,
            slug='test-deal',
            item_description='Test Item',
            amount=Decimal('5000.00'),
            buyer_email='buyer@example.com',
            buyer_name='Test Buyer',
            delivery_address='Test Address'
        )
        
    def test_mark_deal_as_shipped(self):
        """Test seller can mark deal as shipped"""
        self.deal.status = 'PAID'
        self.deal.paid_at = timezone.now()
        self.deal.save()
        
        self.client.force_authenticate(user=self.seller)
        data = {'tracking_number': 'TRK123456'}
        response = self.client.post(f'/api/deals/{self.deal.slug}/ship/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'SHIPPED')
        self.assertEqual(response.data['tracking_number'], 'TRK123456')
        self.assertIsNotNone(response.data['shipped_at'])
        self.assertIsNotNone(response.data['auto_release_at'])
        
    def test_auto_release_calculation(self):
        """Test auto_release_at is calculated correctly"""
        self.deal.status = 'PAID'
        self.deal.paid_at = timezone.now()
        self.deal.delivery_days = 3
        self.deal.save()
        
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(f'/api/deals/{self.deal.slug}/ship/')
        
        # Auto release should be shipped_at + delivery_days + 1 day
        shipped_at = timezone.datetime.fromisoformat(response.data['shipped_at'].replace('Z', '+00:00'))
        auto_release_at = timezone.datetime.fromisoformat(response.data['auto_release_at'].replace('Z', '+00:00'))
        
        expected_days = 4  # 3 delivery days + 1 grace day
        actual_days = (auto_release_at - shipped_at).days
        self.assertEqual(actual_days, expected_days)
        
    def test_confirm_delivery(self):
        """Test buyer can confirm delivery"""
        self.deal.status = 'SHIPPED'
        self.deal.shipped_at = timezone.now()
        self.deal.save()
        
        # No authentication needed for confirmation
        response = self.client.post(f'/api/deals/{self.deal.slug}/confirm/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertIsNotNone(response.data['completed_at'])
        
    def test_open_dispute(self):
        """Test buyer can open a dispute"""
        self.deal.status = 'SHIPPED'
        self.deal.save()
        
        data = {'reason': 'Item not as described'}
        response = self.client.post(f'/api/deals/{self.deal.slug}/dispute/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'OPEN')
        
        # Verify deal status changed
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.status, 'DISPUTED')


class TransactionTests(TestCase):
    """Test transaction tracking"""
    
    def setUp(self):
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com'
        )
        self.deal = Deal.objects.create(
            seller=self.seller,
            slug='test-deal',
            item_description='Test Item',
            amount=Decimal('5000.00')
        )
        
    def test_create_transaction(self):
        """Test transaction can be created"""
        transaction = Transaction.objects.create(
            deal=self.deal,
            tx_type='COLLECTION',
            status='SUCCESS',
            amount=Decimal('5000.00'),
            payaza_ref='PAY-123456'
        )
        
        self.assertEqual(transaction.tx_type, 'COLLECTION')
        self.assertEqual(transaction.status, 'SUCCESS')
        self.assertEqual(transaction.amount, Decimal('5000.00'))
        
    def test_transaction_types(self):
        """Test all transaction types can be created"""
        types = ['COLLECTION', 'PAYOUT', 'REFUND']
        
        for tx_type in types:
            transaction = Transaction.objects.create(
                deal=self.deal,
                tx_type=tx_type,
                status='SUCCESS',
                amount=Decimal('1000.00')
            )
            self.assertEqual(transaction.tx_type, tx_type)


class DisputeTests(TestCase):
    """Test dispute handling"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_staff=True
        )
        self.deal = Deal.objects.create(
            seller=self.seller,
            slug='test-deal',
            item_description='Test Item',
            amount=Decimal('5000.00'),
            status='DISPUTED'
        )
        self.dispute = Dispute.objects.create(
            deal=self.deal,
            reason='Item damaged'
        )
        
    def test_create_dispute(self):
        """Test dispute can be created"""
        self.assertEqual(self.dispute.status, 'OPEN')
        self.assertEqual(self.dispute.reason, 'Item damaged')
        
    def test_admin_can_list_disputes(self):
        """Test admin can list open disputes"""
        self.client.force_authenticate(user=self.seller)
        response = self.client.get('/api/admin/disputes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
    def test_admin_can_resolve_dispute_refund(self):
        """Test admin can resolve dispute with refund"""
        self.client.force_authenticate(user=self.seller)
        data = {'action': 'refund'}
        response = self.client.post(f'/api/admin/disputes/{self.dispute.id}/resolve/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dispute']['status'], 'RESOLVED_REFUND')
        self.assertEqual(response.data['deal']['status'], 'REFUNDED')
        
    def test_admin_can_resolve_dispute_release(self):
        """Test admin can resolve dispute with release"""
        self.client.force_authenticate(user=self.seller)
        data = {'action': 'release'}
        response = self.client.post(f'/api/admin/disputes/{self.dispute.id}/resolve/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dispute']['status'], 'RESOLVED_RELEASE')
        self.assertEqual(response.data['deal']['status'], 'COMPLETED')


class MerchantDashboardTests(TestCase):
    """Test merchant dashboard functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_merchant=True
        )
        self.client.force_authenticate(user=self.seller)
        
        # Create test deals
        Deal.objects.create(
            seller=self.seller,
            slug='deal-1',
            item_description='Item 1',
            amount=Decimal('1000.00'),
            status='COMPLETED'
        )
        Deal.objects.create(
            seller=self.seller,
            slug='deal-2',
            item_description='Item 2',
            amount=Decimal('2000.00'),
            status='PAID'
        )
        Deal.objects.create(
            seller=self.seller,
            slug='deal-3',
            item_description='Item 3',
            amount=Decimal('3000.00'),
            status='DISPUTED'
        )
        
    def test_dashboard_stats(self):
        """Test dashboard returns correct statistics"""
        response = self.client.get('/api/merchant/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_deals'], 3)
        self.assertEqual(response.data['completed_deals'], 1)
        self.assertEqual(response.data['disputed_deals'], 1)
        self.assertEqual(response.data['active_deals'], 1)  # PAID status
        
    def test_merchant_deals_list(self):
        """Test merchant can list their deals"""
        response = self.client.get('/api/merchant/deals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
    def test_merchant_deals_filter_by_status(self):
        """Test merchant can filter deals by status"""
        response = self.client.get('/api/merchant/deals/?status=COMPLETED')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'COMPLETED')


class PaymentLinkTests(TestCase):
    """Test payment link creation"""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username='seller1',
            password='testpass123',
            email='seller@example.com',
            is_merchant=True
        )
        self.client.force_authenticate(user=self.seller)
        
    def test_create_payment_link(self):
        """Test merchant can create payment link"""
        data = {
            'item_description': 'iPhone 15 Pro',
            'amount': '850000.00',
            'delivery_days': 3,
            'buyer_email': 'buyer@example.com'
        }
        response = self.client.post('/api/merchant/links/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('link_url', response.data)
        self.assertIn('slug', response.data)
        
    def test_list_payment_links(self):
        """Test merchant can list payment links"""
        Deal.objects.create(
            seller=self.seller,
            slug='link-1',
            item_description='Item 1',
            amount=Decimal('1000.00')
        )
        
        response = self.client.get('/api/merchant/links/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('link_url', response.data[0])
