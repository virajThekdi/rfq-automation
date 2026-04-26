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
            
            st.success(f"✅ Loaded {len(vendors_list)} vendors and {len(items_list)} items")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Vendors:**")
                st.dataframe(pd.DataFrame(vendors_list))
            with col2:
                st.write("**RFQ Items:**")
                st.dataframe(pd.DataFrame(items_list))
            
            # Data is already in list of dicts format - no need to call .to_dict()
            st.session_state['vendors'] = vendors_list
            st.session_state['items'] = items_list
            
        except Exception as e:
            st.error(f"❌ Error reading Excel: {e}")
else:
    st.subheader("✏️ Manual Entry")
    
    # Vendors input
    st.write("**Add Vendors:**")
    num_vendors = st.number_input("Number of vendors:", min_value=1, max_value=50, value=3)
    
    vendors = []
    for i in range(num_vendors):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"Vendor {i+1} Name", key=f"v_name_{i}")
        with col2:
            email = st.text_input(f"Vendor {i+1} Email", key=f"v_email_{i}")
        if name and email:
            vendors.append({'name': name, 'email': email})
    
    st.session_state['vendors'] = vendors
    
    st.markdown("---")
    
    # Items input
    st.write("**Add Items:**")
    num_items = st.number_input("Number of items:", min_value=1, max_value=50, value=3)
    
    items = []
    for i in range(num_items):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            name = st.text_input(f"Item {i+1}", key=f"i_name_{i}")
        with col2:
            desc = st.text_input(f"Description", key=f"i_desc_{i}")
        with col3:
            qty = st.text_input(f"Quantity", key=f"i_qty_{i}")
        with col4:
            unit = st.text_input(f"Unit", key=f"i_unit_{i}")
        if name:
            items.append({'item_name': name, 'description': desc, 'quantity': qty, 'unit': unit})
    
    st.session_state['items'] = items

st.markdown("---")

# Email details
st.subheader("📬 Email Configuration")

col1, col2 = st.columns(2)
with col1:
    subject = st.text_input("Email Subject:", value="RFQ Request - Quotation Needed")
    body = st.text_area("Email Body:", value="Please provide your quotation for the following items:", height=150)
with col2:
    footer = st.text_area("Email Footer:", value="Looking forward to your response.\n\nBest regards", height=150)

st.markdown("---")

# Deadline and Follow-ups (Enhanced UI)
st.subheader("⏰ Deadline & Automated Follow-ups")

col1, col2 = st.columns([2, 1])

with col1:
    st.write("**Deadline Settings:**")
    deadline_days = st.number_input("Deadline (days from now):", min_value=1, max_value=30, value=3)
    deadline_date = datetime.now() + timedelta(days=deadline_days)
    st.caption(f"📅 Deadline will be: {deadline_date.strftime('%B %d, %Y at %I:%M %p')}")

with col2:
    st.write("**Quick Presets:**")
    if st.button("⚡ 24 hours", use_container_width=True):
        deadline_days = 1
    if st.button("📅 3 days", use_container_width=True):
        deadline_days = 3
    if st.button("📆 1 week", use_container_width=True):
        deadline_days = 7

st.markdown("---")

# Follow-up configuration with better UI
st.write("### 🔄 Automatic Follow-up Reminders")

enable_followups = st.checkbox("Enable automatic follow-up reminders to pending vendors", value=True)

if enable_followups:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**How many reminders?**")
        followup_count = st.select_slider(
            "Number of follow-ups:",
            options=[0, 1, 2, 3, 4, 5],
            value=2,
            help="System will send this many reminders to vendors who haven't responded"
        )
        
        if followup_count > 0:
            st.success(f"✅ Will send up to {followup_count} reminder(s) per vendor")
        else:
            st.info("ℹ️ No follow-ups will be sent")
    
    with col2:
        st.write("**How often to remind?**")
        interval_option = st.radio(
            "Send reminders every:",
            ["12 hours", "24 hours (1 day)", "48 hours (2 days)", "72 hours (3 days)"],
            index=1
        )
        
        # Convert to hours
        interval_map = {
            "12 hours": 12,
            "24 hours (1 day)": 24,
            "48 hours (2 days)": 48,
            "72 hours (3 days)": 72
        }
        followup_interval = interval_map[interval_option]
        
        st.info(f"⏱️ Reminders sent every {followup_interval} hours")
    
    # Show follow-up timeline
    if followup_count > 0:
        st.write("**Follow-up Timeline:**")
        timeline_html = "<div style='background-color: #f0f0f0; padding: 15px; border-radius: 5px;'>"
        timeline_html += f"<strong>Initial RFQ:</strong> Sent immediately<br>"
        
        for i in range(1, followup_count + 1):
            hours_from_now = followup_interval * i
            reminder_time = datetime.now() + timedelta(hours=hours_from_now)
            timeline_html += f"<strong>Reminder #{i}:</strong> {hours_from_now}h later ({reminder_time.strftime('%b %d, %I:%M %p')})<br>"
        
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
else:
    followup_count = 0
    followup_interval = 0
    st.warning("⚠️ Follow-ups disabled. You'll need to manually check for responses.")

deadline_minutes = deadline_days * 24 * 60

st.markdown("---")

# Send button
st.write("### 🚀 Ready to Send?")

col1, col2 = st.columns([2, 1])

with col1:
    if 'vendors' in st.session_state and 'items' in st.session_state:
        st.success(f"✅ Ready: {len(st.session_state.get('vendors', []))} vendors, {len(st.session_state.get('items', []))} items")
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
        try:
            with st.spinner("Creating RFQ..."):
                # Create RFQ in database
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
            
            # Send emails if requested
            if send_now:
                with st.spinner("📧 Sending emails..."):
                    sender_email = os.getenv('EMAIL_ADDRESS')
                    sender_password = os.getenv('EMAIL_PASSWORD')
                    
                    if not sender_email or not sender_password:
                        st.error("❌ Email credentials not found in .env file")
                    else:
                        # Generate and send emails
                        success_count = 0
                        failed_count = 0
                        
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
                            except Exception as e:
                                st.warning(f"⚠️ Failed to send to {vendor['name']}: {e}")
                                failed_count += 1
                        
                        # Summary
                        if success_count > 0:
                            st.success(f"✅ Emails sent: {success_count}/{len(st.session_state['vendors'])}")
                        if failed_count > 0:
                            st.warning(f"⚠️ Failed: {failed_count}")
            else:
                st.info("📧 Emails will be sent later via the Follow-ups page")
            
            # Show follow-up info
            if followup_count > 0:
                st.info(f"🔄 Automatic follow-ups enabled: {followup_count} reminders every {followup_interval} hours")
                st.caption("Go to 'Active RFQs' page to manually send follow-ups, or they will be sent automatically by the scheduler")
            
            st.balloons()
            
            # Clear session
            if 'vendors' in st.session_state:
                del st.session_state['vendors']
            if 'items' in st.session_state:
                del st.session_state['items']
                
        except Exception as e:
            st.error(f"❌ Error creating RFQ: {e}")
