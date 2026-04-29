"""
followup_manager.py
===================
PURPOSE: Manage automatic follow-up emails to vendors
USED BY: app.py, pages/2_📊_Active_RFQs.py
DEPENDS ON: email_sender, email_generator, database

This module:
1. Checks which vendors need follow-up reminders
2. Generates polite reminder emails
3. Sends follow-ups via Gmail SMTP
4. Updates database with follow-up tracking
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Import email modules
try:
    from . import email_sender, email_generator
except ImportError:
    import email_sender, email_generator


def check_followups_needed(db_manager, rfq_id: int) -> List[Dict]:
    rfq = db_manager.get_rfq(rfq_id)
    if not rfq or rfq['followup_count'] <= 0 or rfq['status'] != 'active':
        return []
    deadline = datetime.fromisoformat(rfq['deadline_time'])
    now = datetime.now()
    if now > deadline:
        return []
    vendors = db_manager.get_vendors(rfq_id)
    pending_vendors = [v for v in vendors if v['response_status'] == 'pending']
    vendors_needing_followup = []
    for vendor in pending_vendors:
        if vendor['followup_sent_count'] >= rfq['followup_count']:
            continue
        last_contact = datetime.fromisoformat(
            vendor['last_followup_at'] if vendor['last_followup_at'] else vendor['sent_at']
        )
        hours_since = (now - last_contact).total_seconds() / 3600
        if hours_since >= rfq['followup_interval']:
            vendors_needing_followup.append(vendor)
    return vendors_needing_followup

def generate_followup_email(rfq: Dict, vendor: Dict, items: List[Dict], 
                           followup_number: int) -> tuple:
    """
    Generate a polite follow-up reminder email.
    
    Args:
        rfq: RFQ dictionary
        vendor: Vendor dictionary
        items: List of RFQ items
        followup_number: Which follow-up this is (1, 2, 3...)
        
    Returns:
        Tuple of (subject, html_body)
    """
    
    # Calculate time until deadline
    deadline = datetime.fromisoformat(rfq['deadline_time'])
    now = datetime.now()
    hours_remaining = (deadline - now).total_seconds() / 3600
    days_remaining = int(hours_remaining / 24)
    
    # Subject line
    if followup_number == 1:
        subject = f"Reminder: {rfq['subject']}"
    else:
        subject = f"Follow-up #{followup_number}: {rfq['subject']}"
    
    # Build items table HTML
    items_html = """
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f0f0f0;">
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Item</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Description</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Quantity</th>
                <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Unit</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for item in items:
        items_html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 10px;">{item['name']}</td>
                <td style="border: 1px solid #ddd; padding: 10px;">{item['description']}</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: center;">{item['quantity']}</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: center;">{item['unit']}</td>
            </tr>
        """
    
    items_html += """
        </tbody>
    </table>
    """
    
    # Generate urgency message based on time remaining
    if days_remaining <= 1:
        urgency_message = f"""
        <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong style="color: #c62828;">⏰ URGENT:</strong> 
            Only <strong>{int(hours_remaining)} hours</strong> remaining until deadline!
        </div>
        """
    elif days_remaining <= 3:
        urgency_message = f"""
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong style="color: #e65100;">⚠️ REMINDER:</strong> 
            Only <strong>{days_remaining} days</strong> remaining until deadline.
        </div>
        """
    else:
        urgency_message = f"""
        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <strong style="color: #1565c0;">📅 TIMELINE:</strong> 
            <strong>{days_remaining} days</strong> remaining until deadline.
        </div>
        """
    
    # Main email body
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #ffffff; padding: 30px; border: 1px solid #ddd; }}
        .footer {{ background-color: #f5f5f5; padding: 15px; text-align: center; border-radius: 0 0 5px 5px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📨 Quotation Request Reminder</h2>
        </div>
        <div class="content">
            <p>Dear <strong>{vendor['name']}</strong>,</p>
            
            <p>This is a friendly reminder regarding our Request for Quotation (RFQ) sent on 
            <strong>{datetime.fromisoformat(rfq['created_at']).strftime('%B %d, %Y')}</strong>.</p>
            
            <p>We have not yet received your quotation and wanted to follow up with you.</p>
            
            {urgency_message}
            
            <h3 style="color: #1976d2; margin-top: 25px;">📋 Items Requested:</h3>
            {items_html}
            
            <h3 style="color: #1976d2;">📝 Original Request:</h3>
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #1976d2; margin: 15px 0;">
                {rfq['body']}
            </div>
            
            <p style="margin-top: 25px;"><strong>Please reply to this email with your quotation.</strong></p>
            
            <p>If you have any questions or need clarification, feel free to contact us.</p>
            
            <p>Thank you for your attention to this matter!</p>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>Procurement Team</strong>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated reminder. Please reply with your quotation.</p>
            <p>{rfq.get('footer', '')}</p>
        </div>
    </div>
</body>
</html>
    """
    
    return subject, html_body


