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


def get_credential(key):
    """
    Get credential from environment variables (GitHub Actions secrets).
    GitHub Actions injects secrets as environment variables.
    """
    value = os.getenv(key)
    if not value:
        print(f"❌ WARNING: {key} not found in environment variables")
    return value


def check_emails():
    """Check for new vendor responses"""
    print(f"\n{'='*70}")
    print(f"🔍 EMAIL CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        db = DatabaseManager()
        
        # Get email credentials from environment (GitHub Actions secrets)
        sender_email = get_credential('EMAIL_ADDRESS')
        sender_password = get_credential('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("❌ ERROR: Email credentials not found in environment")
            print("💡 Make sure EMAIL_ADDRESS and EMAIL_PASSWORD are set in GitHub Actions secrets")
            return
        
        # Get all active RFQs
        active_rfqs = db.get_active_rfqs()
        
        if not active_rfqs:
            print("ℹ️ No active RFQs found")
            return
        
        print(f"📊 Found {len(active_rfqs)} active RFQ(s)")
        
        total_new_responses = 0
        
        for rfq in active_rfqs:
            print(f"\n  📤 RFQ #{rfq['id']}: {rfq['subject']}")
            
            # Get vendors for this RFQ
            vendors = db.get_vendors(rfq['id'])
            pending = [v for v in vendors if v['response_status'] == 'pending']
            
            if not pending:
                print(f"    ✅ All vendors responded")
                continue
            
            print(f"    ⏳ Checking {len(pending)} pending vendor(s)...")
            
            # Check for new responses
            for vendor in pending:
                result = check_new_responses(
                    db_manager=db,
                    rfq_id=rfq['id'],
                    vendor_email=vendor['email'],
                    email_address=sender_email,
                    email_password=sender_password
                )
                
                if result['new_responses'] > 0:
                    total_new_responses += result['new_responses']
                    print(f"    📧 New response from {vendor['name']}!")
        
        if total_new_responses > 0:
            print(f"\n✅ Email check complete: {total_new_responses} new response(s) found")
        else:
            print(f"\nℹ️ Email check complete: No new responses")
            
    except Exception as e:
        print(f"❌ Email check failed: {e}")
        import traceback
        traceback.print_exc()


def send_followups():
    """Send follow-up reminders to pending vendors"""
    print(f"\n{'='*70}")
    print(f"🔄 FOLLOW-UP CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    try:
        db = DatabaseManager()
        
        # Get email credentials from environment (GitHub Actions secrets)
        sender_email = get_credential('EMAIL_ADDRESS')
        sender_password = get_credential('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("❌ ERROR: Email credentials not found in environment")
            print("💡 Make sure EMAIL_ADDRESS and EMAIL_PASSWORD are set in GitHub Actions secrets")
            return
        
        # Check all active RFQs for follow-ups
        results = check_all_active_rfqs(
            db_manager=db,
            sender_email=sender_email,
            sender_password=sender_password
        )
        
        if results['total_followups_sent'] > 0:
            print(f"\n✅ Follow-up check complete:")
            print(f"    📧 {results['total_followups_sent']} follow-up(s) sent")
            print(f"    📋 {results['rfqs_processed']} RFQ(s) processed")
            
            # Show details
            for rfq_result in results['rfq_results']:
                if rfq_result['result']['followups_sent'] > 0:
                    print(f"\n    RFQ #{rfq_result['rfq_id']}:")
                    print(f"      • Sent to: {', '.join(rfq_result['result']['vendors_sent'])}")
        else:
            print(f"\nℹ️ Follow-up check complete: No follow-ups needed at this time")
            
    except Exception as e:
        print(f"❌ Follow-up check failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main automation worker"""
    print("\n" + "="*70)
    print("🤖 RFQ AUTOMATION WORKER STARTED")
    print("="*70)
    
    # Verify environment
    print("\n🔧 Checking environment...")
    print(f"  • EMAIL_ADDRESS: {'✅ Found' if os.getenv('EMAIL_ADDRESS') else '❌ Missing'}")
    print(f"  • EMAIL_PASSWORD: {'✅ Found' if os.getenv('EMAIL_PASSWORD') else '❌ Missing'}")
    print(f"  • SUPABASE_URL: {'✅ Found' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
    print(f"  • SUPABASE_KEY: {'✅ Found' if os.getenv('SUPABASE_KEY') else '❌ Missing'}")
    print(f"  • GEMINI_API_KEY: {'✅ Found' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
    
    missing = []
    if not os.getenv('EMAIL_ADDRESS'): missing.append('EMAIL_ADDRESS')
    if not os.getenv('EMAIL_PASSWORD'): missing.append('EMAIL_PASSWORD')
    if not os.getenv('SUPABASE_URL'): missing.append('SUPABASE_URL')
    if not os.getenv('SUPABASE_KEY'): missing.append('SUPABASE_KEY')
    if not os.getenv('GEMINI_API_KEY'): missing.append('GEMINI_API_KEY')
    
    if missing:
        print(f"\n❌ ERROR: Missing required environment variables: {', '.join(missing)}")
        print("💡 Make sure all secrets are configured in GitHub Actions settings")
        sys.exit(1)
    
    # Run both tasks
    check_emails()
    send_followups()
    
    print("\n" + "="*70)
    print("✅ AUTOMATION WORKER COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
