# 🚀 TrustPay Backend - Quick Start

## Phase 1 Features Added ✨

- ✅ Email notifications (5 types)
- ✅ Google OAuth login
- ✅ Seller profiles
- ✅ Delivery address & tracking
- ✅ Email verification

---

## ⚡ Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

### 4. Create `.env` File
```bash
cp .env.example .env
```

Edit `.env` and add your credentials (optional for testing):
```env
SECRET_KEY=your-secret-key
DEBUG=True

# For email testing (optional - defaults to console)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# For Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
```

### 5. Create Media Directory
```bash
mkdir -p media/seller_profiles
```

### 6. Run Server
```bash
python manage.py runserver
```

✅ **Done!** Server running at http://localhost:8000

---

## 🧪 Quick Test

### Test 1: Register User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "password": "test123",
    "email": "seller@test.com",
    "is_merchant": true
  }'
```

### Test 2: Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "password": "test123"
  }'
```

Save the `access` token from response.

### Test 3: Create Deal
```bash
curl -X POST http://localhost:8000/api/deals/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "item_description": "iPhone 15 Pro",
    "amount": "850000",
    "delivery_days": 3,
    "buyer_email": "buyer@test.com",
    "buyer_name": "John Doe",
    "delivery_address": "123 Main St, Lagos"
  }'
```

### Test 4: Check Email (Console)
Look at your terminal - you should see email output!

---

## 📚 Documentation

- **Full Setup Guide:** `PHASE1_SETUP.md`
- **Feature Summary:** `PHASE1_SUMMARY.md`
- **API Documentation:** `API_INTEGRATION.md`
- **Product Requirements:** `PRD.md`

---

## 🎯 Key Endpoints

### Authentication
```
POST /api/auth/register/          # Register
POST /api/auth/login/             # Login
POST /api/auth/google/            # Google OAuth
GET  /api/auth/profile/           # Get seller profile
PUT  /api/auth/profile/           # Update profile
```

### Deals
```
POST /api/deals/                  # Create deal
GET  /api/deals/                  # List deals
GET  /api/deals/{slug}/           # Get deal
POST /api/deals/{slug}/pay/       # Get virtual account
POST /api/deals/{slug}/ship/      # Mark shipped
POST /api/deals/{slug}/confirm/   # Confirm delivery
POST /api/deals/{slug}/dispute/   # Open dispute
```

### Merchant
```
GET  /api/merchant/dashboard/     # Dashboard stats
GET  /api/merchant/deals/         # List merchant deals
GET  /api/merchant/transactions/  # Transaction history
POST /api/merchant/links/         # Create payment link
```

### Admin
```
GET  /api/admin/disputes/         # List disputes
POST /api/admin/disputes/{id}/resolve/  # Resolve dispute
```

---

## 🔥 Email Testing

By default, emails print to console (no setup needed).

**To test:**
1. Create a deal
2. Simulate payment (change status to PAID in admin)
3. Check terminal for email output
4. Mark as shipped
5. Check for shipping email
6. Confirm delivery
7. Check for delivery email

**To use real emails:**
1. Get Gmail app password
2. Add to `.env`:
   ```env
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```
3. Restart server

---

## 🎨 Google OAuth Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/accounts/google/login/callback/`
6. Copy Client ID and Secret to `.env`

---

## 🐛 Troubleshooting

### Migrations failing?
```bash
# Delete database and retry
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

### Import errors?
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Email not showing?
- Check terminal output (console backend)
- Verify `.env` if using SMTP
- Check for error messages

### Can't upload images?
```bash
# Ensure media directory exists
mkdir -p media/seller_profiles
```

---

## ✅ Verification Checklist

- [ ] Server starts without errors
- [ ] Can register new user
- [ ] Can login and get JWT token
- [ ] Can create deal
- [ ] Emails appear in console
- [ ] Can access admin panel
- [ ] Can create seller profile
- [ ] Can upload profile photo

---

## 🎉 You're Ready!

Everything is set up and working. Check the full documentation for advanced features.

**Next Steps:**
1. Test all endpoints
2. Configure Payaza credentials
3. Set up Google OAuth (optional)
4. Deploy to production

Need help? Check `PHASE1_SETUP.md` for detailed instructions.

Happy coding! 🚀
