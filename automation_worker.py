#!/usr/bin/env python3
"""
RFQ Automation Worker - 24/7 Background Service

This script runs automatically via GitHub Actions (or other schedulers)
to check emails and send follow-ups without manual intervention.
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from database.db_manager import DatabaseManager
from modules.email_monitor import check_new_responses
from modules.followup_manager import check_all_active_rfqs


def check_emails():
    """Check for new vendor responses"""
    print(f"\n{'='*70}")
    print(f"🔍 EMAIL CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        db = DatabaseManager()
        
        # Get email credentials
        sender_email = os.getenv('EMAIL_ADDRESS')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("❌ ERROR: Email credentials not found in environment")
            return
        
        # Get all active RFQs
        active_rfqs = db.get_active_rfqs()
        
        if not active_rfqs:
            print("ℹ️ No active RFQs found")
            return
        
        print(f"📊 Found {len(active_rfqs)} active RFQ(s)")
        
        total_new_responses = 0
        
        # Check emails for each active RFQ
        for rfq in active_rfqs:
            rfq_id = rfq['id']
            rfq_subject = rfq['subject']
            
            print(f"\n🔎 Checking RFQ #{rfq_id}: {rfq_subject}")
            
            # Check for new responses
            result = check_new_responses(
                db_manager=db,
                rfq_id=rfq_id,
                sender_email=sender_email,
                sender_password=sender_password
            )
            
            if result and result['success_count'] > 0:
                print(f"   ✅ Found {result['success_count']} new response(s)")
                total_new_responses += result['success_count']
            else:
                print(f"   ℹ️ No new responses")
        
        print(f"\n{'='*70}")
        print(f"✅ Email check complete: {total_new_responses} new response(s) found")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ ERROR during email check: {e}")
        import traceback
        traceback.print_exc()


def send_followups():
    """Send follow-up reminders to pending vendors"""
    print(f"\n{'='*70}")
    print(f"📧 FOLLOW-UP CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        db = DatabaseManager()
        
        # Get email credentials
        sender_email = os.getenv('EMAIL_ADDRESS')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("❌ ERROR: Email credentials not found in environment")
            return
        
        # Check all active RFQs for follow-ups
        result = check_all_active_rfqs(db, sender_email, sender_password)
        
        if result['total_sent'] > 0:
            print(f"\n✅ Sent {result['total_sent']} follow-up email(s)")
            print(f"   • RFQs processed: {result['rfqs_processed']}")
        else:
            print("ℹ️ No follow-ups needed at this time")
            if result['rfqs_processed'] > 0:
                print(f"   • Checked {result['rfqs_processed']} RFQ(s)")
        
        print(f"\n{'='*70}")
        print(f"✅ Follow-up check complete")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ ERROR during follow-up check: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main automation worker"""
    if len(sys.argv) < 2:
        print("Usage: python automation_worker.py [check-emails|send-followups|both]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    print(f"\n🤖 RFQ AUTOMATION WORKER STARTED")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Command: {command}\n")
    
    if command == "check-emails":
        check_emails()
    elif command == "send-followups":
        send_followups()
    elif command == "both":
        check_emails()
        send_followups()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: check-emails, send-followups, both")
        sys.exit(1)
    
    print(f"🏁 Worker finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
