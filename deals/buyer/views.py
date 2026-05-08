from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from deals.models import Deal
from deals.serializers import DealSerializer
from .serializers import BuyerDashboardSerializer, TrackingInfoSerializer


class BuyerDashboardView(APIView):
    """
    Buyer dashboard - track orders by email
    No authentication required, uses email for lookup
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Get buyer's orders by email
        POST /api/buyer/dashboard/
        Body: { "email": "buyer@example.com" }
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all deals for this buyer email
        deals = Deal.objects.filter(buyer_email=email).order_by('-created_at')
        
        if not deals.exists():
            return Response({
                'email': email,
                'total_orders': 0,
                'pending_orders': 0,
                'completed_orders': 0,
                'disputed_orders': 0,
                'orders': []
            })
        
        # Calculate statistics
        stats = deals.aggregate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(status__in=['PENDING_PAYMENT', 'PAID', 'SHIPPED'])),
            completed_orders=Count('id', filter=Q(status='COMPLETED')),
            disputed_orders=Count('id', filter=Q(status='DISPUTED'))
        )
        
        # Serialize deals
        serializer = DealSerializer(deals, many=True)
        
        return Response({
            'email': email,
            'total_orders': stats['total_orders'],
            'pending_orders': stats['pending_orders'],
            'completed_orders': stats['completed_orders'],
            'disputed_orders': stats['disputed_orders'],
            'orders': serializer.data
        })


class BuyerOrderDetailView(APIView):
    """
    Get detailed order information for buyer
    No authentication required
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        """
        Get order details by slug
        GET /api/buyer/orders/{slug}/
        """
        deal = get_object_or_404(Deal, slug=slug)
        serializer = DealSerializer(deal)
        return Response(serializer.data)


class BuyerOrderTrackingView(APIView):
    """
    Get tracking information for an order
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        """
        Get tracking info for order
        GET /api/buyer/orders/{slug}/tracking/
        """
        deal = get_object_or_404(Deal, slug=slug)
        serializer = TrackingInfoSerializer(deal)
        return Response(serializer.data)


class BuyerOrdersByPhoneView(APIView):
    """
    Get buyer's orders by phone number
    Alternative to email lookup
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Get buyer's orders by phone
        POST /api/buyer/orders-by-phone/
        Body: { "phone": "08012345678" }
        """
        phone = request.data.get('phone')
        
        if not phone:
            return Response(
                {'error': 'Phone number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all deals for this buyer phone
        deals = Deal.objects.filter(buyer_phone=phone).order_by('-created_at')
        
        if not deals.exists():
            return Response({
                'phone': phone,
                'total_orders': 0,
                'orders': []
            })
        
        serializer = DealSerializer(deals, many=True)
        
        return Response({
            'phone': phone,
            'total_orders': deals.count(),
            'orders': serializer.data
        })
