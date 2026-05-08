# 🔧 Fix Google OAuth Error 401: invalid_client

## ❌ Current Error:
```
Error 401: invalid_client
Request details: flowName=GeneralOAuthFlow
```

This means Google doesn't recognize your backend URL.

---

## ✅ Solution: Update Google Cloud Console

### **Step 1: Get Your Render Backend URL**

Your Render backend URL should be something like:
```
https://trustpay-backend.onrender.com
```

Or check your Render dashboard to find the exact URL.

---

### **Step 2: Go to Google Cloud Console**

1. **Visit:** https://console.cloud.google.com/
2. **Select Project:** trustpay-495700
3. **Navigate to:** APIs & Services → Credentials

---

### **Step 3: Edit OAuth 2.0 Client ID**

Click on your OAuth Client ID:
```
Client ID: 62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com
```

---

### **Step 4: Add Authorized Redirect URIs**

Add these **EXACT** URLs (replace `YOUR-RENDER-URL` with your actual Render URL):

```
https://YOUR-RENDER-URL.onrender.com/accounts/google/login/callback/
https://trust-pay-frontend.vercel.app/auth/callback
https://trust-pay-frontend.vercel.app/
http://localhost:8000/accounts/google/login/callback/
http://localhost:3000/
```

**Example (if your Render URL is trustpay-backend.onrender.com):**
```
https://trustpay-backend.onrender.com/accounts/google/login/callback/
https://trust-pay-frontend.vercel.app/auth/callback
https://trust-pay-frontend.vercel.app/
http://localhost:8000/accounts/google/login/callback/
http://localhost:3000/
```

---

### **Step 5: Add Authorized JavaScript Origins**

Add these URLs:

```
https://YOUR-RENDER-URL.onrender.com
https://trust-pay-frontend.vercel.app
http://localhost:8000
http://localhost:3000
```

**Example:**
```
https://trustpay-backend.onrender.com
https://trust-pay-frontend.vercel.app
http://localhost:8000
http://localhost:3000
```

---

### **Step 6: Save Changes**

Click **SAVE** at the bottom of the page.

⚠️ **Important:** Changes may take 5-10 minutes to propagate.

---

## 🔍 Step 7: Verify Environment Variables on Render

Make sure these are set in your **Render Dashboard → Environment**:

```env
GOOGLE_CLIENT_ID=62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
FRONTEND_URL=https://trust-pay-frontend.vercel.app
RENDER_EXTERNAL_URL=https://YOUR-RENDER-URL.onrender.com
```

---

## 🧪 Step 8: Test the Fix

### **Option A: Test from Frontend**

1. Go to: https://trust-pay-frontend.vercel.app
2. Click "Login with Google"
3. Should redirect to Google OAuth
4. After login, should redirect back to your app

### **Option B: Test Directly**

Visit this URL in your browser (replace YOUR-RENDER-URL):
```
https://YOUR-RENDER-URL.onrender.com/accounts/google/login/
```

Should redirect to Google login page.

---

## 🔍 Common Issues & Solutions

### **Issue 1: Still getting 401 after adding URLs**
**Solution:** Wait 5-10 minutes for Google to propagate changes, then try again.

### **Issue 2: "Redirect URI mismatch"**
**Solution:** The URL must match EXACTLY (including trailing slash `/`). Check:
- `https://` (not `http://`)
- Correct domain
- `/accounts/google/login/callback/` (with trailing slash)

### **Issue 3: "Access blocked: This app's request is invalid"**
**Solution:** 
1. Make sure OAuth consent screen is configured
2. Add test users if app is in testing mode
3. Verify scopes are correct (profile, email)

### **Issue 4: Environment variables not loading**
**Solution:**
1. Check Render dashboard → Environment tab
2. Make sure variables are saved
3. Redeploy the service after adding variables

---

## 📋 Checklist

- [ ] Found my Render backend URL
- [ ] Logged into Google Cloud Console
- [ ] Selected project: trustpay-495700
- [ ] Went to APIs & Services → Credentials
- [ ] Clicked on OAuth 2.0 Client ID
- [ ] Added Authorized Redirect URIs (with Render URL)
- [ ] Added Authorized JavaScript Origins (with Render URL)
- [ ] Clicked SAVE
- [ ] Waited 5-10 minutes
- [ ] Verified environment variables on Render
- [ ] Tested Google login

---

## 🎯 Quick Reference

### **Your Google OAuth Credentials:**
```
Client ID: 62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com
Client Secret: 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
```

### **Required Redirect URI Format:**
```
https://[YOUR-BACKEND-DOMAIN]/accounts/google/login/callback/
```

### **Frontend URL:**
```
https://trust-pay-frontend.vercel.app
```

---

## 🆘 Still Not Working?

### **Debug Steps:**

1. **Check Render Logs:**
   - Go to Render Dashboard → Your Service → Logs
   - Look for OAuth-related errors

2. **Check Environment Variables:**
   ```bash
   # In Render Shell
   echo $GOOGLE_CLIENT_ID
   echo $GOOGLE_CLIENT_SECRET
   ```

3. **Verify Django Settings:**
   - Make sure `allauth` is installed
   - Check `SOCIALACCOUNT_PROVIDERS` in settings.py
   - Verify `SITE_ID = 1`

4. **Check Django Sites Framework:**
   ```bash
   # In Render Shell
   python manage.py shell
   >>> from django.contrib.sites.models import Site
   >>> site = Site.objects.get_current()
   >>> print(site.domain)
   # Should show your Render domain
   ```

5. **Update Site Domain:**
   ```bash
   # In Render Shell
   python manage.py shell
   >>> from django.contrib.sites.models import Site
   >>> site = Site.objects.get(id=1)
   >>> site.domain = 'your-render-url.onrender.com'
   >>> site.name = 'TrustPay'
   >>> site.save()
   ```

---

## 📞 Need More Help?

**Google OAuth Docs:** https://developers.google.com/identity/protocols/oauth2  
**Django Allauth Docs:** https://django-allauth.readthedocs.io/  
**Render Docs:** https://render.com/docs

---

## ✅ Expected Result

After fixing, you should see:
1. ✅ Google login page appears
2. ✅ User can select Google account
3. ✅ User is redirected back to your app
4. ✅ JWT tokens are generated
5. ✅ User is logged in

---

**Last Updated:** May 8, 2026  
**Status:** Awaiting Google Cloud Console update
