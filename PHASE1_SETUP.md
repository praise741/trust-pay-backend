# Phase 1 Implementation - Setup Guide

## ✅ What Was Added

### 1. **Email Notifications** 📧
- Payment received email (to seller)
- Shipping notification email (to buyer)
- Delivery confirmed email (to seller)
- Dispute opened emails (to both parties)
- Dispute resolved emails (to both parties)
- Email verification
- Welcome email

### 2. **Google OAuth Authentication** 🔐
- Sign up with Google
- Login with Google
- Automatic account linking

### 3. **Seller Profile** 👤
- Business name, description
- Profile photo upload
- Social media links (Instagram, WhatsApp, Twitter)
- Website URL
- Verification badge
- Deal statistics (total, completed, completion rate)

### 4. **Enhanced Deal Model** 📦
- Buyer name field
- Delivery address field
- Tracking number field

### 5. **Email Verification** ✉️
- Email verification on signup
- Email verified status tracking

---

## 🔧 Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create Migrations

```bash
python manage.py makemigrations users
python manage.py makemigrations deals
python manage.py migrate
```

### Step 3: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Payaza Configuration
PAYAZA_BASE_URL=https://api.payaza.africa
PAYAZA_PUBLIC_KEY=PZ78-PKTEST-your-uuid-here
PAYAZA_TENANT_ID=test
PAYAZA_SECRET=your-webhook-secret-here

# Email Configuration (Gmail Example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=TrustPay <noreply@trustpay.ng>

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Step 5: Gmail App Password Setup

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App Passwords
4. Generate a new app password for "Mail"
5. Use this password in `EMAIL_HOST_PASSWORD`

### Step 6: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://localhost:3000` (your frontend)
6. Copy Client ID and Client Secret to `.env`

### Step 7: Create Media Directory

```bash
mkdir media
mkdir media/seller_profiles
```

### Step 8: Run the Server

```bash
python manage.py runserver
```

---

## 📡 New API Endpoints

### Authentication

```
POST /api/auth/google/
Body: { "token": "google_id_token" }
Response: { "access": "...", "refresh": "...", "user": {...} }
```

### Seller Profile

```
GET /api/auth/profile/
Headers: Authorization: Bearer <token>
Response: Full seller profile

PUT /api/auth/profile/
Headers: Authorization: Bearer <token>
Body: { "business_name": "...", "business_description": "...", ... }
Response: Updated profile

GET /api/auth/sellers/{username}/
Response: Public seller profile (no auth required)
```

### Enhanced Deal Creation

```
POST /api/deals/
Body: {
  "item_description": "iPhone 15 Pro",
  "amount": "850000.00",
  "delivery_days": 3,
  "buyer_email": "buyer@example.com",
  "buyer_phone": "08098765432",
  "buyer_name": "Maxwell Okafor",
  "delivery_address": "123 Main St, Lagos"
}
```

### Mark as Shipped (with tracking)

```
POST /api/deals/{slug}/ship/
Body: { "tracking_number": "TRK123456" }
```

---

## 🧪 Testing Email Notifications

### Option 1: Console Backend (Development)

Emails will print to console. Already configured in settings:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Option 2: Gmail SMTP (Production-like)

Configure Gmail credentials in `.env` as shown above.

### Test Flow:

1. Create a deal
2. Simulate payment (webhook or manual status change)
3. Check console/email for "Payment Received" email
4. Mark as shipped
5. Check for "Shipping Notification" email
6. Confirm delivery
7. Check for "Delivery Confirmed" email

---

## 🎨 Frontend Integration

### Google OAuth Flow

```javascript
// 1. Load Google Sign-In library
<script src="https://accounts.google.com/gsi/client" async defer></script>

// 2. Initialize Google Sign-In
google.accounts.id.initialize({
  client_id: 'YOUR_GOOGLE_CLIENT_ID',
  callback: handleGoogleResponse
});

// 3. Handle response
async function handleGoogleResponse(response) {
  const res = await fetch('http://localhost:8000/api/auth/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: response.credential })
  });
  
  const data = await res.json();
  // Store data.access and data.refresh tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
}
```

### Seller Profile Upload

```javascript
// Upload profile photo
const formData = new FormData();
formData.append('profile_photo', file);
formData.append('business_name', 'My Shop');

await fetch('http://localhost:8000/api/auth/profile/', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

---

## 📊 Database Changes

### New Fields in `User` Model:
- `email_verified` (Boolean)
- `phone_verified` (Boolean)
- `google_id` (String, unique)

### New Model: `SellerProfile`
- `user` (OneToOne → User)
- `business_name`
- `business_description`
- `profile_photo` (ImageField)
- `instagram_handle`
- `whatsapp_number`
- `twitter_handle`
- `website_url`
- `is_verified`
- `total_deals`
- `completed_deals`
- `created_at`
- `updated_at`

### New Fields in `Deal` Model:
- `buyer_name`
- `delivery_address` (TextField)
- `tracking_number`

---

## 🐛 Troubleshooting

### Email not sending?
- Check `.env` configuration
- Verify Gmail app password
- Check console for error messages
- Try console backend first for testing

### Google OAuth not working?
- Verify Client ID in `.env`
- Check authorized redirect URIs in Google Console
- Ensure `django.contrib.sites` is in INSTALLED_APPS
- Run `python manage.py migrate` after adding allauth

### Profile photo not uploading?
- Ensure `media/` directory exists
- Check `MEDIA_ROOT` and `MEDIA_URL` in settings
- Verify Pillow is installed: `pip install pillow`

### Migrations failing?
- Delete `db.sqlite3` and all migration files (except `__init__.py`)
- Run `python manage.py makemigrations` again
- Run `python manage.py migrate`

---

## ✅ Verification Checklist

- [ ] Dependencies installed
- [ ] Migrations created and applied
- [ ] Superuser created
- [ ] `.env` file configured
- [ ] Gmail app password set up
- [ ] Google OAuth credentials configured
- [ ] Media directory created
- [ ] Server running without errors
- [ ] Can register new user
- [ ] Can login with Google
- [ ] Can create/update seller profile
- [ ] Emails sending (console or SMTP)
- [ ] Can create deal with new fields
- [ ] Can upload profile photo

---

## 🚀 Next Steps (Phase 2)

After Phase 1 is working:
- Buyer Dashboard
- Deal Images Upload
- In-app Notifications
- SMS Notifications (optional)
- Enhanced Analytics

---

## 📞 Support

If you encounter issues:
1. Check the error message carefully
2. Verify all environment variables are set
3. Ensure migrations are applied
4. Check Django logs for detailed errors

Happy coding! 🎉
