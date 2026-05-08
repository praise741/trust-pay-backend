from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_email_verification(user, verification_url):
    """Send email verification link to user"""
    subject = 'Verify Your TrustPay Email'
    html_message = render_to_string('emails/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """Send welcome email after successful registration"""
    subject = 'Welcome to TrustPay!'
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
        'frontend_url': settings.FRONTEND_URL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
