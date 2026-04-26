"""Page 3: View Responses with Email Monitoring"""
import streamlit as st
import sys
sys.path.insert(0, '..')
from database.db_manager import DatabaseManager
import json
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

# Import QCF modules
try:
    from modules import qcf_enhanced, qcf_generator
except ImportError:
    st.error("⚠️ QCF modules not found. Please check installation.")

st.set_page_config(page_title="Responses", page_icon="💬", layout="wide")

# Initialize
db = DatabaseManager()
load_dotenv()

# Title and Check Now button
col1, col2 = st.columns([3, 1])
with col1:
    st.title("💬 Vendor Responses")
with col2:
    check_button = st.button("🔄 Check New Emails", type="primary", use_container_width=True)

# Check for new responses
if check_button:
    with st.spinner("📧 Checking Gmail inbox..."):
        try:
            # Load credentials
            sender_email = os.getenv('EMAIL_ADDRESS')
            sender_password = os.getenv('EMAIL_PASSWORD')
            gemini_key = os.getenv('GEMINI_API_KEY')
            
            if not all([sender_email, sender_password, gemini_key]):
                st.error("❌ Missing credentials in .env file")
                st.info("Required: EMAIL_ADDRESS, EMAIL_PASSWORD, GEMINI_API_KEY")
            else:
                # Import modules
                from modules import email_monitor, ai_parser
                
                # Get selected RFQ (if any)
                active_rfqs = db.get_active_rfqs()
                
                if not active_rfqs:
                    st.warning("No active RFQs to check")
                else:
                    # Check all active RFQs
                    total_new = 0
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, rfq in enumerate(active_rfqs):
                        rfq_id = rfq['id']
                        status_text.text(f"Checking RFQ #{rfq_id}: {rfq['subject'][:50]}...")
                        
                        # Check for responses to this RFQ
                        results = email_monitor.check_new_responses(
                            email_address=sender_email,
                            password=sender_password,
                            rfq_id=rfq_id,
                            db_manager=db,
                            ai_parser=ai_parser,
                            gemini_api_key=gemini_key
                        )
                        
                        if results["success"]:
                            total_new += results["new_responses"]
                            
                            if results["new_responses"] > 0:
                                st.success(f"✅ RFQ #{rfq_id}: Found {results['new_responses']} new response(s)")
                                for vendor_email in results["processed"]:
                                    st.caption(f"  ✓ {vendor_email}")
                            
                            if results["failed"]:
                                st.warning(f"⚠️ RFQ #{rfq_id}: {len(results['failed'])} failed to process")
                        else:
                            st.error(f"❌ RFQ #{rfq_id}: {results['message']}")
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(active_rfqs))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Final summary
                    if total_new > 0:
                        st.balloons()
                        st.success(f"🎉 Total: {total_new} new response(s) processed!")
                        st.info("Page will refresh to show new responses...")
                        st.rerun()
                    else:
                        st.info("📭 No new responses found in inbox")
                
        except Exception as e:
            st.error(f"❌ Error checking inbox: {e}")
            with st.expander("Show Error Details"):
                import traceback
                st.code(traceback.format_exc())

st.markdown("---")

# Select RFQ
active_rfqs = db.get_active_rfqs()

if not active_rfqs:
    st.info("📬 No active RFQs. Create one to start receiving responses!")
    if st.button("➕ Create New RFQ"):
        st.switch_page("pages/1_📤_Create_RFQ.py")