def send_followups(db_manager, rfq_id: int, sender_email: str, 
                  sender_password: str, dry_run: bool = False) -> Dict:
    """
    Check and send follow-up emails to pending vendors.
    
    Args:
        db_manager: DatabaseManager instance
        rfq_id: RFQ ID to check
        sender_email: Gmail address
        sender_password: Gmail App Password
        dry_run: If True, only check but don't actually send
        
    Returns:
        Dictionary with results:
        {
            "success": bool,
            "vendors_checked": int,
            "followups_needed": int,
            "followups_sent": int,
            "failed": List[str],
            "message": str
        }
    """
    
    results = {
        "success": False,
        "vendors_checked": 0,
        "followups_needed": 0,
        "followups_sent": 0,
        "failed": [],
        "message": ""
    }
    
    try:
        # Get vendors needing follow-ups
        vendors = check_followups_needed(db_manager, rfq_id)
        
        results["vendors_checked"] = len(db_manager.get_vendors(rfq_id))
        results["followups_needed"] = len(vendors)
        
        if not vendors:
            results["success"] = True
            results["message"] = "No follow-ups needed at this time"
            return results
        
        # Get RFQ details
        rfq = db_manager.get_rfq(rfq_id)
        items = db_manager.get_items(rfq_id)
        
        print(f"\n[INFO] Sending follow-ups for RFQ #{rfq_id}...")
        print(f"[INFO] {len(vendors)} vendor(s) need follow-ups")
        
        # Send follow-ups to each vendor
        for vendor in vendors:
            try:
                followup_number = vendor['followup_sent_count'] + 1
                
                print(f"\n[INFO] Preparing follow-up #{followup_number} for {vendor['name']}...")
                
                # Generate email
                subject, html_body = generate_followup_email(
                    rfq, vendor, items, followup_number
                )
                
                if dry_run:
                    print(f"[DRY RUN] Would send to {vendor['email']}")
                    print(f"[DRY RUN] Subject: {subject}")
                    results["followups_sent"] += 1
                else:
                    # Send email
                    success = email_sender.send_email(
                        sender_email=sender_email,
                        sender_password=sender_password,
                        recipient_email=vendor['email'],
                        subject=subject,
                        html_body=html_body
                    )
                    
                    if success:
                        # Update database
                        db_manager.update_vendor_followup(vendor['id'])
                        results["followups_sent"] += 1
                        print(f"[✓] Follow-up sent to {vendor['name']}")
                    else:
                        results["failed"].append(vendor['email'])
                        print(f"[✗] Failed to send to {vendor['name']}")
                
            except Exception as e:
                print(f"[✗] Error sending to {vendor['name']}: {e}")
                results["failed"].append(vendor['email'])
        
        # Summary
        results["success"] = True
        results["message"] = f"Sent {results['followups_sent']} follow-up(s)"
        
        if results["failed"]:
            results["message"] += f" ({len(results['failed'])} failed)"
        
        print(f"\n[SUMMARY] {results['message']}")
        return results
        
    except Exception as e:
        print(f"[✗] Error in send_followups: {e}")
        import traceback
        traceback.print_exc()
        results["message"] = f"Error: {str(e)}"
        return results


def check_all_active_rfqs(db_manager, sender_email: str, 
                         sender_password: str) -> Dict:
    """
    Check ALL active RFQs and send follow-ups where needed.
    
    This function can be called periodically (e.g., every hour)
    to automatically check and send follow-ups.
    
    Args:
        db_manager: DatabaseManager instance
        sender_email: Gmail address
        sender_password: Gmail App Password
        
    Returns:
        Summary dictionary
    """
    
    results = {
        "rfqs_checked": 0,
        "total_followups_sent": 0,
        "rfq_results": []
    }
    
    # Get all active RFQs
    active_rfqs = db_manager.get_active_rfqs()
    results["rfqs_checked"] = len(active_rfqs)
    
    print(f"\n[INFO] Checking {len(active_rfqs)} active RFQ(s) for follow-ups...")
    
    for rfq in active_rfqs:
        rfq_result = send_followups(
            db_manager=db_manager,
            rfq_id=rfq['id'],
            sender_email=sender_email,
            sender_password=sender_password
        )
        
        results["total_followups_sent"] += rfq_result["followups_sent"]
        results["rfq_results"].append({
            "rfq_id": rfq['id'],
            "subject": rfq['subject'],
            "result": rfq_result
        })
    
    print(f"\n[SUMMARY] Total follow-ups sent: {results['total_followups_sent']}")
    return results


if __name__ == "__main__":
    print("[✓] Follow-up Manager Module Loaded!")
