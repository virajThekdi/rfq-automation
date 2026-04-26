"""Page 1: Create New RFQ with Follow-up Support"""
import streamlit as st
import sys
sys.path.insert(0, '..')
from database.db_manager import DatabaseManager
from modules import excel_reader, email_sender, email_generator
from datetime import datetime, timedelta
import pandas as pd
import os
import tempfile
from dotenv import load_dotenv

st.set_page_config(page_title="Create RFQ", page_icon="📤", layout="wide")
st.title("📤 Create New RFQ")

db = DatabaseManager()
load_dotenv()

# Helper function to get credentials from either .env or st.secrets
def get_credential(key):
    """Get credential from .env (local) or st.secrets (Streamlit Cloud)"""
    # Try environment variable first (local development)
    value = os.getenv(key)
    if value:
        return value
    # Fall back to Streamlit secrets (Streamlit Cloud)
    try:
        return st.secrets.get(key)
    except:
        return None

# Upload method
upload_method = st.radio("Choose input method:", ["Upload Excel File", "Manual Entry"])

if upload_method == "Upload Excel File":
    st.subheader("📄 Upload Excel File")
    st.info("Excel must have 2 sheets: 'Vendors' and 'RFQ'")
    
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
    
    if uploaded_file:
        try:
            # Use Python's tempfile to create a proper temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                temp_path = tmp_file.name
            
            # Read vendors and items (already returns lists of dicts)
            vendors_list, items_list = excel_reader.read_excel_file(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Store in session
            st.session_state['vendors'] = vendors_list
            st.session_state['items'] = items_list
            
            st.success(f"✅ Loaded {len(vendors_list)} vendors and {len(items_list)} items")
            
        except Exception as e:
            st.error(f"Error reading Excel: {e}")

else:
    st.subheader("✍️ Manual Entry")
    
    # Vendors input
    st.write("**Step 1: Add Vendors**")
    col1, col2 = st.columns(2)
    with col1:
        vendor_name = st.text_input("Vendor Name")
    with col2:
        vendor_email = st.text_input("Vendor Email")
    
    if st.button("➕ Add Vendor"):
        if vendor_name and vendor_email:
            if 'vendors' not in st.session_state:
                st.session_state['vendors'] = []
            st.session_state['vendors'].append({
                'name': vendor_name,
                'email': vendor_email
            })
            st.success(f"✅ Added {vendor_name}")
            st.rerun()
        else:
            st.error("Please fill both fields")
    
    # Display vendors
    if 'vendors' in st.session_state and st.session_state['vendors']:
        st.write(f"**Current Vendors ({len(st.session_state['vendors'])}):**")
        for idx, v in enumerate(st.session_state['vendors']):
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(v['name'])
            col2.write(v['email'])
            if col3.button("🗑️", key=f"del_vendor_{idx}"):
                st.session_state['vendors'].pop(idx)
                st.rerun()
    
    st.markdown("---")
    
    # Items input
    st.write("**Step 2: Add Items**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        item_name = st.text_input("Item Name")
    with col2:
        item_desc = st.text_input("Description")
    with col3:
        item_qty = st.number_input("Quantity", min_value=1, value=1)
    with col4:
        item_unit = st.text_input("Unit", value="pcs")
    
    if st.button("➕ Add Item"):
        if item_name:
            if 'items' not in st.session_state:
                st.session_state['items'] = []
            st.session_state['items'].append({
                'item_name': item_name,  # Use 'item_name' key for consistency
                'description': item_desc,
                'quantity': item_qty,
                'unit': item_unit
            })
            st.success(f"✅ Added {item_name}")
            st.rerun()
        else:
            st.error("Please fill item name")
    
    # Display items
    if 'items' in st.session_state and st.session_state['items']:
        st.write(f"**Current Items ({len(st.session_state['items'])}):**")
        items_df = pd.DataFrame(st.session_state['items'])
        
        # Add delete button for each row
        for idx, item in enumerate(st.session_state['items']):
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            col1.write(item.get('item_name', item.get('name', '')))
            col2.write(item['description'])
            col3.write(str(item['quantity']))
            col4.write(item['unit'])
            if col5.button("🗑️", key=f"del_item_{idx}"):
                st.session_state['items'].pop(idx)
                st.rerun()

st.markdown("---")

# RFQ Details
st.subheader("📋 RFQ Details")

col1, col2 = st.columns(2)
with col1:
    subject = st.text_input("Subject/Title", value="Request for Quotation")
with col2:
    deadline_days = st.number_input("Response Deadline (days)", min_value=1, max_value=30, value=7)

body = st.text_area("RFQ Message Body", 
                    value="Dear Vendor,\n\nWe are requesting quotations for the following items. Please provide your best price and delivery timeline.",
                    height=150)

footer = st.text_area("Email Footer/Additional Info",
                     value="Please submit your quotation by the deadline. For questions, contact us at this email.",
                     height=100)

# Follow-up settings
st.markdown("---")
st.subheader("🔄 Follow-up Settings (Optional)")
st.caption("Automatically send reminder emails to vendors who haven't responded")

col1, col2 = st.columns(2)
with col1:
    followup_count = st.number_input("Number of follow-ups", min_value=0, max_value=5, value=2,
                                    help="How many reminder emails to send (0 = no follow-ups)")
with col2:
    followup_interval = st.number_input("Hours between follow-ups", min_value=1, max_value=168, value=24,
                                       help="Time to wait before sending next reminder")

if followup_count > 0:
    st.info(f"📧 Will send up to {followup_count} reminders, {followup_interval} hours apart")
    st.caption("Example: If deadline is 7 days and interval is 24h, reminders will be sent on days 1, 2, 3... until vendor responds")

# Calculate deadline
deadline_minutes = deadline_days * 24 * 60

st.markdown("---")

# Submit button
col1, col2 = st.columns(2)
with col1:
    can_create = ('vendors' in st.session_state and st.session_state['vendors'] and 
                  'items' in st.session_state and st.session_state['items'])
    if can_create:
        st.success(f"✅ Ready to create: {len(st.session_state['vendors'])} vendors, {len(st.session_state['items'])} items")
    else:
        st.warning("⚠️ Please add vendors and items first")

with col2:
    send_now = st.checkbox("Send emails immediately", value=True)

if st.button("🚀 Create & Send RFQ", type="primary", use_container_width=True):
    if 'vendors' not in st.session_state or not st.session_state['vendors']:
        st.error("❌ Please add vendors first!")
    elif 'items' not in st.session_state or not st.session_state['items']:
        st.error("❌ Please add items first!")
    else:
        rfq_id = None  # Track RFQ ID for rollback
        
        try:
            # STEP 1: Validate and TEST email credentials if sending now
            if send_now:
                sender_email = get_credential('EMAIL_ADDRESS')
                sender_password = get_credential('EMAIL_PASSWORD')
                
                if not sender_email or not sender_password:
                    st.error("❌ Email credentials not found!")
                    st.warning("⚠️ For local: Add credentials to .env file")
                    st.warning("⚠️ For Streamlit Cloud: Add credentials in app settings → Secrets")
                    st.info("💡 Current environment: " + ("Local" if os.getenv('EMAIL_ADDRESS') else "Streamlit Cloud"))
                    st.stop()
                
                # NEW: Test email connection BEFORE creating RFQ
                with st.spinner("🔍 Testing email connection..."):
                    connection_test = email_sender.test_email_connection(sender_email, sender_password)
                    
                    if not connection_test:
                        st.error("❌ Email connection test FAILED!")
                        st.error("🚫 RFQ will NOT be created until email credentials are valid")
                        st.warning("⚠️ Possible issues:")
                        st.warning("  • Wrong email address")
                        st.warning("  • Wrong app password")
                        st.warning("  • 2-Step verification not enabled")
                        st.warning("  • App password not generated from Google Account settings")
                        st.info("💡 Go to Settings page to update credentials")
                        st.stop()  # STOP HERE - Don't create RFQ
                    
                    st.success("✅ Email connection verified!")
            
            # STEP 2: Create RFQ in database (only if email test passed)
            with st.spinner("Creating RFQ..."):
                rfq_id = db.create_rfq(
                    subject=subject,
                    body=body,
                    footer=footer,
                    deadline_minutes=deadline_minutes,
                    followup_count=followup_count,
                    followup_interval=followup_interval
                )
                
                # Add vendors and items
                db.add_vendors(rfq_id, st.session_state['vendors'])
                db.add_items(rfq_id, st.session_state['items'])
                
                st.success(f"✅ RFQ #{rfq_id} created successfully!")
            
            # STEP 3: Send emails if requested
            if send_now:
                with st.spinner("📧 Sending emails to vendors..."):
                    success_count = 0
                    failed_count = 0
                    failed_vendors = []
                    
                    for vendor in st.session_state['vendors']:
                        try:
                            # Generate email HTML
                            html_email = email_generator.generate_rfq_email(
                                vendor_name=vendor['name'],
                                subject=subject,
                                body=body,
                                items=st.session_state['items'],
                                footer=footer
                            )
                            
                            # Send email
                            success = email_sender.send_email(
                                sender_email=sender_email,
                                sender_password=sender_password,
                                recipient_email=vendor['email'],
                                subject=subject,
                                html_body=html_email
                            )
                            
                            if success:
                                success_count += 1
                            else:
                                failed_count += 1
                                failed_vendors.append(vendor['name'])
                        except Exception as e:
                            st.warning(f"⚠️ Failed to send to {vendor['name']}: {e}")
                            failed_count += 1
                            failed_vendors.append(vendor['name'])
                    
                    # STEP 4: Check results and ROLLBACK if complete failure
                    if success_count == 0 and failed_count > 0:
                        # ALL emails failed - DELETE the RFQ
                        st.error(f"❌ ALL emails failed to send!")
                        with st.spinner("🔄 Rolling back - deleting RFQ..."):
                            db.delete_rfq(rfq_id)
                            st.error("🚫 RFQ has been deleted because no emails were sent")
                            st.warning("⚠️ Please check your email settings and try again")
                            st.info("💡 Even though connection test passed, actual sending failed. This could be due to:")
                            st.info("  • Rate limiting by Gmail")
                            st.info("  • Invalid recipient addresses")
                            st.info("  • Network issues")
                            st.stop()
                    
                    # STEP 5: Show results for successful/partial cases
                    if success_count == len(st.session_state['vendors']):
                        # All emails sent successfully
                        st.success(f"✅ Perfect! All {success_count} emails sent successfully!")
                        st.balloons()
                    elif success_count > 0:
                        # Partial success
                        st.warning(f"⚠️ Partial success: {success_count} sent, {failed_count} failed")
                        st.error(f"Failed vendors: {', '.join(failed_vendors)}")
                        st.info("💡 Tip: Go to 'Active RFQs' page to resend to failed vendors")
            else:
                st.info("📧 RFQ created! Emails will be sent later via the 'Active RFQs' page")
            
            # Show follow-up info
            if followup_count > 0:
                st.info(f"🔄 Automatic follow-ups enabled: {followup_count} reminders every {followup_interval} hours")
                st.caption("Follow-ups will be sent automatically by GitHub Actions every 30 minutes")
            
            # Clear session
            if 'vendors' in st.session_state:
                del st.session_state['vendors']
            if 'items' in st.session_state:
                del st.session_state['items']
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
            # If RFQ was created but something went wrong, try to clean up
            if rfq_id:
                try:
                    st.warning(f"⚠️ Attempting to delete RFQ #{rfq_id} due to error...")
                    db.delete_rfq(rfq_id)
                    st.info("🔄 RFQ deleted")
                except:
                    st.error(f"⚠️ Could not delete RFQ #{rfq_id}. Please delete manually from Active RFQs page.")
            
            with st.expander("Show Error Details"):
                import traceback
                st.code(traceback.format_exc())