else:
    # RFQ selector
    rfq_options = {f"RFQ #{rfq['id']}: {rfq['subject']}": rfq['id'] for rfq in active_rfqs}
    selected_rfq_name = st.selectbox("Select RFQ to view responses:", list(rfq_options.keys()))
    selected_rfq_id = rfq_options[selected_rfq_name]
    
    # Get RFQ details
    rfq = db.get_rfq(selected_rfq_id)
    vendors = db.get_vendors(selected_rfq_id)
    responses = db.get_responses(selected_rfq_id)
    
    # Response statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Vendors", len(vendors))
    with col2:
        responded = sum(1 for v in vendors if v['response_status'] == 'responded')
        st.metric("Responses Received", responded, delta=f"{responded}/{len(vendors)}")
    with col3:
        pending = len(vendors) - responded
        st.metric("Pending", pending, delta="-" + str(pending) if pending > 0 else "0")
    
    st.markdown("---")
    
    # Vendor Status Table
    st.subheader("📊 Vendor Response Status")
    vendor_status = []
    for v in vendors:
        vendor_status.append({
            "Vendor": v['name'],
            "Email": v['email'],
            "Status": "✅ Responded" if v['response_status'] == 'responded' else "⏳ Pending",
            "Sent At": v['sent_at'][:19],
            "Responded At": v['responded_at'][:19] if v['responded_at'] else "-"
        })
    
    df_vendors = pd.DataFrame(vendor_status)
    st.dataframe(df_vendors, use_container_width=True, hide_index=True)
    
    if not responses:
        st.info("⏳ No responses received yet for this RFQ.")
        st.info("💡 Click 'Check New Emails' button above to scan inbox for responses.")
    else:
        st.markdown("---")
        
        # QCF Generation Section
        st.subheader("📊 Generate Quotation Comparison Report")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.info("💡 Generate side-by-side vendor price comparison in Excel format")
        
        with col2:
            if st.button("📥 Generate QCF Report", type="primary", use_container_width=True):
                with st.spinner("Generating comparison report..."):
                    try:
                        items = db.get_items(selected_rfq_id)
                        
                        # Build responses list for QCF
                        responses_data = []
                        for resp in responses:
                            if resp['is_quotation'] and resp['parsed_json']:
                                try:
                                    parsed = json.loads(resp['parsed_json'])
                                    responses_data.append({
                                        'vendor_name': resp['vendor_name'],
                                        'vendor_email': resp['vendor_email'],
                                        'items': parsed.get('items', []),
                                        'notes': parsed.get('notes', '')
                                    })
                                except:
                                    pass
                        
                        if responses_data:
                            # Generate enhanced QCF
                            output_path = qcf_enhanced.generate_enhanced_qcf({
                                'rfq_subject': rfq['subject'],
                                'items': [{'name': item['name'], 'description': item['description'], 
                                          'quantity': item['quantity'], 'unit': item['unit']} 
                                         for item in items],
                                'responses': responses_data
                            })
                            
                            if output_path and os.path.exists(output_path):
                                st.success("✅ QCF Report generated successfully!")
                                
                                # Show download button
                                with open(output_path, 'rb') as f:
                                    st.download_button(
                                        label="📥 Download QCF Excel Report",
                                        data=f,
                                        file_name=os.path.basename(output_path),
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        type="primary"
                                    )
                            else:
                                st.error("❌ Failed to generate QCF report")
                        else:
                            st.warning("⚠️ No valid quotations to compare yet")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating QCF: {e}")
                        with st.expander("Show Error Details"):
                            import traceback
                            st.code(traceback.format_exc())
        
        with col3:
            st.caption("📋 Quick summary")
            valid_quotations = sum(1 for r in responses if r['is_quotation'])
            st.metric("Valid Quotes", valid_quotations)
        
        st.markdown("---")
        
        # Individual Responses
        st.subheader("📧 Individual Vendor Responses")
        
        for i, resp in enumerate(responses):
            is_quotation = resp['is_quotation']
            
            # Color coding based on status
            status_emoji = "✅" if is_quotation else "⚠️"
            
            with st.expander(
                f"{status_emoji} {resp['vendor_name']} - {resp['received_at'][:19]}", 
                expanded=False
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Vendor:** {resp['vendor_name']}")
                    st.write(f"**Email:** {resp['vendor_email']}")
                    st.write(f"**Received:** {resp['received_at'][:19]}")
                    st.write(f"**Parser Used:** {resp['ai_provider']}")
                
                with col2:
                    if is_quotation:
                        st.success("✅ Valid Quotation")
                    else:
                        st.warning("⚠️ Not a Quotation")
                
                # Show parsed quotation
                if resp['parsed_json']:
                    try:
                        parsed = json.loads(resp['parsed_json'])
                        
                        if 'items' in parsed and parsed['items']:
                            st.subheader("📦 Quoted Items:")
                            items_data = []
                            total = 0
                            
                            for item in parsed['items']:
                                price_str = str(item.get('price', '-'))
                                # Try to extract numeric value for total
                                try:
                                    price_num = float(price_str.replace(',', '').replace('₹', '').replace('$', '').strip())
                                    total += price_num
                                except:
                                    price_num = None
                                
                                items_data.append({
                                    'Item': item.get('item_name', '-'),
                                    'Quantity': item.get('quantity', '-'),
                                    'Unit': item.get('unit', '-'),
                                    'Price': price_str,
                                    'Delivery': item.get('delivery', '-')
                                })
                            
                            df = pd.DataFrame(items_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            if total > 0:
                                st.metric("Total Amount", f"₹{total:,.2f}")
                        
                        if 'notes' in parsed and parsed['notes']:
                            st.info(f"📝 **Additional Notes:** {parsed['notes']}")
                            
                    except Exception as e:
                        st.error(f"Could not parse quotation data: {e}")
                
                # Show raw email (collapsed by default)
                with st.expander("📄 View Raw Email Body"):
                    st.text_area(
                        "Email Content:", 
                        resp['email_body'], 
                        height=200, 
                        key=f"email_{i}",
                        disabled=True
                    )

# Footer
st.markdown("---")
st.caption("💡 Tip: Click 'Check New Emails' regularly to fetch latest responses, or wait for automatic monitoring (if enabled)")
