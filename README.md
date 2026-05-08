# TrustPay Backend

A Django REST API escrow service that sits between buyers and sellers, integrating with Payaza for payment processing. Holds deal state in SQLite — no Celery, no Redis, no async.

## ✨ Phase 1 Features (NEW!)

- ✅ **Email Notifications** - 5 types of automated emails
- ✅ **Google OAuth** - One-click signup/login
- ✅ **Seller Profiles** - Business info, photos, social links
- ✅ **Enhanced Deals** - Delivery address, tracking numbers
- ✅ **Email Verification** - Secure account verification

## 🆕 Phase 2 Features (LATEST!)

- ✅ **Buyer Dashboard** - Track orders by email/phone (no account needed)
- ✅ **Enhanced Tracking** - Add/update tracking numbers anytime

**All Tests Passing:** 42/42 ✅

## Tech Stack

- **Django 6.0** + **Django REST Framework**
- **SQLite** (zero-config, default)
- **SimpleJWT** for authentication
- **Google OAuth** for social login
- **Payaza API** for virtual accounts and payouts
- **Email System** for notifications

## Setup

### Quick Start (5 Minutes)

See **[QUICKSTART.md](QUICKSTART.md)** for the fastest setup.

### Detailed Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your SECRET_KEY, Payaza, Email, and Google OAuth credentials

# 4. Run database migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Create media directory
mkdir -p media/seller_profiles

# 7. Start the development server
python manage.py runserver
```

### Phase 1 Setup

For detailed Phase 1 setup (Email, Google OAuth, Seller Profiles):
- **[PHASE1_SETUP.md](PHASE1_SETUP.md)** - Complete setup guide
- **[PHASE1_SUMMARY.md](PHASE1_SUMMARY.md)** - Feature overview

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `DEBUG` | Debug mode toggle | `True` |
| `PAYAZA_BASE_URL` | Payaza API base URL | `https://api.payaza.africa` |
| `PAYAZA_PUBLIC_KEY` | Payaza public key | `PZ78-PKTEST-...` |
| `PAYAZA_TENANT_ID` | Payaza tenant ID | `test` |
| `PAYAZA_SECRET` | Payaza webhook secret | `your-webhook-secret-here` |
| **`EMAIL_HOST_USER`** | Email address for sending | `your-email@gmail.com` |
| **`EMAIL_HOST_PASSWORD`** | Email app password | `your-app-password` |
| **`GOOGLE_CLIENT_ID`** | Google OAuth Client ID | `your-client-id` |
| **`GOOGLE_CLIENT_SECRET`** | Google OAuth Secret | `your-secret` |
| **`FRONTEND_URL`** | Frontend URL for links | `http://localhost:3000` |

> **Bold** = New in Phase 1. Copy `.env.example` to `.env` and fill in your values. `.env` is already in `.gitignore`.

## API Endpoints

### Authentication (`/api/auth/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register/` | Register a new user | No |
| POST | `/api/auth/login/` | Obtain JWT token pair | No |
| POST | `/api/auth/refresh/` | Refresh JWT access token | No |
| **POST** | **`/api/auth/google/`** | **Google OAuth login** | **No** |
| **GET** | **`/api/auth/profile/`** | **Get seller profile** | **Yes** |
| **PUT** | **`/api/auth/profile/`** | **Update seller profile** | **Yes** |
| **GET** | **`/api/auth/sellers/{username}/`** | **Public seller profile** | **No** |

### Deals (`/api/deals/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/deals/` | List all deals | Yes |
| POST | `/api/deals/` | Create a new deal | Yes |
| GET | `/api/deals/{slug}/` | Get deal details | Yes |
| POST | `/api/deals/{slug}/pay/` | Initiate payment (get VA) | Yes |
| POST | `/api/deals/{slug}/ship/` | Mark deal as shipped | Yes |
| POST | `/api/deals/{slug}/confirm/` | Confirm delivery | Yes |
| POST | `/api/deals/{slug}/dispute/` | Dispute a deal | Yes |

