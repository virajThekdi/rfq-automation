"""RFQ Automation System - Streamlit Version
Main Dashboard and Entry Point
"""
import streamlit as st
import sys
import os
from datetime import datetime
from database.db_manager import DatabaseManager

# Page config
st.set_page_config(
    page_title="RFQ Automation System",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .activity-item {
        border-left: 3px solid #1f77b4;
        padding-left: 15px;
        margin-bottom: 15px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📤 RFQ Automation Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# Get statistics
active_rfqs = db.get_active_rfqs()
total_active = len(active_rfqs)

# Calculate total pending responses
total_pending = 0
for rfq in active_rfqs:
    vendors = db.get_vendors(rfq['id'])
    responded = sum(1 for v in vendors if v['response_status'] == 'responded')
    total_pending += (len(vendors) - responded)

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_active}</div>
        <div class="metric-label">Active RFQs</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
        <div class="metric-value">{total_pending}</div>
        <div class="metric-label">Pending Responses</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_responded = sum(rfq['responded_vendors'] for rfq in active_rfqs)
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
        <div class="metric-value">{total_responded}</div>
        <div class="metric-label">Responses Received</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Get completion rate
    if total_active > 0:
        total_vendors = sum(rfq['total_vendors'] for rfq in active_rfqs)
        rate = int((total_responded / total_vendors * 100)) if total_vendors > 0 else 0
    else:
        rate = 0
    st.markdown(f"""
    <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
        <div class="metric-value">{rate}%</div>
        <div class="metric-label">Response Rate</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Actions
st.subheader("🎯 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📤 Create New RFQ", use_container_width=True):
        st.switch_page("pages/1_📤_Create_RFQ.py")

with col2:
    if st.button("📊 View Active RFQs", use_container_width=True):
        st.switch_page("pages/2_📊_Active_RFQs.py")

with col3:
    if st.button("💬 View Responses", use_container_width=True):
        st.switch_page("pages/3_💬_Responses.py")

with col4:
    if st.button("📜 View History", use_container_width=True):
        st.switch_page("pages/4_📜_History.py")

st.markdown("---")

# Active RFQs Overview
st.subheader("📄 Active RFQs Overview")

if total_active == 0:
    st.info("📬 No active RFQs. Create your first RFQ to get started!")
    if st.button("➕ Create First RFQ", type="primary"):
        st.switch_page("pages/1_📤_Create_RFQ.py")
else:
    for rfq in active_rfqs:
        with st.expander(f"📤 {rfq['subject']} - {rfq['responded_vendors']}/{rfq['total_vendors']} responses"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Created:** {rfq['created_at'][:19]}")
                st.write(f"**Deadline:** {rfq['deadline_time'][:19]}")
                st.write(f"**Status:** {rfq['status'].title()}")
                
                # Progress bar
                progress = rfq['responded_vendors'] / rfq['total_vendors'] if rfq['total_vendors'] > 0 else 0
                st.progress(progress)
                st.caption(f"{rfq['responded_vendors']} of {rfq['total_vendors']} vendors responded")
            
            with col2:
                if st.button(f"View Details", key=f"view_{rfq['id']}"):
                    st.session_state['selected_rfq_id'] = rfq['id']
                    st.switch_page("pages/2_📊_Active_RFQs.py")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🚀 RFQ Automation System v2.0")

with col2:
    st.caption("💻 Cloud-hosted on Streamlit")

with col3:
    st.caption(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
