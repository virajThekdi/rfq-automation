"""Page 5: Settings"""
import streamlit as st
import os
from dotenv import load_dotenv, set_key

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

load_dotenv()

st.subheader("📧 Email Configuration")

email_address = st.text_input("Gmail Address:", value=os.getenv('EMAIL_ADDRESS', ''))
email_password = st.text_input("Gmail App Password:", value=os.getenv('EMAIL_PASSWORD', ''), type="password")

st.markdown("---")

st.subheader("🤖 AI Configuration")

gemini_key = st.text_input("Gemini API Key:", value=os.getenv('GEMINI_API_KEY', ''), type="password")
openai_key = st.text_input("OpenAI API Key (optional):", value=os.getenv('OPENAI_API_KEY', ''), type="password")
grok_key = st.text_input("Grok API Key (optional):", value=os.getenv('GROK_API_KEY', ''), type="password")

if st.button("💾 Save Settings", type="primary"):
    try:
        env_path = '../.env'
        set_key(env_path, 'EMAIL_ADDRESS', email_address)
        set_key(env_path, 'EMAIL_PASSWORD', email_password)
        set_key(env_path, 'GEMINI_API_KEY', gemini_key)
        set_key(env_path, 'OPENAI_API_KEY', openai_key)
        set_key(env_path, 'GROK_API_KEY', grok_key)
        
        st.success("✅ Settings saved successfully!")
    except Exception as e:
        st.error(f"❌ Error saving settings: {e}")
