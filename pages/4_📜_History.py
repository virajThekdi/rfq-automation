"""Page 4: RFQ History"""
import streamlit as st
import sys
sys.path.insert(0, '..')
from database.db_manager import DatabaseManager
import pandas as pd

st.set_page_config(page_title="History", page_icon="📜", layout="wide")
st.title("📜 RFQ History")

db = DatabaseManager()

st.info("🚧 History page - Coming soon! Will show all past RFQs with search and analytics.")
