import os
import logging
import smtplib
import secrets
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for user verification and notifications
    """

    def __init__(self):
        self.smtp_server = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = (
            settings.smtp_from_email if settings.smtp_from_email else self.smtp_username
        )
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls
        self.base_url = settings.frontend_url
        self.backend_url = settings.backend_url

    def _create_smtp_connection(self):
        """Create and return SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise

    def _send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str = None
    ) -> bool:
        """Send email with HTML and optional text content"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text version if provided
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def generate_verification_token(self, length: int = 32) -> str:
        """Generate a secure random token for email verification"""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email to user"""
        try:
            verification_url = f"{self.base_url}/auth/verify-email?token={verification_token}&email={user.email}"

            subject = "Welcome to SaladOverflow - Verify Your Email"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Email - SaladOverflow</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #dee2e6; }}
                    .footer {{ background: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #6c757d; }}
                    .btn {{ display: inline-block; padding: 12px 30px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                    .btn:hover {{ background: #218838; }}
                    .highlight {{ background: #fff3cd; padding: 10px; border-radius: 4px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0; color: #28a745;">SaladOverflow</h1>
                        <p style="margin: 10px 0 0 0;">Welcome to the freshest Q&A community!</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user.display_name}</h2>
                        
                        <p>Thank you for joining SaladOverflow! You're just one step away from being part of our amazing community.</p>
                        
                        <p>To complete your registration and start asking questions, sharing knowledge, and earning karma, please verify your email address:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" class="btn">Verify My Email</a>
                        </div>
                        
                        <div class="highlight">
                            <strong>Email:</strong> {user.email}<br>
                            <strong>Username:</strong> @{user.display_name}<br>
                            <strong>Joined:</strong> {user.created_at.strftime("%B %d, %Y")}
                        </div>
                        
                        <p><strong>What's next after verification?</strong></p>
                        <ul>
                            <li><strong>Upload a profile image</strong> to make your profile stand out</li>
                            <li><strong>Complete your bio</strong> to tell the community about yourself</li>
                            <li><strong>Ask your first question</strong> or help others by answering</li>
                            <li><strong>Start earning karma</strong> by contributing quality content</li>
                        </ul>
                        
                        <p><strong>Welcome to the community!</strong></p>
                        <p>We're excited to have you join our growing community of developers, programmers, and tech enthusiasts sharing knowledge and helping each other solve problems.</p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
                        
                        <p><small>If you didn't create an account with SaladOverflow, you can safely ignore this email.</small></p>
                        
                        <p><small>This verification link will expire in 24 hours. If the button doesn't work, copy and paste this URL into your browser:<br>
                        <code style="background: #f8f9fa; padding: 5px; word-break: break-all;">{verification_url}</code></small></p>
                    </div>
                    
                    <div class="footer">
                        <p>&copy; 2025 SaladOverflow. Made for the developer community.</p>
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
            Welcome to SaladOverflow!
            
            Hi {user.display_name},
            
            Thank you for joining SaladOverflow! Please verify your email address to complete your registration:
            
            Verification URL: {verification_url}
            
            Email: {user.email}
            Username: @{user.display_name}
            Joined: {user.created_at.strftime("%B %d, %Y")}
            
            What's next after verification?
            - Upload a profile image to make your profile stand out
            - Complete your bio to tell the community about yourself  
            - Ask your first question or help others by answering
            - Start earning karma by contributing quality content
            
            Welcome to the community! We're excited to have you join our growing community of developers, programmers, and tech enthusiasts.
            
            This verification link will expire in 24 hours.
            
            If you didn't create an account with SaladOverflow, you can safely ignore this email.
            
            - The SaladOverflow Team
            """

            return self._send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            return False

    def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """Send password reset email to user"""
        try:
            reset_url = f"{self.base_url}/auth/reset-password?token={reset_token}&email={user.email}"

            # Get logo URL (served from backend static files)
            logo_url = f"{self.backend_url}/static/img/logo.png"

            subject = "SaladOverflow - Password Reset Request"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reset Your Password</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #222725;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #222725;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #121113; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 2px solid #899878;">
                                        <img src="{logo_url}" alt="SaladOverflow" style="max-width: 120px; height: auto; margin-bottom: 20px;">
                                        <h1 style="margin: 0; color: #F7F7F2; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">Password Reset Request</h1>
                                    </td>
                                </tr>
                                
                                <!-- Main Content -->
                                <tr>
                                    <td style="padding: 40px 40px 30px;">
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            Hello {user.display_name},
                                        </p>
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            We received a request to reset the password for your SaladOverflow account. If you made this request, click the button below to create a new password.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- CTA Button -->
                                <tr>
                                    <td style="padding: 0 40px 30px; text-align: center;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background-color: #899878; border-radius: 6px; padding: 16px 40px;">
                                                    <a href="{reset_url}" style="color: #121113; text-decoration: none; font-size: 16px; font-weight: 600; display: inline-block;">
                                                        Reset Your Password
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Alternative Link -->
                                <tr>
                                    <td style="padding: 0 40px 30px;">
                                        <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.6; opacity: 0.9;">
                                            If the button above doesn't work, copy and paste this link into your browser:
                                        </p>
                                        <div style="padding: 14px; background-color: #222725; border-radius: 6px; border: 1px solid #899878;">
                                            <p style="margin: 0; color: #899878; font-size: 13px; word-break: break-all; font-family: 'Courier New', monospace;">
                                                {reset_url}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Important Info Box -->
                                <tr>
                                    <td style="padding: 0 40px 40px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 20px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                                    <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.5; font-weight: 600;">
                                                        Important Security Information
                                                    </p>
                                                    <p style="margin: 0 0 10px; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        This password reset link will expire in 1 hour for security reasons.
                                                    </p>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #222725; border-top: 1px solid #899878;">
                                        <p style="margin: 0 0 10px; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.8;">
                                            If you're having trouble or didn't request this reset, please contact our support team.
                                        </p>
                                        <p style="margin: 0; color: #F7F7F2; font-size: 12px; opacity: 0.6; line-height: 1.4;">
                                            This is an automated security email from SaladOverflow. Please do not reply to this message.
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            text_content = f"""
            Password Reset Request - SaladOverflow
            
            Hello {user.display_name},
            
            We received a request to reset the password for your SaladOverflow account. If you made this request, use the link below to create a new password.
            
            Reset URL: {reset_url}
            
            Important Security Information:
            - This password reset link will expire in 1 hour for security reasons.
            - If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
            
            If you're having trouble or didn't request this reset, please contact our support team.
            
            This is an automated security email from SaladOverflow. Please do not reply to this message.
            
            - The SaladOverflow Team
            """

            return self._send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return False

    def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to newly registered user"""
        try:
            subject = "Welcome to SaladOverflow"

            # Get logo URL (served from backend static files)
            logo_url = f"{self.backend_url}/static/img/logo.png"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to SaladOverflow</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #222725;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #222725;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #121113; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 2px solid #899878;">
                                        <img src="{logo_url}" alt="SaladOverflow" style="max-width: 120px; height: auto; margin-bottom: 20px;">
                                        <h1 style="margin: 0; color: #F7F7F2; font-size: 28px; font-weight: 600; letter-spacing: -0.5px;">Welcome to SaladOverflow</h1>
                                    </td>
                                </tr>
                                
                                <!-- Main Content -->
                                <tr>
                                    <td style="padding: 40px 40px 30px;">
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            Hello {user.display_name},
                                        </p>
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            We're delighted to have you join our community of developers, problem-solvers, and knowledge seekers. You're now part of a platform where curiosity meets expertise.
                                        </p>
                                        <p style="margin: 0 0 30px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            Whether you're here to ask questions, share your knowledge, or simply learn from others, you've come to the right place.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Getting Started Section -->
                                <tr>
                                    <td style="padding: 0 40px 30px;">
                                        <h2 style="margin: 0 0 20px; color: #899878; font-size: 20px; font-weight: 600;">Getting Started</h2>
                                        
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 16px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878; margin-bottom: 12px;">
                                                    <h3 style="margin: 0 0 8px; color: #F7F7F2; font-size: 16px; font-weight: 600;">Ask Your First Question</h3>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        Don't be shy. Share what you're working on and what's puzzling you. Our community is here to help.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <div style="height: 12px;"></div>
                                        
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 16px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878; margin-bottom: 12px;">
                                                    <h3 style="margin: 0 0 8px; color: #F7F7F2; font-size: 16px; font-weight: 600;">Answer and Contribute</h3>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        Browse questions in your areas of expertise. Every answer helps build our collective knowledge.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <div style="height: 12px;"></div>
                                        
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 16px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                                    <h3 style="margin: 0 0 8px; color: #F7F7F2; font-size: 16px; font-weight: 600;">Build Your Reputation</h3>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        Earn karma points through quality contributions. Help others and watch your standing grow.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- CTA Button -->
                                <tr>
                                    <td style="padding: 0 40px 40px; text-align: center;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background-color: #899878; border-radius: 6px; padding: 14px 32px;">
                                                    <a href="{self.base_url}" style="color: #121113; text-decoration: none; font-size: 16px; font-weight: 600; display: inline-block;">
                                                        Explore the Community
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #222725; border-top: 1px solid #899878;">
                                        <p style="margin: 0 0 10px; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.8;">
                                            Questions? We're here to help. Visit our community or reach out to our support team.
                                        </p>
                                        <p style="margin: 0; color: #F7F7F2; font-size: 12px; opacity: 0.6; line-height: 1.4;">
                                            You're receiving this email because you recently created an account on SaladOverflow.
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            text_content = f"""
            Welcome to SaladOverflow!
            
            Hello {user.display_name},
            
            We're delighted to have you join our community of developers, problem-solvers, and knowledge seekers. You're now part of a platform where curiosity meets expertise.
            
            Whether you're here to ask questions, share your knowledge, or simply learn from others, you've come to the right place.
            
            Getting Started:
            
            1. Ask Your First Question
               Don't be shy. Share what you're working on and what's puzzling you. Our community is here to help.
            
            2. Answer and Contribute
               Browse questions in your areas of expertise. Every answer helps build our collective knowledge.
            
            3. Build Your Reputation
               Earn karma points through quality contributions. Help others and watch your standing grow.
            
            Explore the Community: {self.base_url}
            
            Questions? We're here to help. Visit our community or reach out to our support team.
            
            You're receiving this email because you recently created an account on SaladOverflow.
            
            - The SaladOverflow Team
            """

            return self._send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
            return False

    def send_post_created_notification(
        self, user: User, post_title: str, post_id: int, post_slug: str
    ) -> bool:
        """Send email notification to user when they create a post"""
        try:
            post_url = f"{self.base_url}/posts/{post_id}"
            logo_url = f"{self.backend_url}/static/img/logo.png"

            subject = "Your Question Is Live on SaladOverflow"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Your Question Has Been Posted</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #222725;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #222725;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #121113; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 30px; border-bottom: 2px solid #899878;">
                                        <img src="{logo_url}" alt="SaladOverflow" style="max-width: 120px; height: auto; margin-bottom: 20px;">
                                        <h1 style="margin: 0 0 8px; color: #F7F7F2; font-size: 24px; font-weight: 600; letter-spacing: -0.5px;">Your Question Is Live</h1>
                                        <p style="margin: 0; color: #899878; font-size: 14px;">Successfully posted to SaladOverflow</p>
                                    </td>
                                </tr>
                                
                                <!-- Main Content -->
                                <tr>
                                    <td style="padding: 30px 40px 20px;">
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            Hello {user.display_name},
                                        </p>
                                        <p style="margin: 0 0 20px; color: #F7F7F2; font-size: 16px; line-height: 1.6;">
                                            Your question has been posted successfully and is now visible to the community.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Question Details -->
                                <tr>
                                    <td style="padding: 0 40px 20px;">
                                        <div style="padding: 24px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                            <p style="margin: 0 0 8px; color: #899878; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Your Question</p>
                                            <h2 style="margin: 0 0 16px; color: #F7F7F2; font-size: 18px; line-height: 1.4; font-weight: 600;">
                                                {post_title}
                                            </h2>
                                            <p style="margin: 0; color: #F7F7F2; font-size: 14px; opacity: 0.7;">
                                                Posted on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Post Link -->
                                <tr>
                                    <td style="padding: 0 40px 30px;">
                                        <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.6; opacity: 0.9;">
                                            You can view or share your question using this link:
                                        </p>
                                        <div style="padding: 14px; background-color: #222725; border-radius: 6px; border: 1px solid #899878;">
                                            <p style="margin: 0; color: #899878; font-size: 13px; word-break: break-all; font-family: 'Courier New', monospace;">
                                                {post_url}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- CTA Button -->
                                <tr>
                                    <td style="padding: 0 40px 40px; text-align: center;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background-color: #899878; border-radius: 6px; padding: 16px 40px;">
                                                    <a href="{post_url}" style="color: #121113; text-decoration: none; font-size: 16px; font-weight: 600; display: inline-block;">
                                                        View Your Question
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Info Box -->
                                <tr>
                                    <td style="padding: 0 40px 40px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 20px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                                    <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.5; font-weight: 600;">
                                                        What Happens Next
                                                    </p>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        Community members can now view and respond to your question. You'll receive email notifications when someone posts an answer or comments on your question.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #222725; border-top: 1px solid #899878;">
                                        <p style="margin: 0 0 10px; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.8;">
                                            This is a confirmation that your post was successfully published on SaladOverflow.
                                        </p>
                                        <p style="margin: 0; color: #F7F7F2; font-size: 12px; opacity: 0.6; line-height: 1.4;">
                                            This is an automated notification. Please do not reply to this email.
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            text_content = f"""
            Your Question Is Live - SaladOverflow
            
            Hello {user.display_name},
            
            Your question has been posted successfully and is now visible to the community.
            
            Your Question: {post_title}
            Posted on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
            
            View your question: {post_url}
            
            What Happens Next:
            Community members can now view and respond to your question. You'll receive email notifications when someone posts an answer or comments on your question.
            
            This is a confirmation that your post was successfully published on SaladOverflow.
            
            - The SaladOverflow Team
            """

            return self._send_email(user.email, subject, html_content, text_content)

        except Exception as e:
            logger.error(
                f"Failed to send post created notification to {user.email}: {e}"
            )
            return False

    def send_new_answer_notification(
        self,
        post_author: User,
        answerer: User,
        post_title: str,
        post_id: int,
        post_slug: str,
        answer_content_plain: str,
        answerer_karma: int,
    ) -> bool:
        """Send email notification to post author when someone answers their question"""
        try:
            post_url = f"{self.base_url}/posts/{post_id}"
            logo_url = f"{self.backend_url}/static/img/logo.png"

            # Truncate answer preview to ~200 characters
            answer_preview = (
                answer_content_plain[:200] + "..."
                if len(answer_content_plain) > 200
                else answer_content_plain
            )

            subject = f"New Response to Your Question on SaladOverflow"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>New Response to Your Post</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #222725;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #222725;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #121113; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 30px; border-bottom: 2px solid #899878;">
                                        <img src="{logo_url}" alt="SaladOverflow" style="max-width: 120px; height: auto; margin-bottom: 20px;">
                                        <h1 style="margin: 0 0 8px; color: #F7F7F2; font-size: 24px; font-weight: 600; letter-spacing: -0.5px;">New Response to Your Question</h1>
                                        <p style="margin: 0; color: #899878; font-size: 14px;">Someone has answered your question on SaladOverflow</p>
                                    </td>
                                </tr>
                                
                                <!-- User Info -->
                                <tr>
                                    <td style="padding: 30px 40px 20px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <p style="margin: 0; color: #899878; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Answered by</p>
                                                    <p style="margin: 6px 0 0; color: #F7F7F2; font-size: 16px; font-weight: 500;">{answerer.display_name}</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 13px; opacity: 0.7;">Karma: {answerer_karma:,}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Original Question Context -->
                                <tr>
                                    <td style="padding: 0 40px 20px;">
                                        <div style="padding: 16px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                            <p style="margin: 0 0 8px; color: #899878; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Your Question</p>
                                            <p style="margin: 0; color: #F7F7F2; font-size: 15px; line-height: 1.5; font-weight: 500;">
                                                {post_title}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Answer Preview -->
                                <tr>
                                    <td style="padding: 0 40px 30px;">
                                        <p style="margin: 0 0 12px; color: #899878; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Answer Preview</p>
                                        <div style="padding: 20px; background-color: #222725; border-radius: 6px; border: 1px solid rgba(137, 152, 120, 0.3);">
                                            <p style="margin: 0; color: #F7F7F2; font-size: 15px; line-height: 1.6; opacity: 0.95;">
                                                {answer_preview}
                                            </p>
                                            <p style="margin: 16px 0 0; color: #899878; font-size: 14px; font-style: italic;">
                                                Read the complete answer on SaladOverflow
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- CTA Button -->
                                <tr>
                                    <td style="padding: 0 40px 40px; text-align: center;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background-color: #899878; border-radius: 6px; padding: 16px 40px;">
                                                    <a href="{post_url}" style="color: #121113; text-decoration: none; font-size: 16px; font-weight: 600; display: inline-block;">
                                                        View Full Answer
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Engagement Box -->
                                <tr>
                                    <td style="padding: 0 40px 40px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 20px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                                    <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.5; font-weight: 600;">
                                                        Did this answer help?
                                                    </p>
                                                    <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.9;">
                                                        If this answer solved your problem, consider marking it as accepted to help others find the solution. You can also upvote helpful answers to support the community.
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #222725; border-top: 1px solid #899878;">
                                        <p style="margin: 0 0 10px; color: #F7F7F2; font-size: 14px; line-height: 1.5; opacity: 0.8;">
                                            You can manage your email notification preferences in your account settings.
                                        </p>
                                        <p style="margin: 0; color: #F7F7F2; font-size: 12px; opacity: 0.6; line-height: 1.4;">
                                            You're receiving this email because you asked a question on SaladOverflow and someone has responded.
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            text_content = f"""
            New Response to Your Question - SaladOverflow
            
            Hello {post_author.display_name},
            
            Someone has answered your question on SaladOverflow!
            
            Answered by: {answerer.display_name}
            Karma: {answerer_karma:,}
            
            Your Question: {post_title}
            
            Answer Preview:
            {answer_preview}
            
            Read the complete answer: {post_url}
            
            Did this answer help?
            If this answer solved your problem, consider marking it as accepted to help others find the solution. You can also upvote helpful answers to support the community.
            
            You can manage your email notification preferences in your account settings.
            
            - The SaladOverflow Team
            """

            return self._send_email(
                post_author.email, subject, html_content, text_content
            )

        except Exception as e:
            logger.error(
                f"Failed to send new answer notification to {post_author.email}: {e}"
            )
            return False

    def send_admin_post_log(
        self,
        user: User,
        post_title: str,
        post_id: int,
        post_type: str,
        post_content_plain: str,
    ) -> bool:
        """Send automated log email to admin when any post is created"""
        try:
            admin_email = "saladoverflow@saladsync.ca"
            logo_url = f"{self.backend_url}/static/img/logo.png"
            post_url = f"{self.base_url}/posts/{post_id}"

            # Truncate content preview to ~300 characters
            content_preview = (
                post_content_plain[:300] + "..."
                if len(post_content_plain) > 300
                else post_content_plain
            )

            subject = f"[SALADOVERFLOW LOG] New {post_type.title()} Posted by {user.display_name}"

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Post Creation Log</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #222725;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #222725;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #121113; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 30px; border-bottom: 2px solid #899878;">
                                        <img src="{logo_url}" alt="SaladOverflow" style="max-width: 120px; height: auto; margin-bottom: 20px;">
                                        <h1 style="margin: 0 0 8px; color: #F7F7F2; font-size: 24px; font-weight: 600; letter-spacing: -0.5px;">New Post Created</h1>
                                        <p style="margin: 0; color: #899878; font-size: 14px;">Automated Activity Log</p>
                                    </td>
                                </tr>
                                
                                <!-- Post Details -->
                                <tr>
                                    <td style="padding: 30px 40px 20px;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding-bottom: 12px;">
                                                    <p style="margin: 0; color: #899878; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Post Type</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 16px; font-weight: 500;">{post_type.title()}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding-bottom: 12px;">
                                                    <p style="margin: 0; color: #899878; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Author</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 16px; font-weight: 500;">{user.display_name} (@{user.username})</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 13px; opacity: 0.7;">Email: {user.email}</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 13px; opacity: 0.7;">User ID: {user.id}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <p style="margin: 0; color: #899878; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Posted</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 16px; font-weight: 500;">{datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                                                    <p style="margin: 4px 0 0; color: #F7F7F2; font-size: 13px; opacity: 0.7;">Post ID: {post_id}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Post Content -->
                                <tr>
                                    <td style="padding: 0 40px 20px;">
                                        <div style="padding: 24px; background-color: #222725; border-radius: 6px; border-left: 3px solid #899878;">
                                            <p style="margin: 0 0 8px; color: #899878; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Post Title</p>
                                            <h2 style="margin: 0 0 20px; color: #F7F7F2; font-size: 18px; line-height: 1.4; font-weight: 600;">
                                                {post_title}
                                            </h2>
                                            <p style="margin: 0 0 8px; color: #899878; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Content Preview</p>
                                            <p style="margin: 0; color: #F7F7F2; font-size: 14px; line-height: 1.6; opacity: 0.9;">
                                                {content_preview}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Post Link -->
                                <tr>
                                    <td style="padding: 0 40px 30px;">
                                        <p style="margin: 0 0 12px; color: #F7F7F2; font-size: 14px; line-height: 1.6; opacity: 0.9;">
                                            View full post:
                                        </p>
                                        <div style="padding: 14px; background-color: #222725; border-radius: 6px; border: 1px solid #899878;">
                                            <p style="margin: 0; color: #899878; font-size: 13px; word-break: break-all; font-family: 'Courier New', monospace;">
                                                {post_url}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- CTA Button -->
                                <tr>
                                    <td style="padding: 0 40px 40px; text-align: center;">
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin: 0 auto;">
                                            <tr>
                                                <td style="background-color: #899878; border-radius: 6px; padding: 16px 40px;">
                                                    <a href="{post_url}" style="color: #121113; text-decoration: none; font-size: 16px; font-weight: 600; display: inline-block;">
                                                        View Post
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #222725; border-top: 1px solid #899878;">
                                        <p style="margin: 0; color: #F7F7F2; font-size: 12px; opacity: 0.6; line-height: 1.4;">
                                            This is an automated log notification from SaladOverflow. This email is sent for all new posts created on the platform.
                                        </p>
                                    </td>
                                </tr>
                                
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            text_content = f"""
            [SALADOVERFLOW LOG] New {post_type.title()} Posted
            
            Post Type: {post_type.title()}
            
            Author: {user.display_name} (@{user.username})
            Email: {user.email}
            User ID: {user.id}
            
            Posted: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
            Post ID: {post_id}
            
            Title: {post_title}
            
            Content Preview:
            {content_preview}
            
            View full post: {post_url}
            
            ---
            This is an automated log notification from SaladOverflow.
            """

            return self._send_email(admin_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Failed to send admin post log: {e}")
            return False

    def is_email_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.smtp_server and self.smtp_port and self.from_email)

    def test_email_connection(self) -> bool:
        """Test email server connection"""
        try:
            with self._create_smtp_connection() as server:
                pass
            logger.info("Email connection test successful")
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False


# Global email service instance
email_service = EmailService()
