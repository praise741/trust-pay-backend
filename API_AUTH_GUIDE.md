# Trust Pay API Authentication Guide

## Overview

This guide explains how to use the Trust Pay API authentication endpoints. The API uses JWT (JSON Web Tokens) for authentication.

## Base URL

```
http://localhost:8000/api
```

## Endpoints

### 1. API Root `/`

**GET** `http://localhost:8000/`

Returns information about available API endpoints.

**Response:**
```json
{
  "message": "Trust Pay API",
  "version": "1.0.0",
  "endpoints": {
    "auth": "/api/auth/",
    "deals": "/api/deals/",
    "admin": "/api/admin/",
    "webhooks": "/api/webhooks/",
    "merchant": "/api/merchant/",
    "buyer": "/api/buyer/"
  }
}
```

---

### 2. User Registration `/api/auth/register/`

**POST** `http://localhost:8000/api/auth/register/`

Create a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password_123",
  "phone": "08012345678",
  "is_merchant": true
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "phone": "08012345678",
  "is_merchant": true,
  "email_verified": false
}
```

**Errors:**
- `400 Bad Request`: Missing required fields or invalid data
- `400 Bad Request`: Username or email already exists

---

### 3. Email/Password Login `/api/auth/login/`

**POST** `http://localhost:8000/api/auth/login/`

Login with email and password to receive JWT tokens.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors:**
- `401 Unauthorized`: Invalid username or password

---

### 4. Google OAuth Login `/api/auth/google/`

**POST** `http://localhost:8000/api/auth/google/`

Login using a Google ID token from Google OAuth.

**Important:** You must obtain a valid Google ID token from Google's OAuth 2.0 flow.

#### How to get a Google ID token:

1. Use Google Sign-In JavaScript library
2. Use Google Sign-In for Android/iOS
3. Use any Google OAuth 2.0 library

**Request Body - Option 1 (with "token"):**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2ZjI2MjM5MjI4YWM1OTRmNDczY2U4YjY1NTAyZjU3YWM4ZjA4MDgiLCJ0eXAiOiJKV1QifQ..."
}
```

**Request Body - Option 2 (with "credential"):**
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2ZjI2MjM5MjI4YWM1OTRmNDczY2U4YjY1NTAyZjU3YWM4ZjA4MDgiLCJ0eXAiOiJKV1QifQ..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "john_smith",
    "email": "john@gmail.com",
    "first_name": "John",
    "last_name": "Smith",
    "is_merchant": false,
    "email_verified": true
  }
}
```

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Bad Request: No token provided` | Missing "token" or "credential" field | Provide a valid Google ID token in request body |
| `400 Bad Request: Invalid token format` | Token doesn't have 3 parts (e.g., "test" instead of "header.payload.signature") | Use a real Google ID token, not a test string |
| `400 Bad Request: Wrong number of segments` | Token format is invalid | Make sure you're sending a complete Google OAuth token |
| `400 Bad Request: Invalid token audience` | Token is for wrong Google app | Use token from correct Google OAuth app credentials |
| `400 Bad Request: Email not provided` | Google token missing email | Ensure email scope is requested in OAuth |
| `500 Internal Server Error: Google OAuth not configured` | Server not set up with Google credentials | Ensure GOOGLE_CLIENT_ID is set in environment variables |

---

### 5. Refresh Access Token `/api/auth/refresh/`

**POST** `http://localhost:8000/api/auth/refresh/`

Get a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token
- `400 Bad Request`: Refresh token not provided

---

### 6. Get/Update Seller Profile `/api/auth/profile/`

**GET** `http://localhost:8000/api/auth/profile/`

Get current user's seller profile (authentication required).

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": 1,
  "username": "john_doe",
  "business_name": "John's Shop",
  "business_description": "Selling quality products",
  "instagram_handle": "@johns_shop",
  "whatsapp_number": "08012345678",
  "rating": 4.5,
  "verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**
- `401 Unauthorized`: No valid token provided
- `404 Not Found`: User is not a merchant

**PUT** `http://localhost:8000/api/auth/profile/`

Update current user's seller profile (authentication required).

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body (all fields optional):**
```json
{
  "business_name": "Updated Shop Name",
  "business_description": "Updated description",
  "instagram_handle": "@updated_handle",
  "whatsapp_number": "08098765432"
}
```

**Response (200 OK):** Updated profile object

---

## Authentication

For endpoints that require authentication, include the JWT access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Validity

- **Access Token:** Valid for 24 hours
- **Refresh Token:** Valid for 7 days

## Testing with cURL

### Register User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "phone": "08012345678",
    "is_merchant": true
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Get Profile (requires authentication)
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## Common Issues & Solutions

### Issue: "Not Found: /" 
**Solution:** The root "/" endpoint now returns API information. No action needed.

### Issue: "Invalid Google token: Wrong number of segments"
**Solution:** Don't send test tokens. Use a real Google ID token from Google OAuth 2.0.

### Issue: "Bad Request: /api/auth/google/"
**Solution:** Ensure you're sending a valid Google ID token in the request body with either "token" or "credential" key.

### Issue: "Unauthorized: /api/auth/refresh/"
**Solution:** Provide the refresh token in the request body:
```json
{
  "refresh": "your_refresh_token_here"
}
```

## Environment Setup

Ensure these environment variables are set:

```env
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=your_django_secret_key
DEBUG=True  # for development only
```

## Next Steps

- Implement Google Sign-In in your frontend
- Store tokens securely (use httpOnly cookies or secure storage)
- Refresh tokens before they expire
- Never expose refresh tokens to the client side
