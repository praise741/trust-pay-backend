from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=10, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    bank_account_name = models.CharField(max_length=100, blank=True)
    is_merchant = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)


class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=255, blank=True)
    business_description = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='seller_profiles/', blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    website_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    total_deals = models.PositiveIntegerField(default=0)
    completed_deals = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name or self.user.username}'s Profile"

    @property
    def completion_rate(self):
        if self.total_deals == 0:
            return 0
        return round((self.completed_deals / self.total_deals) * 100, 2)
