"""
email_sender.py
===============
PURPOSE: Send emails via SMTP (multi-provider support)
USED BY: app.py, followup_manager.py
DEPENDS ON: smtplib, email (Python standard library)

This module handles sending emails through various SMTP servers.
Supports Gmail, Outlook, Yahoo, and custom SMTP servers.
Uses App Passwords for authentication (not regular passwords).
"""

import smtplib  # For sending emails
from email.mime.text import MIMEText  # For email content
from email.mime.multipart import MIMEMultipart  # For email structure
from typing import List, Dict, Tuple  # For type hints
import time  # For delays
import os  # For environment variables


# SMTP provider configurations
# Format: {provider_name: (smtp_server, smtp_port)}
SMTP_PROVIDERS = {
    'gmail': ('smtp.gmail.com', 587),
    'outlook': ('smtp-mail.outlook.com', 587),
    'office365': ('smtp.office365.com', 587),
    'hotmail': ('smtp-mail.outlook.com', 587),
    'yahoo': ('smtp.mail.yahoo.com', 587),
    'custom': (None, 587)  # Will be overridden by env vars
}


def get_smtp_settings() -> Tuple[str, int]:
    """
    Get SMTP server settings based on environment configuration.
    
    Reads EMAIL_PROVIDER from environment variables and returns
    the appropriate SMTP server and port.
    
    Environment Variables:
        EMAIL_PROVIDER: Provider name (gmail/outlook/hotmail/yahoo/custom)
        SMTP_SERVER: Custom SMTP server (if EMAIL_PROVIDER=custom)
        SMTP_PORT: Custom SMTP port (optional, defaults to 587)
    
    Returns:
        Tuple of (smtp_server, smtp_port)
    
    Raises:
        ValueError: If provider is invalid or custom settings missing
    """
    
    # Get provider from environment (default to gmail for backward compatibility)
    provider = os.getenv('EMAIL_PROVIDER', 'gmail').lower()
    
    # Check if provider is supported
    if provider not in SMTP_PROVIDERS:
        raise ValueError(
            f"Unsupported EMAIL_PROVIDER: {provider}. "
            f"Supported: {', '.join(SMTP_PROVIDERS.keys())}"
        )
    
    # Handle custom provider
    if provider == 'custom':
        smtp_server = os.getenv('SMTP_SERVER')
        if not smtp_server:
            raise ValueError(
                "SMTP_SERVER environment variable is required when EMAIL_PROVIDER=custom"
            )
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        print(f"[INFO] Using custom SMTP: {smtp_server}:{smtp_port}")
        return smtp_server, smtp_port
    
    # Get predefined provider settings
    smtp_server, smtp_port = SMTP_PROVIDERS[provider]
    print(f"[INFO] Using {provider.upper()} SMTP: {smtp_server}:{smtp_port}")
    return smtp_server, smtp_port


