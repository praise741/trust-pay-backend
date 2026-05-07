# TrustPay Backend — Hackathon PRD (Stripped)

## 1. What We Are Actually Building

A Django REST API that sits between buyers/sellers and Payaza. It holds deal state in SQLite. No Redis, no Celery, no async.

**Core Loop:**
1. Seller creates Deal → we store it
2. Buyer hits "Pay" → we call Payaza to get a one-time Virtual Account (VA)
3. Buyer transfers money to VA → Payaza hits our webhook → we mark deal PAID
4. Seller ships → marks SHIPPED
5. Auto-release: a simple management command runs manually to check expired deals
6. Buyer confirms → marks COMPLETED → we trigger payout to seller
7. Buyer disputes → marks DISPUTED → stops everything, admin resolves

---

## 2. Tech Stack (ONLY THIS)

- Django 4.2 + Django REST Framework
- SQLite (default, zero config)
- Django Admin (built-in, use it for disputes)
- `requests` library for Payaza API calls
- `djangorestframework-simplejwt` for auth tokens

**NO:** Celery, Redis, Channels, Postgres, Docker, anything else.

---

## 3. Models (Exact Fields)

### User (swap to custom NOW before any migrations)

Create `users/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=10, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    is_merchant = models.BooleanField(default=False)
```

In `settings.py`:
```python
AUTH_USER_MODEL = 'users.User'
```

### Deal

Create `deals/models.py`:

```python
import uuid
from django.db import models
from django.conf import settings

class Deal(models.Model):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('DISPUTED', 'Disputed'),
        ('REFUNDED', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deals')
    buyer_email = models.EmailField(blank=True)
    buyer_phone = models.CharField(max_length=15, blank=True)
    item_description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_days = models.PositiveIntegerField(default=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')

    # Payaza VA
    va_account_number = models.CharField(max_length=20, blank=True)
    va_bank_name = models.CharField(max_length=100, blank=True)
    va_reference = models.CharField(max_length=100, blank=True, unique=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    auto_release_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Fee (hardcoded 1.5%)
    trust_fee_percent = models.DecimalField(max_digits=4, decimal_places=2, default=1.50)

    def __str__(self):
        return f"{self.item_description} - {self.status}"
```

### Transaction (simple ledger)

