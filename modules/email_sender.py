"""
email_sender.py
===============
PURPOSE: Send emails via Gmail SMTP
USED BY: app.py, followup_manager.py
DEPENDS ON: smtplib, email (Python standard library)

This module handles sending emails through Gmail's SMTP server.
It uses an App Password for authentication (not regular password).
"""

import smtplib  # For sending emails
from email.mime.text import MIMEText  # For email content
from email.mime.multipart import MIMEMultipart  # For email structure
from typing import List  # For type hints
import time  # For delays


def send_email(sender_email: str, sender_password: str, recipient_email: str,
               subject: str, html_body: str) -> bool:
    """
    Send an HTML email via Gmail SMTP.
    
    Args:
        sender_email: Your Gmail address
        sender_password: Your Gmail App Password (NOT regular password)
        recipient_email: Recipient's email address
        subject: Email subject line
        html_body: HTML content of the email
        
    Returns:
        True if sent successfully, False otherwise
    """
    
    try:
        # Step 1: Create email message object
        message = MIMEMultipart("alternative")  # "alternative" allows HTML + plain text
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Step 2: Attach HTML content
        # The email will display as HTML in email clients
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Step 3: Connect to Gmail SMTP server
        # Gmail SMTP settings:
        # - Server: smtp.gmail.com
        # - Port: 587 (TLS encryption)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        # Start TLS encryption (required by Gmail)
        server.starttls()
        
        # Step 4: Login with credentials
        server.login(sender_email, sender_password)
        
        # Step 5: Send the email
        server.send_message(message)
        
        # Step 6: Close connection
        server.quit()
        
        print(f"[✓] Email sent to {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"[✗] Authentication failed. Check your email and App Password.")
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
    
    Args:
        sender_email: Your Gmail address
        sender_password: Your Gmail App Password
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
    
    print(f"\n[INFO] Sending emails to {len(recipients)} recipients...\n")
    
    for idx, recipient in enumerate(recipients, 1):
        print(f"[{idx}/{len(recipients)}] Sending to {recipient}... ", end="")
        
        success = send_email(sender_email, sender_password, recipient, 
                           subject, html_body)
        
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


def test_email_connection(sender_email: str, sender_password: str) -> bool:
    """
    Test if email credentials are valid.
    
    Attempts to login to Gmail SMTP without sending an email.
    
    Args:
        sender_email: Gmail address
        sender_password: App Password
        
    Returns:
        True if connection successful, False otherwise
    """
    
    try:
        print("[INFO] Testing email connection...")
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        
        print("[✓] Email connection successful")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("[✗] Authentication failed. Check your credentials.")
        return False
        
    except Exception as e:
        print(f"[✗] Connection error: {str(e)}")
        return False
