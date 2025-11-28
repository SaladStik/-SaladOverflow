#!/usr/bin/env python3
"""
Send a test email to verify the email service is working
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import EmailService


async def send_test_email():
    """Send a test email to nick@saladsync.ca"""

    email_service = EmailService()

    print("📧 Sending test email to nick@saladsync.ca")
    print("=" * 50)

    # Test email details
    to_email = "nick@saladsync.ca"
    subject = "🧪 SaladOverflow Email Test"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Email Test - SaladOverflow</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: white; padding: 30px; border: 1px solid #dee2e6; }}
            .footer {{ background: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #6c757d; }}
            .success {{ background: #d4edda; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #28a745; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; color: #28a745;">🥗 SaladOverflow</h1>
                <p style="margin: 10px 0 0 0;">Email System Test</p>
            </div>
            
            <div class="content">
                <h2>Hello Nick! 👋</h2>
                
                <div class="success">
                    <strong>✅ Email System Test Successful!</strong><br>
                    Your SaladOverflow email service is working perfectly.
                </div>
                
                <p>This is a test email to verify that the SaladOverflow email system is properly configured and working.</p>
                
                <p><strong>Email Configuration Details:</strong></p>
                <ul>
                    <li>📧 <strong>From:</strong> {email_service.from_email}</li>
                    <li>🏷️ <strong>From Name:</strong> {email_service.from_name}</li>
                    <li>🌐 <strong>SMTP Host:</strong> {email_service.smtp_server}</li>
                    <li>🔌 <strong>SMTP Port:</strong> {email_service.smtp_port}</li>
                    <li>🔒 <strong>TLS Enabled:</strong> {email_service.use_tls}</li>
                    <li>🌍 <strong>Frontend URL:</strong> {email_service.base_url}</li>
                </ul>
                
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>📅 <strong>Test Date:</strong> {datetime.now().strftime("%B %d, %Y")}</li>
                    <li>🕒 <strong>Test Time:</strong> {datetime.now().strftime("%I:%M %p")}</li>
                    <li>📍 <strong>Test Email:</strong> {to_email}</li>
                </ul>
                
                <p>If you're receiving this email, it means:</p>
                <ul>
                    <li>✅ SMTP connection is working</li>
                    <li>✅ Gmail authentication is successful</li>
                    <li>✅ Email templates are rendering correctly</li>
                    <li>✅ TLS encryption is functioning</li>
                    <li>✅ The system is ready for production</li>
                </ul>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                
                <p><small>This is an automated test email from the SaladOverflow development environment.</small></p>
            </div>
            
            <div class="footer">
                <p>&copy; 2025 SaladOverflow. Email system test successful! 🎉</p>
                <p>This is an automated test message.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    SaladOverflow Email System Test
    
    Hello Nick!
    
    This is a test email to verify that the SaladOverflow email system is properly configured and working.
    
    Email Configuration:
    - From: {email_service.from_email}
    - From Name: {email_service.from_name}
    - SMTP Host: {email_service.smtp_server}
    - SMTP Port: {email_service.smtp_port}
    - TLS Enabled: {email_service.use_tls}
    - Frontend URL: {email_service.base_url}
    
    Test Details:
    - Test Date: {datetime.now().strftime("%B %d, %Y")}
    - Test Time: {datetime.now().strftime("%I:%M %p")}
    - Test Email: {to_email}
    
    If you're receiving this email, it means:
    ✅ SMTP connection is working
    ✅ Gmail authentication is successful
    ✅ Email templates are rendering correctly
    ✅ TLS encryption is functioning
    ✅ The system is ready for production
    
    This is an automated test email from the SaladOverflow development environment.
    
    - The SaladOverflow Team
    """

    # Send the test email
    try:
        print(f"📤 Sending test email...")
        print(f"   To: {to_email}")
        print(f"   From: {email_service.from_name} <{email_service.from_email}>")
        print(f"   Subject: {subject}")

        success = email_service._send_email(
            to_email, subject, html_content, text_content
        )

        if success:
            print("✅ Test email sent successfully!")
            print(f"📧 Check {to_email} for the test email.")
            print("\n🎉 Your SaladOverflow email system is working perfectly!")
        else:
            print("❌ Failed to send test email!")
            print("Check the logs for error details.")

        return success

    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(send_test_email())
