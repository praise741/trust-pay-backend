from rest_framework import serializers
from deals.models import Deal
from django.utils import timezone


class BuyerDashboardSerializer(serializers.Serializer):
    """Serializer for buyer dashboard statistics"""
    email = serializers.EmailField()
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    disputed_orders = serializers.IntegerField()


class TrackingInfoSerializer(serializers.ModelSerializer):
    """Serializer for order tracking information"""
    
    status_display = serializers.SerializerMethodField()
    estimated_delivery = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    can_confirm = serializers.SerializerMethodField()
    can_dispute = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'slug', 'item_description', 'amount', 'status', 'status_display',
            'tracking_number', 'delivery_address', 'buyer_name',
            'created_at', 'paid_at', 'shipped_at', 'auto_release_at',
            'completed_at', 'estimated_delivery', 'days_remaining',
            'can_confirm', 'can_dispute', 'delivery_days'
        ]
    
    def get_status_display(self, obj):
        """Get human-readable status"""
        status_map = {
            'PENDING_PAYMENT': 'Waiting for Payment',
            'PAID': 'Payment Received - Preparing to Ship',
            'SHIPPED': 'Shipped - In Transit',
            'DELIVERED': 'Delivered',
            'COMPLETED': 'Completed',
            'DISPUTED': 'Under Dispute',
            'REFUNDED': 'Refunded'
        }
        return status_map.get(obj.status, obj.status)
    
    def get_estimated_delivery(self, obj):
        """Calculate estimated delivery date"""
        if obj.shipped_at:
            # Use auto_release_at minus 1 day (grace period)
            if obj.auto_release_at:
                return obj.auto_release_at - timezone.timedelta(days=1)
        elif obj.paid_at:
            # Estimate based on payment date + delivery days
            return obj.paid_at + timezone.timedelta(days=obj.delivery_days)
        return None
    
    def get_days_remaining(self, obj):
        """Calculate days remaining until auto-release"""
        if obj.status == 'SHIPPED' and obj.auto_release_at:
            now = timezone.now()
            if obj.auto_release_at > now:
                delta = obj.auto_release_at - now
                return delta.days
            return 0
        return None
    
    def get_can_confirm(self, obj):
        """Check if buyer can confirm delivery"""
        return obj.status == 'SHIPPED'
    
    def get_can_dispute(self, obj):
        """Check if buyer can open dispute"""
        return obj.status in ['SHIPPED', 'DELIVERED', 'PAID']


class OrderTimelineSerializer(serializers.Serializer):
    """Serializer for order timeline/history"""
    
    event = serializers.CharField()
    timestamp = serializers.DateTimeField()
    description = serializers.CharField()
    
    @staticmethod
    def get_timeline(deal):
        """Generate timeline events for a deal"""
        timeline = []
        
        if deal.created_at:
            timeline.append({
                'event': 'ORDER_CREATED',
                'timestamp': deal.created_at,
                'description': 'Order created'
            })
        
        if deal.paid_at:
            timeline.append({
                'event': 'PAYMENT_RECEIVED',
                'timestamp': deal.paid_at,
                'description': 'Payment received and secured'
            })
        
        if deal.shipped_at:
            timeline.append({
                'event': 'SHIPPED',
                'timestamp': deal.shipped_at,
                'description': f'Order shipped{" - " + deal.tracking_number if deal.tracking_number else ""}'
            })
        
        if deal.completed_at:
            timeline.append({
                'event': 'COMPLETED',
                'timestamp': deal.completed_at,
                'description': 'Order completed'
            })
        
        return timeline