def send_email(sender_email: str, sender_password: str, recipient_email: str,
               subject: str, html_body: str, smtp_server: str = None, 
               smtp_port: int = None) -> bool:
    """
    Send an HTML email via SMTP.
    
    Automatically detects SMTP settings from environment variables if not provided.
    Supports Gmail, Outlook, Yahoo, and custom SMTP servers.
    
    Args:
        sender_email: Your email address
        sender_password: Your App Password (NOT regular password)
        recipient_email: Recipient's email address
        subject: Email subject line
        html_body: HTML content of the email
        smtp_server: Optional SMTP server (overrides env config)
        smtp_port: Optional SMTP port (overrides env config)
        
    Returns:
        True if sent successfully, False otherwise
        
    Notes:
        - Gmail: Requires App Password (16-char code from Google Account settings)
        - Outlook/Hotmail: Requires App Password or OAuth2
        - Yahoo: Requires App Password from Yahoo Account Security settings
        - Custom: Configure SMTP_SERVER and SMTP_PORT in environment
    """
    
    try:
        # Step 1: Get SMTP settings
        if smtp_server is None or smtp_port is None:
            smtp_server, smtp_port = get_smtp_settings()
        
        # Step 2: Create email message object
        message = MIMEMultipart("alternative")  # "alternative" allows HTML + plain text
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Step 3: Attach HTML content
        # The email will display as HTML in email clients
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Step 4: Connect to SMTP server
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        # Start TLS encryption (required by most providers)
        server.starttls()
        
        # Step 5: Login with credentials
        server.login(sender_email, sender_password)
        
        # Step 6: Send the email
        server.send_message(message)
        
        # Step 7: Close connection
        server.quit()
        
        print(f"[✓] Email sent to {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"[✗] Authentication failed. Check your email and App Password.")
        print(f"    Tip: Most providers require App Passwords, not regular passwords.")
        return False
        
    except smtplib.SMTPException as e:
        print(f"[✗] SMTP error sending to {recipient_email}: {str(e)}")
        return False
        
    except Exception as e:
        print(f"[✗] Error sending to {recipient_email}: {str(e)}")
        return False


def send_bulk_emails(sender_email: str, sender_password: str, 
                    recipients: List[str], subject: str, html_body: str,
                    delay: float = 1.0) -> dict:
    """
    Send the same email to multiple recipients.
    
    Includes a small delay between sends to avoid being flagged as spam.
    Uses SMTP settings from environment variables.
    
    Args:
        sender_email: Your email address
        sender_password: Your App Password
        recipients: List of recipient email addresses
        subject: Email subject
        html_body: HTML email content
        delay: Seconds to wait between sends (default 1.0)
        
    Returns:
        Dictionary with 'success' and 'failed' lists
    """
    
    results = {
        "success": [],
        "failed": []
    }
    
    print(f"\n[INFO] Sending emails to {len(recipients)} recipients...")
    
    # Get SMTP settings once (reused for all sends)
    try:
        smtp_server, smtp_port = get_smtp_settings()
    except ValueError as e:
        print(f"[✗] Configuration error: {str(e)}")
        results["failed"] = recipients
        return results
    
    print()
    
    for idx, recipient in enumerate(recipients, 1):
        print(f"[{idx}/{len(recipients)}] Sending to {recipient}... ", end="")
        
        success = send_email(sender_email, sender_password, recipient, 
                           subject, html_body, smtp_server, smtp_port)
        
        if success:
            results["success"].append(recipient)
        else:
            results["failed"].append(recipient)
        
        # Small delay to avoid spam filters
        if idx < len(recipients):  # Don't delay after last email
            time.sleep(delay)
    
    # Print summary
    print(f"\n[SUMMARY] Sent: {len(results['success'])}, Failed: {len(results['failed'])}")
    
    if results["failed"]:
        print(f"[WARNING] Failed recipients: {', '.join(results['failed'])}")
    
    return results


def test_email_connection(sender_email: str, sender_password: str, 
                         smtp_server: str = None, smtp_port: int = None) -> bool:
    """
    Test if email credentials are valid.
    
    Attempts to login to SMTP server without sending an email.
    Uses environment-configured settings if not provided.
    
    Args:
        sender_email: Email address
        sender_password: App Password
        smtp_server: Optional SMTP server (overrides env config)
        smtp_port: Optional SMTP port (overrides env config)
        
    Returns:
        True if connection successful, False otherwise
    """
    
    try:
        print("[INFO] Testing email connection...")
        
        # Get SMTP settings
        if smtp_server is None or smtp_port is None:
            smtp_server, smtp_port = get_smtp_settings()
        
        # Test connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        
        print("[✓] Email connection successful")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("[✗] Authentication failed. Check your credentials.")
        print("    Tip: Most providers require App Passwords:")
        print("    - Gmail: https://myaccount.google.com/apppasswords")
        print("    - Outlook: https://account.live.com/proofs/AppPassword")
        print("    - Yahoo: https://login.yahoo.com/account/security")
        return False
        
    except Exception as e:
        print(f"[✗] Connection error: {str(e)}")
        return False


def get_provider_instructions(provider: str = None) -> str:
    """
    Get setup instructions for a specific email provider.
    
    Args:
        provider: Provider name (gmail/outlook/yahoo/custom)
                 If None, uses EMAIL_PROVIDER from environment
    
    Returns:
        String with setup instructions
    """
    
    if provider is None:
        provider = os.getenv('EMAIL_PROVIDER', 'gmail').lower()
    
    instructions = {
        'gmail': """
        Gmail SMTP Setup:
        1. Enable 2-Factor Authentication on your Google Account
        2. Go to: https://myaccount.google.com/apppasswords
        3. Select 'Mail' and 'Other (Custom name)'
        4. Copy the 16-character App Password
        5. Use this App Password (not your regular password)
        
        Environment Variables:
        EMAIL_PROVIDER=gmail
        EMAIL_ADDRESS=your@gmail.com
        EMAIL_PASSWORD=your-16-char-app-password
        """,
        
        'outlook': """
        Outlook/Office 365 SMTP Setup:
        1. Enable 2-Factor Authentication (recommended)
        2. Go to: https://account.live.com/proofs/AppPassword
        3. Generate an App Password
        4. Use this App Password in your configuration
        
        Environment Variables:
        EMAIL_PROVIDER=outlook
        EMAIL_ADDRESS=your@outlook.com
        EMAIL_PASSWORD=your-app-password
        """,
        
        'hotmail': """
        Hotmail SMTP Setup (same as Outlook):
        1. Enable 2-Factor Authentication (recommended)
        2. Go to: https://account.live.com/proofs/AppPassword
        3. Generate an App Password
        4. Use this App Password in your configuration
        
        Environment Variables:
        EMAIL_PROVIDER=hotmail
        EMAIL_ADDRESS=your@hotmail.com
        EMAIL_PASSWORD=your-app-password
        """,
        
        'yahoo': """
        Yahoo SMTP Setup:
        1. Enable 2-Factor Authentication
        2. Go to: https://login.yahoo.com/account/security
        3. Click 'Generate app password'
        4. Select 'Other App' and give it a name
        5. Copy the App Password
        
        Environment Variables:
        EMAIL_PROVIDER=yahoo
        EMAIL_ADDRESS=your@yahoo.com
        EMAIL_PASSWORD=your-app-password
        """,
        
        'custom': """
        Custom SMTP Setup:
        Configure your own SMTP server settings.
        
        Environment Variables:
        EMAIL_PROVIDER=custom
        SMTP_SERVER=smtp.your-domain.com
        SMTP_PORT=587
        EMAIL_ADDRESS=your@email.com
        EMAIL_PASSWORD=your-password
        """
    }
    
    return instructions.get(provider, "Unknown provider")
