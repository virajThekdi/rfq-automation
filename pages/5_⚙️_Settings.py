"""Page 5: Settings"""
import streamlit as st
import os
from dotenv import load_dotenv, set_key

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

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

# Show environment info
st.info("🌍 **Environment Detection:**")
col1, col2 = st.columns(2)

with col1:
    is_local = os.getenv('EMAIL_ADDRESS') is not None
    if is_local:
        st.success("✅ Running locally (using .env file)")
    else:
        st.info("☁️ Running on Streamlit Cloud (using st.secrets)")

with col2:
    email_found = get_credential('EMAIL_ADDRESS') is not None
    if email_found:
        st.success("✅ Email credentials found")
    else:
        st.error("❌ Email credentials NOT found")

st.markdown("---")

# Credential status check
st.subheader("🔍 Credential Status")

credentials = {
    'EMAIL_ADDRESS': get_credential('EMAIL_ADDRESS'),
    'EMAIL_PASSWORD': get_credential('EMAIL_PASSWORD'),
    'GEMINI_API_KEY': get_credential('GEMINI_API_KEY'),
    'SUPABASE_URL': get_credential('SUPABASE_URL'),
    'SUPABASE_KEY': get_credential('SUPABASE_KEY'),
}

status_data = []
for key, value in credentials.items():
    if value:
        status = "✅ Configured"
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
    else:
        status = "❌ Missing"
        masked = "-"
    
    status_data.append({
        'Credential': key,
        'Status': status,
        'Value (masked)': masked
    })

import pandas as pd
st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)

st.markdown("---")

# Configuration section
st.subheader("📧 Email Configuration")

st.warning("⚠️ **Important:** Configuration method depends on your environment:")
st.write("• **Local development (Codespaces/local machine):** Edit `.env` file directly")
st.write("• **Streamlit Cloud:** Configure in app settings → Secrets (TOML format)")

email_address = st.text_input("Gmail Address:", value=get_credential('EMAIL_ADDRESS') or '')
email_password = st.text_input("Gmail App Password:", value=get_credential('EMAIL_PASSWORD') or '', type="password")

st.info("💡 **To get Gmail App Password:**\n1. Go to Google Account settings\n2. Security → 2-Step Verification → App passwords\n3. Generate new app password for 'Mail'")

st.markdown("---")

st.subheader("🤖 AI Configuration")

gemini_key = st.text_input("Gemini API Key:", value=get_credential('GEMINI_API_KEY') or '', type="password")

st.markdown("---")

# Save button (only works for local .env)
if st.button("💾 Save to .env (Local Only)", type="primary"):
    try:
        # Check if running locally
        if not os.path.exists('.env'):
            st.warning("⚠️ No .env file found. Creating one...")
            with open('.env', 'w') as f:
                f.write("# RFQ Automation Environment Variables\n")
        
        # Save to .env
        set_key('.env', 'EMAIL_ADDRESS', email_address)
        set_key('.env', 'EMAIL_PASSWORD', email_password)
        set_key('.env', 'GEMINI_API_KEY', gemini_key)
        
        st.success("✅ Settings saved to .env file!")
        st.info("🔄 Restart the app for changes to take effect")
        
    except Exception as e:
        st.error(f"❌ Error saving to .env: {e}")
        st.info("💡 If on Streamlit Cloud, configure secrets in app settings instead")

# Instructions for Streamlit Cloud
with st.expander("📖 How to Configure Streamlit Cloud Secrets"):
    st.markdown("""
    **For Streamlit Cloud deployment:**
    
    1. Go to your app dashboard: https://share.streamlit.io/
    2. Click on your app → Settings (⚙️) → Secrets
    3. Add credentials in TOML format:
    
    ```toml
    EMAIL_ADDRESS = "your-email@gmail.com"
    EMAIL_PASSWORD = "your-app-password"
    GEMINI_API_KEY = "your-gemini-key"
    SUPABASE_URL = "your-supabase-url"
    SUPABASE_KEY = "your-supabase-key"
    ```
    
    4. Click "Save"
    5. App will automatically restart with new secrets
    """)

# Instructions for GitHub Actions
with st.expander("🔧 How to Configure GitHub Actions Secrets"):
    st.markdown("""
    **For automation worker (GitHub Actions):**
    
    1. Go to: https://github.com/virajThekdi/rfq-automation/settings/secrets/actions
    2. Add these secrets:
       - `EMAIL_ADDRESS`
       - `EMAIL_PASSWORD`
       - `GEMINI_API_KEY`
       - `SUPABASE_URL`
       - `SUPABASE_KEY`
    3. GitHub Actions will use these for automated tasks
    """)

st.markdown("---")
st.caption("💡 Tip: Keep your credentials secure. Never commit .env file to git!")
