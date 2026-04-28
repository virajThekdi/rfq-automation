#!/usr/bin/env python3
"""
RFQ Automation Worker - 24/7 Background Service

This script runs automatically via GitHub Actions (or other schedulers)
to check emails and send follow-ups without manual intervention.

Usage:
    python automation_worker.py              # Run both tasks
    python automation_worker.py check-emails # Check emails only
    python automation_worker.py send-followups # Send follow-ups only
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
from modules import ai_parser


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
        gemini_api_key = get_credential('GEMINI_API_KEY')
        
        if not sender_email or not sender_password:
            print("❌ ERROR: Email credentials not found in environment")
            print("💡 Make sure EMAIL_ADDRESS and EMAIL_PASSWORD are set in GitHub Actions secrets")
            return False
        
        if not gemini_api_key:
            print("⚠️ WARNING: GEMINI_API_KEY not found - AI parsing will be limited")
        
        # Get all active RFQs
        active_rfqs = db.get_active_rfqs()
        
        if not active_rfqs:
            print("ℹ️ No active RFQs found")
            return True
        
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
            
            # Check for new responses for this RFQ
            # NOTE: check_new_responses() checks ALL pending vendors for the RFQ automatically
            result = check_new_responses(
                email_address=sender_email,
                password=sender_password,
                rfq_id=rfq['id'],
                db_manager=db,
                ai_parser=ai_parser,
                gemini_api_key=gemini_api_key or ""
            )
            
            if result['new_responses'] > 0:
                total_new_responses += result['new_responses']
                print(f"    📧 {result['new_responses']} new response(s) found!")
                if result.get('processed'):
                    for vendor_email in result['processed']:
                        print(f"      • {vendor_email}")
        
        if total_new_responses > 0:
            print(f"\n✅ Email check complete: {total_new_responses} new response(s) found")
        else:
            print(f"\nℹ️ Email check complete: No new responses")
        
        return True
            
    except Exception as e:
        print(f"❌ Email check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


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
            return False
        
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
        
        return True
            
    except Exception as e:
        print(f"❌ Follow-up check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_environment():
    """Verify all required environment variables are present"""
    print("\n🔧 Checking environment...")
    print(f"  • EMAIL_PROVIDER: {os.getenv('EMAIL_PROVIDER', 'gmail')} (default: gmail)")
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
        return False
    
    return True


def main():
    """Main automation worker"""
    print("\n" + "="*70)
    print("🤖 RFQ AUTOMATION WORKER STARTED")
    print("="*70)
    
    # Verify environment first
    if not verify_environment():
        sys.exit(1)
    
    # Parse command-line arguments
    task = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    success = True
    
    if task == 'check-emails':
        # Run email check only
        success = check_emails()
        
    elif task == 'send-followups':
        # Run follow-up check only
        success = send_followups()
        
    elif task == 'all':
        # Run both tasks
        email_success = check_emails()
        followup_success = send_followups()
        success = email_success and followup_success
        
    else:
        print(f"\n❌ ERROR: Unknown task '{task}'")
        print("💡 Valid tasks: check-emails, send-followups, all (or no argument)")
        sys.exit(1)
    
    print("\n" + "="*70)
    if success:
        print("✅ AUTOMATION WORKER COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")
        sys.exit(0)
    else:
        print("⚠️ AUTOMATION WORKER COMPLETED WITH ERRORS")
        print("="*70 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
