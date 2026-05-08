from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from django.utils.text import slugify
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from datetime import timedelta
import random
import string

from .models import Deal, Transaction, Dispute
from .serializers import (
    DealSerializer, DealCreateSerializer,
    DealPayResponseSerializer, TransactionSerializer,
    DisputeSerializer, DisputeCreateSerializer,
)
from payments.payaza import create_virtual_account, payout_seller, refund_buyer, PayazaError
from .email_service import (
    send_payment_received_email,
    send_shipping_notification_email,
    send_delivery_confirmed_email,
    send_dispute_opened_email_to_seller,
    send_dispute_opened_email_to_buyer,
)


class DealListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return DealCreateSerializer if self.request.method == 'POST' else DealSerializer

    def get_queryset(self):
        return Deal.objects.filter(
            Q(seller=self.request.user) |
            Q(buyer_email=self.request.user.email)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        slug_base = slugify(serializer.validated_data['item_description']) or 'deal'
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        slug = f"{slug_base}-{suffix}"
        serializer.save(seller=self.request.user, slug=slug)


class DealDetailView(generics.RetrieveAPIView):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def deal_pay(request, slug):
    deal = generics.get_object_or_404(Deal, slug=slug)
    if deal.status != 'PENDING_PAYMENT':
        return Response(
            {'error': 'Deal is not pending payment'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    va = create_virtual_account(deal)
    deal.va_account_number = va['account_number']
    deal.va_bank_name = va['bank_name']
    deal.va_reference = va['reference']
    deal.save()
    return Response(DealPayResponseSerializer({
        'va_account_number': va['account_number'],
        'va_bank_name': va['bank_name'],
        'amount': deal.amount,
    }).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deal_ship(request, slug):
    deal = generics.get_object_or_404(Deal, slug=slug)
    if deal.seller != request.user:
        return Response(
            {'error': 'Only the seller can mark as shipped'},
            status=status.HTTP_403_FORBIDDEN,
        )
    if deal.status != 'PAID':
        return Response(
            {'error': 'Deal must be paid before shipping'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    now = timezone.now()
    deal.status = 'SHIPPED'
    deal.shipped_at = now
    deal.auto_release_at = now + timedelta(days=deal.delivery_days + 1)
    
    # Get tracking number from request if provided
    tracking_number = request.data.get('tracking_number', '')
    if tracking_number:
        deal.tracking_number = tracking_number
    
    deal.save()
    
    # Send email notification to buyer
    try:
        send_shipping_notification_email(deal)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send shipping email: {e}")
    
    return Response(DealSerializer(deal).data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_tracking(request, slug):
    """
    Update tracking number for a shipped deal
    PUT /api/deals/{slug}/tracking/
    Body: { "tracking_number": "TRK123456" }
    """
    deal = generics.get_object_or_404(Deal, slug=slug)
    
    if deal.seller != request.user:
        return Response(
            {'error': 'Only the seller can update tracking information'},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    if deal.status not in ['PAID', 'SHIPPED']:
        return Response(
            {'error': 'Can only update tracking for paid or shipped deals'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    tracking_number = request.data.get('tracking_number')
    if not tracking_number:
        return Response(
            {'error': 'Tracking number is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    deal.tracking_number = tracking_number
    deal.save()
    
    return Response({
        'message': 'Tracking number updated successfully',
        'tracking_number': deal.tracking_number,
        'deal': DealSerializer(deal).data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def deal_confirm(request, slug):
    deal = generics.get_object_or_404(Deal, slug=slug)
    if deal.status != 'SHIPPED':
        return Response(
            {'error': 'Deal must be shipped to confirm'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if hasattr(deal, 'dispute') and deal.dispute.status == 'OPEN':
        return Response(
            {'error': 'Deal is under dispute'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        payout_seller(deal)
    except PayazaError:
        Transaction.objects.create(
            deal=deal, tx_type='PAYOUT', status='FAILED', amount=deal.amount
        )
        return Response(
            {'error': 'Payout failed, please try again'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    deal.status = 'COMPLETED'
    deal.completed_at = timezone.now()
    deal.save()
    Transaction.objects.create(
        deal=deal, tx_type='PAYOUT', status='SUCCESS', amount=deal.amount
    )
    
    # Send email notification to seller
    try:
        send_delivery_confirmed_email(deal)
    except Exception as e:
        print(f"Failed to send delivery confirmed email: {e}")
    
    return Response(DealSerializer(deal).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def deal_dispute(request, slug):
    deal = generics.get_object_or_404(Deal, slug=slug)
    if deal.status not in ('SHIPPED', 'DELIVERED', 'PAID'):
        return Response(
            {'error': 'Cannot dispute this deal'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = DisputeCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if hasattr(deal, 'dispute'):
        return Response(
            {'error': 'Deal already has a dispute'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    with transaction.atomic():
        dispute = Dispute.objects.create(deal=deal, reason=serializer.validated_data['reason'])
        deal.status = 'DISPUTED'
        deal.save()
    
    # Send email notifications
    try:
        send_dispute_opened_email_to_seller(deal, dispute)
        send_dispute_opened_email_to_buyer(deal, dispute)
    except Exception as e:
        print(f"Failed to send dispute emails: {e}")
    
    return Response({'dispute_id': dispute.id, 'status': 'OPEN'})


@api_view(['POST'])
@permission_classes([AllowAny])
def deal_mock_pay(request, slug):
    if not getattr(settings, 'PAYAZA_MOCK_MODE', False):
        return Response({'error': 'Mock mode disabled'}, status=403)
    deal = generics.get_object_or_404(Deal, slug=slug)
    if deal.status != 'PENDING_PAYMENT':
        return Response({'error': 'Deal is not pending payment'}, status=400)
    deal.status = 'PAID'
    deal.paid_at = timezone.now()
    deal.save()
    Transaction.objects.create(
        deal=deal, tx_type='COLLECTION', status='SUCCESS',
        amount=deal.amount, payaza_ref=f'mock-{deal.id}'
    )
    return Response({'status': 'Payment simulated', 'deal': DealSerializer(deal).data})
