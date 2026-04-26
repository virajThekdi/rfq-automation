"""Page 2: Active RFQs with Follow-up Management"""
import streamlit as st
import sys
sys.path.insert(0, '..')
from database.db_manager import DatabaseManager
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Active RFQs", page_icon="📊", layout="wide")
st.title("📊 Active RFQs & Follow-up Management")

db = DatabaseManager()
load_dotenv()
active_rfqs = db.get_active_rfqs()

if not active_rfqs:
    st.info("📬 No active RFQs. Create your first RFQ!")
    if st.button("➕ Create RFQ"):
        st.switch_page("pages/1_📤_Create_RFQ.py")
else:
    # Global send follow-ups button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**{len(active_rfqs)} Active RFQ(s)**")
    with col2:
        if st.button("🔄 Send All Follow-ups", type="primary", use_container_width=True):
            with st.spinner("Checking all RFQs for follow-ups..."):
                try:
                    from modules import followup_manager
                    
                    sender_email = os.getenv('EMAIL_ADDRESS')
                    sender_password = os.getenv('EMAIL_PASSWORD')
                    
                    if not sender_email or not sender_password:
                        st.error("❌ Email credentials not found in .env")
                    else:
                        results = followup_manager.check_all_active_rfqs(
                            db_manager=db,
                            sender_email=sender_email,
                            sender_password=sender_password
                        )
                        
                        if results['total_followups_sent'] > 0:
                            st.success(f"✅ Sent {results['total_followups_sent']} follow-up(s)!")
                            for rfq_result in results['rfq_results']:
                                if rfq_result['result']['followups_sent'] > 0:
                                    st.caption(f"  • RFQ #{rfq_result['rfq_id']}: {rfq_result['result']['followups_sent']} sent")
                            st.rerun()
                        else:
                            st.info("ℹ️ No follow-ups needed at this time")
                            
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    with st.expander("Show Details"):
                        import traceback
                        st.code(traceback.format_exc())
    
    st.markdown("---")
    
    # Display each RFQ
    for rfq in active_rfqs:
        with st.expander(f"📤 {rfq['subject']} (RFQ #{rfq['id']})", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.metric("Total Vendors", rfq['total_vendors'])
                st.metric("Responses Received", rfq['responded_vendors'])
                
                # Progress bar
                progress = rfq['responded_vendors'] / rfq['total_vendors'] if rfq['total_vendors'] > 0 else 0
                st.progress(progress)
            
            with col2:
                st.write(f"**Created:** {rfq['created_at'][:19]}")
                st.write(f"**Deadline:** {rfq['deadline_time'][:19]}")
                
                # Time remaining
                deadline = datetime.fromisoformat(rfq['deadline_time'])
                now = datetime.now()
                hours_remaining = (deadline - now).total_seconds() / 3600
                
                if hours_remaining > 0:
                    days_remaining = int(hours_remaining / 24)
                    if days_remaining > 0:
                        st.info(f"⏰ {days_remaining} day(s) remaining")
                    else:
                        st.warning(f"⏰ {int(hours_remaining)} hour(s) remaining")
                else:
                    st.error("⏰ Deadline passed")
                
                # Follow-up settings
                if rfq['followup_count'] > 0:
                    st.success(f"🔄 Follow-ups: {rfq['followup_count']} reminders, every {rfq['followup_interval']}h")
                else:
                    st.caption("🔄 No follow-ups configured")
            
            with col3:
                if st.button("💬 View Responses", key=f"resp_{rfq['id']}", use_container_width=True):
                    st.session_state['selected_rfq_id'] = rfq['id']
                    st.switch_page("pages/3_💬_Responses.py")
                
                # Send follow-ups button
                if rfq['followup_count'] > 0:
                    if st.button("📧 Send Follow-ups", key=f"followup_{rfq['id']}", use_container_width=True):
                        with st.spinner(f"Checking RFQ #{rfq['id']} for follow-ups..."):
                            try:
                                from modules import followup_manager
                                
                                sender_email = os.getenv('EMAIL_ADDRESS')
                                sender_password = os.getenv('EMAIL_PASSWORD')
                                
                                if not sender_email or not sender_password:
                                    st.error("❌ Email credentials missing")
                                else:
                                    results = followup_manager.send_followups(
                                        db_manager=db,
                                        rfq_id=rfq['id'],
                                        sender_email=sender_email,
                                        sender_password=sender_password
                                    )
                                    
                                    if results['success']:
                                        if results['followups_sent'] > 0:
                                            st.success(f"✅ {results['message']}")
                                            st.rerun()
                                        else:
                                            st.info(results['message'])
                                            
                                            # Show details
                                            if results['followups_needed'] == 0:
                                                vendors = db.get_vendors(rfq['id'])
                                                pending = [v for v in vendors if v['response_status'] == 'pending']
                                                
                                                if pending:
                                                    st.caption("Reasons follow-ups not sent:")
                                                    for v in pending:
                                                        if v['followup_sent_count'] >= rfq['followup_count']:
                                                            st.caption(f"  • {v['name']}: Max follow-ups reached ({v['followup_sent_count']}/{rfq['followup_count']})")
                                                        else:
                                                            # Calculate time since last contact
                                                            if v['last_followup_at']:
                                                                last_contact = datetime.fromisoformat(v['last_followup_at'])
                                                            else:
                                                                last_contact = datetime.fromisoformat(v['sent_at'])
                                                            
                                                            hours_since = (datetime.now() - last_contact).total_seconds() / 3600
                                                            hours_needed = rfq['followup_interval']
                                                            hours_remaining = hours_needed - hours_since
                                                            
                                                            if hours_remaining > 0:
                                                                st.caption(f"  • {v['name']}: Too soon, wait {int(hours_remaining)}h more")
                                    else:
                                        st.error(f"❌ {results['message']}")
                                    
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                
                # Delete button with confirmation
                st.markdown("---")
                delete_key = f"delete_{rfq['id']}"
                confirm_key = f"confirm_delete_{rfq['id']}"
                
                # Check if we're in confirmation mode
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    if st.button("🗑️ Delete RFQ", key=delete_key, type="secondary", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Confirm deletion?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Yes", key=f"yes_{rfq['id']}", use_container_width=True):
                            try:
                                success = db.delete_rfq(rfq['id'])
                                if success:
                                    st.success(f"✅ RFQ #{rfq['id']} deleted!")
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete RFQ")
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    with col_no:
                        if st.button("❌ No", key=f"no_{rfq['id']}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
            
            # Vendors table
            st.subheader("📋 Vendor Status")
            vendors = db.get_vendors(rfq['id'])
            
            vendors_data = []
            for v in vendors:
                # Calculate follow-up status
                followup_status = f"{v['followup_sent_count']}/{rfq['followup_count']}"
                
                last_contact = "Initial email"
                if v['last_followup_at']:
                    last_followup = datetime.fromisoformat(v['last_followup_at'])
                    last_contact = f"Reminder sent {last_followup.strftime('%m/%d %H:%M')}"
                
                vendors_data.append({
                    'Vendor': v['name'],
                    'Email': v['email'],
                    'Status': '✅ Responded' if v['response_status'] == 'responded' else '⏳ Pending',
                    'Follow-ups Sent': followup_status,
                    'Last Contact': last_contact,
                    'Sent At': v['sent_at'][:19],
                    'Responded At': v['responded_at'][:19] if v['responded_at'] else '-'
                })
            
            df = pd.DataFrame(vendors_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Items table
            st.subheader("📦 RFQ Items")
            items = db.get_items(rfq['id'])
            
            items_data = []
            for item in items:
                items_data.append({
                    'Item': item['name'],
                    'Description': item['description'],
                    'Quantity': item['quantity'],
                    'Unit': item['unit']
                })
            
            df_items = pd.DataFrame(items_data)
            st.dataframe(df_items, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.caption("💡 Tip: Follow-ups are sent automatically based on your configured interval. Use 'Send Follow-ups' to send them immediately.")
