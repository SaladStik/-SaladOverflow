#!/usr/bin/env python3
"""
Debug email configuration
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import EmailService


def debug_email_config():
    """Debug email configuration"""

    email_service = EmailService()

    print("🔍 Email Configuration Debug")
    print("=" * 50)

    print(f"SMTP Host: '{email_service.smtp_server}'")
    print(f"SMTP Port: {email_service.smtp_port}")
    print(f"SMTP Username: '{email_service.smtp_username}'")
    print(
        f"SMTP Password: '{email_service.smtp_password}' (length: {len(email_service.smtp_password)})"
    )
    print(f"From Email: '{email_service.from_email}'")
    print(f"From Name: '{email_service.from_name}'")
    print(f"Use TLS: {email_service.use_tls}")
    print(f"Frontend URL: '{email_service.base_url}'")

    print("\n📋 Configuration Check:")
    print(f"✅ SMTP Host configured: {bool(email_service.smtp_server)}")
    print(f"✅ SMTP Port configured: {bool(email_service.smtp_port)}")
    print(f"✅ Username configured: {bool(email_service.smtp_username)}")
    print(f"✅ Password configured: {bool(email_service.smtp_password)}")
    print(f"✅ From Email configured: {bool(email_service.from_email)}")

    print(f"\n🔒 Password Analysis:")
    if email_service.smtp_password:
        print(f"   Password length: {len(email_service.smtp_password)} characters")
        print(
            f"   Contains spaces: {'Yes' if ' ' in email_service.smtp_password else 'No'}"
        )
        print(f"   First 4 chars: '{email_service.smtp_password[:4]}...'")
        print(f"   Last 4 chars: '...{email_service.smtp_password[-4:]}'")
    else:
        print("   ❌ No password configured!")


if __name__ == "__main__":
    debug_email_config()