```python
class Transaction(models.Model):
    TYPE_CHOICES = [
        ('COLLECTION', 'Collection'),
        ('PAYOUT', 'Payout'),
        ('REFUND', 'Refund'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='transactions')
    tx_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payaza_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Dispute

```python
class Dispute(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('RESOLVED_REFUND', 'Resolved - Refund'),
        ('RESOLVED_RELEASE', 'Resolved - Release'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE, related_name='dispute')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

---

## 4. Exact API Endpoints

### Auth (`users/views.py`, `users/urls.py`)

**POST /api/auth/register/**
Body: `{"username": "seller1", "password": "pass123", "phone": "08012345678", "bank_name": "GTBank", "bank_account_number": "0123456789", "bank_code": "058", "is_merchant": true}`
Response: `{"id": "...", "username": "seller1", "phone": "..."}`

**POST /api/auth/login/**
Use DRF SimpleJWT. Body: `{"username": "seller1", "password": "pass123"}`
Response: `{"access": "...", "refresh": "..."}`

### Deals (`deals/views.py`, `deals/urls.py`)

**POST /api/deals/** (Auth required, seller only)
Body: `{"item_description": "Architecture Book", "amount": "5000.00", "delivery_days": 3, "buyer_email": "max@example.com", "buyer_phone": "08098765432"}`
Logic: Auto-generate slug using `django.utils.text.slugify` + random suffix. Set status `PENDING_PAYMENT`.
Response: full deal object

**GET /api/deals/** (Auth required)
Returns deals where `request.user == seller` OR `request.user.email == buyer_email`.

**GET /api/deals/<slug>/** (Public if status is PENDING_PAYMENT, otherwise auth)
Response: full deal object

**POST /api/deals/<slug>/pay/** (No auth needed - buyer is anonymous)
Logic:
1. Find deal by slug, check status is `PENDING_PAYMENT`
2. Call Payaza API to create virtual account
3. Save returned `va_account_number`, `va_bank_name`, `va_reference` to deal
4. Return: `{"va_account_number": "...", "va_bank_name": "...", "amount": "5000.00"}`

**POST /api/deals/<slug>/ship/** (Auth required, must be seller)
Logic:
1. Check deal.status == `PAID`
2. Set `status = SHIPPED`, `shipped_at = now()`, `auto_release_at = now() + delivery_days + 1 day`
3. Save and return deal

**POST /api/deals/<slug>/confirm/** (No auth - buyer clicks link)
Logic:
1. Check deal.status == `SHIPPED`
2. Call `trigger_payout(deal)` (see below)
3. Set `status = COMPLETED`, `completed_at = now()`
4. Save and return deal

**POST /api/deals/<slug>/dispute/** (No auth - buyer clicks link)
Body: `{"reason": "Book is torn"}`
Logic:
1. Check deal.status in (`SHIPPED`, `DELIVERED`)
2. Create `Dispute(deal=deal, reason=body['reason'])`
3. Set deal.status = `DISPUTED`
4. Save and return `{"dispute_id": "...", "status": "OPEN"}`

### Webhook (`payments/views.py`, `payments/urls.py`)

**POST /api/webhooks/payaza/**
No auth token header - use Payaza signature verification.
Logic:
1. Verify webhook signature (Payaza sends HMAC in header, verify against body)
2. Parse JSON payload. Find `reference` field.
3. Find Deal where `va_reference == payload['reference']`
4. If event is `payment.success`:
   - deal.status = `PAID`
   - deal.paid_at = now()
   - Create Transaction(deal=deal, tx_type='COLLECTION', status='SUCCESS', amount=deal.amount, payaza_ref=payload.get('transaction_reference'))
   - Save all
5. Return `{"status": "received"}` 200 OK

### Admin (Django Admin + simple API)

Use Django Admin at `/admin/` to view disputes.

**GET /api/admin/disputes/** (Auth + staff only)
List disputes where status='OPEN'

**POST /api/admin/disputes/<id>/resolve/** (Auth + staff only)
Body: `{"action": "refund"}` or `{"action": "release"}`
Logic:
- If refund: call `refund_buyer(deal)`, set dispute.status='RESOLVED_REFUND', deal.status='REFUNDED'
- If release: call `payout_seller(deal)`, set dispute.status='RESOLVED_RELEASE', deal.status='COMPLETED'
- Save all and return

---

## 5. Payaza Integration (Exact Functions)

Create `payments/payaza.py`:

```python
import requests
from django.conf import settings

PAYAZA_BASE = getattr(settings, 'PAYAZA_BASE_URL', 'https://sandbox-api.payaza.africa')
HEADERS = {
    'Authorization': f'Bearer {settings.PAYAZA_API_KEY}',
    'Content-Type': 'application/json',
}

def create_virtual_account(deal):
    url = f"{PAYAZA_BASE}/api/v1/virtual-accounts"  # CHECK ACTUAL PAYAZA DOCS
    payload = {
        "amount": str(deal.amount),
        "reference": str(deal.id),
        "customer_email": deal.buyer_email or "",
        "customer_phone": deal.buyer_phone or "",
        "callback_url": "https://your-domain.com/api/webhooks/payaza/"
    }
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return {
        "account_number": data["account_number"],
        "bank_name": data["bank_name"],
        "reference": data["reference"]
    }

def payout_seller(deal):
    url = f"{PAYAZA_BASE}/api/v1/payouts"  # CHECK ACTUAL PAYAZA DOCS
    net = deal.amount - (deal.amount * deal.trust_fee_percent / 100)
    payload = {
        "account_number": deal.seller.bank_account_number,
        "bank_code": deal.seller.bank_code,
        "amount": str(net),
        "narration": f"TrustPay {deal.item_description}",
        "reference": f"payout-{deal.id}"
    }
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

def refund_buyer(deal):
    url = f"{PAYAZA_BASE}/api/v1/payouts"
    payload = {
        "account_number": deal.buyer_phone,
        "bank_code": "",
        "amount": str(deal.amount),
        "narration": f"TrustPay refund {deal.item_description}",
        "reference": f"refund-{deal.id}"
    }
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

**IMPORTANT:** These URLs are GUESSES. You MUST check Payaza's actual API docs and update the endpoints/payloads.

### Auto-Release (NO CELERY)

Create a management command: `deals/management/commands/auto_release.py`

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from deals.models import Deal
from payments.payaza import payout_seller

class Command(BaseCommand):
    help = 'Auto-release funds for deals past delivery window'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        deals = Deal.objects.filter(
            status='SHIPPED',
            auto_release_at__lte=now
        )
        for deal in deals:
            try:
                payout_seller(deal)
                deal.status = 'COMPLETED'
                deal.completed_at = now
                deal.save()
                self.stdout.write(self.style.SUCCESS(f'Released {deal.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed {deal.id}: {e}'))
```

**Run manually:** `python manage.py auto_release`
For hackathon demo, just run the command manually when needed.

---

## 6. Settings to Update

`settings.py` additions:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'users',
    'deals',
    'payments',
]

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Payaza
PAYAZA_BASE_URL = os.getenv('PAYAZA_BASE_URL', 'https://sandbox-api.payaza.africa')
PAYAZA_API_KEY = os.getenv('PAYAZA_API_KEY', '')
PAYAZA_SECRET = os.getenv('PAYAZA_SECRET', '')  # for webhook verification
```

Add to `urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/deals/', include('deals.urls')),
    path('api/webhooks/', include('payments.urls')),
]
```

---

## 7. Exact Task Split

### Partner A — Models, Auth, Deal CRUD

1. Create `users` app. Custom User model. Register in `settings.AUTH_USER_MODEL`. Migrate.
2. Create `deals` app. `Deal`, `Transaction`, `Dispute` models. Migrate.
3. Wire DRF + SimpleJWT in settings.
4. `POST /api/auth/register/` and `POST /api/auth/login/` views.
5. `POST /api/deals/` (create), `GET /api/deals/` (list my deals), `GET /api/deals/<slug>/` (retrieve).
6. `POST /api/deals/<slug>/ship/` (seller only, sets SHIPPED + auto_release_at).
7. Register models in Django Admin for quick visibility.

### Partner B — Payaza, Webhooks, Payouts, Disputes

1. Create `payments` app. `payaza.py` with exact functions above.
2. `POST /api/deals/<slug>/pay/` - call Payaza VA API, save response to deal.
3. `POST /api/webhooks/payaza/` - verify signature, update deal to PAID, create Transaction.
4. `POST /api/deals/<slug>/confirm/` - call `payout_seller()`, mark COMPLETED.
5. `POST /api/deals/<slug>/dispute/` - create Dispute, mark DISPUTED.
6. Management command `python manage.py auto_release` for auto-payout.
7. Admin dispute resolution endpoint: refund or release.

---

## 8. What You Need From Payaza (Do This FIRST)

1. Sandbox account + API key
2. Exact endpoint for Virtual Account generation
3. Exact endpoint for Payouts
4. Webhook payload format and signature header name
5. Sandbox test bank codes for payouts

**Without #2-4, you cannot build.** Get these before writing any Payaza code.

---

## 9. Running Locally

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install django djangorestframework djangorestframework-simplejwt requests

# Migrate
python manage.py makemigrations users deals payments
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run
python manage.py runserver

# Test auto-release manually
python manage.py auto_release
```

---

**Document Version:** 2.0 (Stripped - No Async)  
**Last Updated:** 2025-05-07  
**Status:** Ready for implementation