### Merchant (`/api/merchant/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/merchant/dashboard/` | Dashboard statistics | Yes |
| GET | `/api/merchant/deals/` | List merchant deals | Yes |
| GET | `/api/merchant/deals/{slug}/` | Get merchant deal details | Yes |
| GET | `/api/merchant/transactions/` | Transaction history | Yes |
| POST | `/api/merchant/links/` | Create payment link | Yes |
| GET | `/api/merchant/links/` | List payment links | Yes |

### Admin (`/api/admin/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/admin/disputes/` | List open disputes | Admin |
| POST | `/api/admin/disputes/{id}/resolve/` | Resolve dispute | Admin |

### Webhooks (`/api/webhooks/`)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/webhooks/payaza/` | Payaza payment callback | No (signature) |

> **Bold** = New in Phase 1

### Authentication Header

All authenticated endpoints require:
```
Authorization: Bearer <access_token>
```

## Auto-Release Command

A management command checks for expired deals and auto-completes them:

```bash
python manage.py auto_release
```

This finds deals in `SHIPPED` status whose `auto_release_at` time has passed and transitions them to `COMPLETED`, triggering a payout to the seller.

## Testing with Payaza Sandbox

1. **Set up sandbox credentials** in your `.env` file:
   ```env
   PAYAZA_BASE_URL=https://api.payaza.africa
   PAYAZA_PUBLIC_KEY=PZ78-PKTEST-your-uuid-here
   PAYAZA_TENANT_ID=test
   PAYAZA_SECRET=your-webhook-secret-here
   ```

2. **Create a deal** and call the pay endpoint to get a virtual account number.

3. **Simulate a payment** by transferring to the VA from the Payaza sandbox dashboard, or use their test API to simulate a credit event.

4. **Verify the webhook** is received — check the deal status transitions to `PAID`:
   ```bash
   python manage.py runserver
   # In another terminal:
   curl http://localhost:8000/api/deals/<slug>/
   ```

5. **(Optional) Expose local server** for Payaza webhooks using a tool like ngrok:
   ```bash
   ngrok http 8000
   # Update your Payaza sandbox webhook URL to the ngrok URL + /api/webhooks/payaza/
   ```

## Email Notifications

### Development (Console)
By default, emails print to the console. No configuration needed!

### Production (SMTP)
Configure Gmail or SendGrid in `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Email Types:**
- Payment received (to seller)
- Shipping notification (to buyer)
- Delivery confirmed (to seller)
- Dispute opened (to both)
- Dispute resolved (to both)

## Google OAuth

1. Create project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add redirect URI: `http://localhost:8000/accounts/google/login/callback/`
5. Add credentials to `.env`

**Frontend Integration:**
```javascript
// Send Google token to backend
const response = await fetch('/api/auth/google/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: googleIdToken })
});
const { access, refresh, user } = await response.json();
```

## Project Structure

```
backend/              # Django project settings
users/                # User model, auth views, seller profiles
  ├── models.py       # User + SellerProfile models
  ├── views.py        # Auth + profile views
  ├── serializers.py  # User + profile serializers
  ├── email_service.py # Email verification
  ├── google_auth.py  # Google OAuth handler
  └── admin.py        # Admin interface
deals/                # Deal model, views, and auto-release command
  ├── models.py       # Deal, Transaction, Dispute models
  ├── views.py        # Deal lifecycle endpoints
  ├── email_service.py # Deal email notifications
  ├── admin_api/      # Admin dispute resolution
  ├── merchant/       # Merchant dashboard & payment links
  └── management/     # Auto-release command
payments/             # Payaza webhook handling
  ├── payaza.py       # Payaza API integration
  └── views.py        # Webhook handler
templates/            # Email templates
  └── emails/         # 9 HTML email templates
media/                # User-uploaded files
  └── seller_profiles/ # Profile photos
manage.py             # Django management script
```
