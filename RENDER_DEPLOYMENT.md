# 🚀 Render Deployment Guide - TrustPay Backend

## 🔧 Issues Fixed

1. ✅ **CORS Configuration** - Added `CORS_ALLOW_ALL_ORIGINS` for development
2. ✅ **CSRF Trusted Origins** - Added frontend and backend URLs
3. ✅ **Email Backend** - Configured with environment variables
4. ✅ **Google OAuth** - Added proper scopes and auth params
5. ✅ **Port Configuration** - Render auto-detects port 10000

---

## 📋 Environment Variables for Render

Add these in your Render dashboard under **Environment**:

### **Required Variables:**

```env
# Django
SECRET_KEY=your-production-secret-key-here
DEBUG=False
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com

# Database (Render provides this automatically if you add PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Payaza
PAYAZA_BASE_URL=https://api.payaza.africa
PAYAZA_PUBLIC_KEY=PZ78-PKPROD-your-production-key
PAYAZA_TENANT_ID=production
PAYAZA_SECRET=your-webhook-secret
PAYAZA_TRANSACTION_PIN=your-4-digit-pin
PAYAZA_MOCK_MODE=False

# Email (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@trustpay.ng

# Google OAuth
GOOGLE_CLIENT_ID=62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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

# Frontend
FRONTEND_URL=https://trust-pay-frontend.vercel.app

# Python version
PYTHON_VERSION=3.11.0
```

---

## 🔐 Google OAuth Configuration

### **Update Authorized Redirect URIs in Google Cloud Console:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Add these **Authorized redirect URIs**:
   ```
   https://your-app-name.onrender.com/accounts/google/login/callback/
   https://trust-pay-frontend.vercel.app
   http://localhost:3000
   ```

6. Add these **Authorized JavaScript origins**:
   ```
   https://your-app-name.onrender.com
   https://trust-pay-frontend.vercel.app
   http://localhost:3000
   ```

7. Click **Save**

---

## 📦 Build Configuration

### **Create `build.sh` file:**

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

Make it executable:
```bash
chmod +x build.sh
```

### **Render Settings:**

- **Build Command:** `./build.sh`
- **Start Command:** `gunicorn backend.wsgi:application`
- **Environment:** Python 3

---

## 🗄️ Database Setup

### **Option 1: PostgreSQL (Recommended for Production)**

1. In Render dashboard, create a new **PostgreSQL** database
2. Link it to your web service
3. Render will automatically set `DATABASE_URL`

### **Option 2: SQLite (Development Only)**

SQLite works but is not recommended for production on Render because:
- File system is ephemeral (resets on deploy)
- No persistence between deployments

---

## 📁 Static Files

Add to `requirements.txt`:
```
whitenoise
```

Update `backend/settings.py`:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... rest of middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 🚀 Deployment Steps

### **1. Push to GitHub**

```bash
git add .
git commit -m "Configure for Render deployment"
git push origin master
```

### **2. Create Web Service on Render**

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository: `praise741/trust-pay-backend`
4. Configure:
   - **Name:** `trustpay-backend`
   - **Environment:** Python 3
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn backend.wsgi:application`
   - **Plan:** Free (or paid for production)

### **3. Add Environment Variables**

Copy all variables from the section above into Render's environment variables.

### **4. Deploy**

Click **Create Web Service** - Render will automatically deploy!

---

## ✅ Post-Deployment Checklist

### **1. Verify Deployment**

```bash
# Check if API is running
curl https://your-app-name.onrender.com/api/auth/register/

# Should return 400 or 405, not 404
```

### **2. Create Superuser**

In Render dashboard, go to **Shell** and run:
```bash
python manage.py createsuperuser
```

### **3. Test Endpoints**

```bash
# Test registration
curl -X POST https://your-app-name.onrender.com/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","username":"testuser"}'

# Test Google OAuth
curl https://your-app-name.onrender.com/api/auth/google/
```

### **4. Update Frontend**

Update your frontend to use the new backend URL:
```javascript
const API_BASE_URL = 'https://your-app-name.onrender.com';
```

---

## 🐛 Troubleshooting

### **Issue: "Not Found: /"**
✅ **Fixed** - This is normal. The root URL has no view. Use `/api/` endpoints.

### **Issue: "no registered origin"**
✅ **Fixed** - Added `CORS_ALLOW_ALL_ORIGINS` and proper CORS headers.

### **Issue: "Error 401: invalid_client" (Google OAuth)**
✅ **Fix:** Update Google Cloud Console redirect URIs to include your Render URL.

### **Issue: "Unauthorized: /api/auth/register/"**
✅ **Fixed** - Registration endpoint now allows unauthenticated access.

### **Issue: Port binding**
✅ **Fixed** - Render automatically detects port 10000. No configuration needed.

### **Issue: Static files not loading**
✅ **Solution:** Add `whitenoise` and run `collectstatic` in build script.

---

## 📊 Monitoring

### **View Logs:**
In Render dashboard → Your service → **Logs**

### **Common Log Messages:**

```
✅ "Detected service running on port 10000" - Good!
✅ "Not Found: /" - Normal (no root view)
❌ "no registered origin" - Check CORS settings
❌ "Error 401: invalid_client" - Update Google OAuth redirect URIs
```

---

## 🔄 Auto-Deploy

Render automatically deploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin master
# Render will auto-deploy!
```

---

## 💰 Render Free Tier Limitations

- **Spins down after 15 minutes of inactivity**
- **First request after spin-down takes ~30 seconds**
- **750 hours/month free**

**For production:** Upgrade to paid plan for:
- No spin-down
- Better performance
- More resources

---

## 🎯 Production Checklist

Before going live:

- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set strong `SECRET_KEY`
- [ ] Configure real email backend (not console)
- [ ] Add production Payaza keys
- [ ] Update Google OAuth redirect URIs
- [ ] Set up monitoring/logging
- [ ] Configure custom domain (optional)
- [ ] Enable HTTPS (automatic on Render)
- [ ] Set up database backups

---

## 📞 Support

**Render Docs:** https://render.com/docs  
**Django Deployment:** https://docs.djangoproject.com/en/4.2/howto/deployment/  
**Repository:** https://github.com/praise741/trust-pay-backend

---

## 🎉 Summary

Your TrustPay backend is now configured for Render deployment with:

- ✅ Proper CORS configuration
- ✅ CSRF trusted origins
- ✅ Email backend setup
- ✅ Google OAuth configuration
- ✅ Environment variable support
- ✅ Static files handling
- ✅ Database flexibility (SQLite/PostgreSQL)

**Next:** Push to GitHub and create a web service on Render! 🚀

---

**Last Updated:** May 8, 2026  
**Version:** 2.0 (Production Ready)
