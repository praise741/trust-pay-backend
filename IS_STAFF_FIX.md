# is_staff Field Fix - Authentication Response

## Problem
The frontend was expecting an `is_staff` flag in the authentication response to determine user roles, but it wasn't being included in either:
- Normal login (JWT token endpoint)
- Google OAuth login

This caused the frontend to treat users as unauthorized and redirect back to the login page.

## Solution
Added `is_staff` field to all authentication responses.

## Changes Made

### 1. **users/serializers.py**
- Created `CustomTokenObtainPairSerializer` that extends `TokenObtainPairSerializer`
- This custom serializer adds user data including `is_staff` to the JWT token response
- Updated `UserSerializer` to include `is_staff` field

### 2. **users/views.py**
- Created `CustomTokenObtainPairView` that uses the custom serializer
- This replaces the default `TokenObtainPairView` for the login endpoint

### 3. **users/urls.py**
- Updated login endpoint to use `CustomTokenObtainPairView` instead of default `TokenObtainPairView`

### 4. **users/google_auth.py**
- Added `is_staff` field to the user data in the Google OAuth response

## Response Format

### Normal Login (POST /api/auth/login/)
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "1234567890",
    "is_merchant": false,
    "is_staff": false,
    "email_verified": true
  }
}
```

### Google OAuth Login (POST /api/auth/google/)
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_merchant": false,
    "is_staff": false,
    "email_verified": true
  }
}
```

## Testing
To test the fix:

1. **Normal Login:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "password123"}'
   ```

2. **Google OAuth:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/google/ \
     -H "Content-Type: application/json" \
     -d '{"token": "YOUR_GOOGLE_ID_TOKEN"}'
   ```

Both responses should now include the `is_staff` field in the user object.

## Notes
- The `is_staff` field comes from Django's `AbstractUser` model, which the custom `User` model extends
- Regular users will have `is_staff: false`
- Admin users created via Django admin or with `is_staff=True` will have `is_staff: true`
- The frontend can now use this field to determine if a user has admin/staff privileges
