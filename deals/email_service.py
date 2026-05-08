from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from datetime import timedelta


def send_payment_received_email(deal):
    """Send email to seller when buyer pays"""
    subject = f'Payment Received - ₦{deal.amount:,.2f} for {deal.item_description}'
    
    expected_delivery = deal.paid_at + timedelta(days=deal.delivery_days) if deal.paid_at else None
    
    html_message = render_to_string('emails/payment_received.html', {
        'deal': deal,
        'seller': deal.seller,
        'expected_delivery': expected_delivery,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[deal.seller.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_shipping_notification_email(deal):
    """Send email to buyer when seller ships"""
    subject = f'Your Order Has Been Shipped - {deal.item_description}'
    
    delivery_deadline = deal.auto_release_at if deal.auto_release_at else None
    
    html_message = render_to_string('emails/shipping_notification.html', {
        'deal': deal,
        'delivery_deadline': delivery_deadline,
        'tracking_number': deal.tracking_number,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    recipient = deal.buyer_email if deal.buyer_email else None
    if recipient:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )


def send_delivery_confirmed_email(deal):
    """Send email to seller when buyer confirms delivery"""
    subject = f'Delivery Confirmed - Payment Released for {deal.item_description}'
    
    net_amount = deal.amount - (deal.amount * deal.trust_fee_percent / 100)
    fee_amount = deal.amount * deal.trust_fee_percent / 100
    
    html_message = render_to_string('emails/delivery_confirmed.html', {
        'deal': deal,
        'seller': deal.seller,
        'net_amount': net_amount,
        'fee_amount': fee_amount,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[deal.seller.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_dispute_opened_email_to_seller(deal, dispute):
    """Send email to seller when dispute is opened"""
    subject = f'Dispute Opened - {deal.item_description}'
    
    html_message = render_to_string('emails/dispute_opened_seller.html', {
        'deal': deal,
        'dispute': dispute,
        'seller': deal.seller,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[deal.seller.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_dispute_opened_email_to_buyer(deal, dispute):
    """Send email to buyer confirming dispute received"""
    subject = f'Your Dispute Has Been Received - {deal.item_description}'
    
    html_message = render_to_string('emails/dispute_opened_buyer.html', {
        'deal': deal,
        'dispute': dispute,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    recipient = deal.buyer_email if deal.buyer_email else None
    if recipient:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )


def send_dispute_resolved_email(deal, dispute, resolution_type):
    """Send email to both parties when dispute is resolved"""
    if resolution_type == 'refund':
        subject_seller = f'Dispute Resolved - Refund Issued for {deal.item_description}'
        subject_buyer = f'Dispute Resolved - Refund Processed for {deal.item_description}'
    else:
        subject_seller = f'Dispute Resolved - Payment Released for {deal.item_description}'
        subject_buyer = f'Dispute Resolved - Payment Released to Seller for {deal.item_description}'
    
    # Email to seller
    html_message_seller = render_to_string('emails/dispute_resolved_seller.html', {
        'deal': deal,
        'dispute': dispute,
        'resolution_type': resolution_type,
        'seller': deal.seller,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message_seller = strip_tags(html_message_seller)
    
    send_mail(
        subject=subject_seller,
        message=plain_message_seller,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[deal.seller.email],
        html_message=html_message_seller,
        fail_silently=False,
    )
    
    # Email to buyer
    if deal.buyer_email:
        html_message_buyer = render_to_string('emails/dispute_resolved_buyer.html', {
            'deal': deal,
            'dispute': dispute,
            'resolution_type': resolution_type,
            'frontend_url': settings.FRONTEND_URL,
        })
        plain_message_buyer = strip_tags(html_message_buyer)
        
        send_mail(
            subject=subject_buyer,
            message=plain_message_buyer,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[deal.buyer_email],
            html_message=html_message_buyer,
            fail_silently=False,
        )
