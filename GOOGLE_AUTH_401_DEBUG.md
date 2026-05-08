# Google OAuth 401 Unauthorized Error - Debugging Guide

## Problem
Getting 401 Unauthorized when calling `POST https://trust-pay-backend-v78l.onrender.com/api/auth/google/`

## Possible Causes

### 1. **Missing Environment Variables on Render** (Most Likely)
The deployed backend on Render doesn't have the Google OAuth credentials set.

**Solution:** Add these environment variables in Render Dashboard:
- `GOOGLE_CLIENT_ID=62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com`
- `GOOGLE_CLIENT_SECRET=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`

### 2. **CORS Preflight Failure**
The browser might be blocking the request due to CORS.

**Check:** Look in browser console for CORS errors before the 401.

### 3. **Wrong Google Client ID**
The Google token was generated for a different Client ID than what's configured on the backend.

**Solution:** Make sure the frontend is using the same Client ID that's configured in Render.

### 4. **Token Format Issue**
The token being sent might not be in the correct format.

**Check:** The token should be a JWT with 3 parts separated by dots.

## How to Fix

### Step 1: Set Environment Variables on Render

1. Go to your Render dashboard: https://dashboard.render.com/
2. Select your `trust-pay-backend-v78l` service
3. Go to "Environment" tab
4. Add these variables:
   ```
   GOOGLE_CLIENT_ID=62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=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
   ```
5. Save and wait for the service to redeploy

### Step 2: Verify Frontend Configuration

Make sure your frontend is using the correct Google Client ID:
```javascript
// Should match the one in Render environment variables
const GOOGLE_CLIENT_ID = "62451695606-fdhgitv0r348q278caloqotv8pgsq9hm.apps.googleusercontent.com";
```

### Step 3: Check Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials
2. Find your OAuth 2.0 Client ID
3. Verify these Authorized JavaScript origins:
   - `https://trust-pay-frontend.vercel.app`
   - `https://trust-pay-backend-v78l.onrender.com`
   - `http://localhost:3000` (for development)

4. Verify these Authorized redirect URIs:
   - `https://trust-pay-frontend.vercel.app`
   - `https://trust-pay-frontend.vercel.app/auth/callback`
   - `http://localhost:3000` (for development)

### Step 4: Test the Endpoint

After setting environment variables, test with curl:

```bash
# This should return 400 with "Google token is required" message
curl -X POST https://trust-pay-backend-v78l.onrender.com/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{}'

# If you get 401, the endpoint is being blocked by authentication middleware
# If you get 400 with error message, the endpoint is working correctly
```

## Expected Behavior

- **Without token:** 400 Bad Request with message "Google token is required"
- **With invalid token:** 400 Bad Request with message "Invalid Google token"
- **With valid token:** 200 OK with JWT tokens and user data
- **If GOOGLE_CLIENT_ID not set:** 500 Internal Server Error with "Google OAuth not configured"

## Current Status

The endpoint is configured correctly in the code with:
- `@permission_classes([AllowAny])` - No authentication required
- Proper error handling
- CORS headers configured

The 401 error suggests either:
1. Environment variables are missing on Render (most likely)
2. There's a middleware intercepting the request
3. CORS preflight is failing

## Next Steps

1. **Immediately:** Add Google OAuth environment variables to Render
2. **Verify:** Check Render logs after redeployment
3. **Test:** Try the Google login again from frontend
4. **Debug:** If still failing, check Render logs for the actual error message
