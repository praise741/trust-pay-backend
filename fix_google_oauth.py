#!/usr/bin/env python
"""
Script to fix Google OAuth configuration
Run this in Render Shell after deployment
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.sites.models import Site

def fix_site_domain():
    """Update Django Site domain to match Render URL"""
    
    # Get Render URL from environment
    render_url = os.getenv('RENDER_EXTERNAL_URL', '')
    
    if not render_url:
        print("❌ RENDER_EXTERNAL_URL not set!")
        print("Please set it in Render Dashboard → Environment")
        print("Example: https://trustpay-backend.onrender.com")
        return False
    
    # Remove https:// prefix
    domain = render_url.replace('https://', '').replace('http://', '')
    
    try:
        # Update or create site
        site, created = Site.objects.get_or_create(id=1)
        site.domain = domain
        site.name = 'TrustPay'
        site.save()
        
        if created:
            print(f"✅ Created new site: {domain}")
        else:
            print(f"✅ Updated site domain: {domain}")
        
        print(f"\n📋 Current Site Configuration:")
        print(f"   ID: {site.id}")
        print(f"   Domain: {site.domain}")
        print(f"   Name: {site.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating site: {e}")
        return False

def check_oauth_config():
    """Check if Google OAuth is properly configured"""
    
    print("\n🔍 Checking OAuth Configuration...\n")
    
    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
    frontend_url = os.getenv('FRONTEND_URL', '')
    render_url = os.getenv('RENDER_EXTERNAL_URL', '')
    
    issues = []
    
    if not client_id:
        issues.append("❌ GOOGLE_CLIENT_ID not set")
    else:
        print(f"✅ GOOGLE_CLIENT_ID: {client_id[:20]}...")
    
    if not client_secret:
        issues.append("❌ GOOGLE_CLIENT_SECRET not set")
    else:
        print(f"✅ GOOGLE_CLIENT_SECRET: {client_secret[:10]}...")
    
    if not frontend_url:
        issues.append("❌ FRONTEND_URL not set")
    else:
        print(f"✅ FRONTEND_URL: {frontend_url}")
    
    if not render_url:
        issues.append("❌ RENDER_EXTERNAL_URL not set")
    else:
        print(f"✅ RENDER_EXTERNAL_URL: {render_url}")
    
    if issues:
        print("\n⚠️  Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    
    print("\n✅ All environment variables are set!")
    return True

def print_instructions():
    """Print instructions for Google Cloud Console"""
    
    render_url = os.getenv('RENDER_EXTERNAL_URL', 'https://YOUR-APP.onrender.com')
    frontend_url = os.getenv('FRONTEND_URL', 'https://trust-pay-frontend.vercel.app')
    
    print("\n" + "="*60)
    print("📋 NEXT STEPS: Update Google Cloud Console")
    print("="*60)
    
    print("\n1. Go to: https://console.cloud.google.com/")
    print("2. Select project: trustpay-495700")
    print("3. Go to: APIs & Services → Credentials")
    print("4. Click on your OAuth 2.0 Client ID")
    
    print("\n5. Add these Authorized Redirect URIs:")
    print(f"   {render_url}/accounts/google/login/callback/")
    print(f"   {frontend_url}/auth/callback")
    print(f"   {frontend_url}/")
    print("   http://localhost:8000/accounts/google/login/callback/")
    print("   http://localhost:3000/")
    
    print("\n6. Add these Authorized JavaScript Origins:")
    print(f"   {render_url}")
    print(f"   {frontend_url}")
    print("   http://localhost:8000")
    print("   http://localhost:3000")
    
    print("\n7. Click SAVE")
    print("\n8. Wait 5-10 minutes for changes to propagate")
    
    print("\n" + "="*60)
    print("✅ After completing these steps, Google OAuth will work!")
    print("="*60 + "\n")

if __name__ == '__main__':
    print("🔧 TrustPay - Google OAuth Fix Script")
    print("="*60 + "\n")
    
    # Check environment variables
    env_ok = check_oauth_config()
    
    # Update Django Site
    if env_ok:
        site_ok = fix_site_domain()
        
        if site_ok:
            # Print instructions
            print_instructions()
        else:
            print("\n❌ Failed to update site domain")
            print("Please check database connection and try again")
    else:
        print("\n⚠️  Please set missing environment variables in Render Dashboard")
        print("Then run this script again")
