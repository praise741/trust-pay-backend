from decimal import Decimal
from rest_framework import serializers
from .models import Deal, Transaction, Dispute

PLATFORM_FEE_PERCENT = Decimal('1.50')


class DealSerializer(serializers.ModelSerializer):
    trust_fee_amount = serializers.SerializerMethodField()
    seller_receives = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'status', 'va_account_number',
                            'va_bank_name', 'va_reference', 'created_at',
                            'paid_at', 'shipped_at', 'auto_release_at',
                            'completed_at']

    def get_trust_fee_amount(self, obj):
        fee = obj.amount * obj.trust_fee_percent / Decimal('100')
        return str(fee.quantize(Decimal('0.01')))

    def get_seller_receives(self, obj):
        net = obj.amount - (obj.amount * obj.trust_fee_percent / Decimal('100'))
        return str(net.quantize(Decimal('0.01')))


class DealCreateSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Deal
        fields = ['item_description', 'amount', 'delivery_days',
                  'buyer_email', 'buyer_phone', 'buyer_name', 'delivery_address',
                  'status', 'slug']


class DealPayResponseSerializer(serializers.Serializer):
    va_account_number = serializers.CharField()
    va_bank_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    trust_fee_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    trust_fee_percent = serializers.DecimalField(max_digits=4, decimal_places=2)
    seller_receives = serializers.DecimalField(max_digits=12, decimal_places=2)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = ['id', 'deal', 'reason', 'status', 'created_at', 'resolved_at']
        read_only_fields = ['id', 'status', 'created_at', 'resolved_at']


class DisputeCreateSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)


class AdminDisputeSerializer(serializers.ModelSerializer):
    deal = DealSerializer(read_only=True)

    class Meta:
        model = Dispute
        fields = '__all__'
