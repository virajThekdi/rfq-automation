"""database/db_manager.py
Database operations for RFQ Streamlit app - Supabase (PostgreSQL) Version
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Manages all database operations for RFQ system using Supabase"""
    
    def __init__(self):
        """Initialize Supabase client"""
        # Try to get from environment first (local)
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        # If not in env, try Streamlit secrets (cloud)
        if not supabase_url or not supabase_key:
            try:
                import streamlit as st
                supabase_url = st.secrets.get("SUPABASE_URL")
                supabase_key = st.secrets.get("SUPABASE_KEY")
            except:
                pass
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment or secrets")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    # ========================================================================
    # RFQ OPERATIONS
    # ========================================================================
    
    def create_rfq(self, subject: str, body: str, footer: str, 
                   deadline_minutes: int, followup_count: int, 
                   followup_interval: int) -> int:
        """Create a new RFQ and return its ID"""
        now = datetime.now().isoformat()
        deadline = datetime.now() + timedelta(minutes=deadline_minutes)
        deadline_str = deadline.isoformat()
        
        response = self.supabase.table('rfqs').insert({
            'subject': subject,
            'body': body,
            'footer': footer,
            'deadline_minutes': deadline_minutes,
            'deadline_time': deadline_str,
            'followup_count': followup_count,
            'followup_interval': followup_interval,
            'created_at': now,
            'status': 'active'
        }).execute()
        
        return response.data[0]['id']
    
    def get_rfq(self, rfq_id: int) -> Optional[Dict]:
        """Get RFQ by ID"""
        response = self.supabase.table('rfqs').select("*").eq('id', rfq_id).execute()
        return response.data[0] if response.data else None
    
    def get_active_rfqs(self) -> List[Dict]:
        """Get all active RFQs"""
        response = self.supabase.table('rfqs').select("*").eq('status', 'active').execute()
        return response.data
    
    def update_rfq_status(self, rfq_id: int, status: str):
        """Update RFQ status"""
        self.supabase.table('rfqs').update({
            'status': status,
            'completed_at': datetime.now().isoformat() if status == 'completed' else None
        }).eq('id', rfq_id).execute()
    
    
    def delete_rfq(self, rfq_id: int):
        """Delete RFQ and all related data (CASCADE in database handles foreign keys)"""
        self.supabase.table('rfqs').delete().eq('id', rfq_id).execute()
        return True
    
    # ========================================================================
    # ITEM OPERATIONS
    # ========================================================================
    
    def add_items(self, rfq_id: int, items: List[Dict]):
        """Add multiple items to an RFQ"""
        items_data = []
        for item in items:
            # Handle both 'name' and 'item_name' keys (Excel uses 'item_name', manual uses 'name')
            item_name = item.get('item_name', item.get('name', ''))
            items_data.append({
                'rfq_id': rfq_id,
                'name': item_name,
                'description': item.get('description', ''),
                'quantity': item.get('quantity', ''),
                'unit': item.get('unit', '')
            })
        self.supabase.table('items').insert(items_data).execute()
    
    def get_items(self, rfq_id: int) -> List[Dict]:
        """Get all items for an RFQ"""
        response = self.supabase.table('items').select("*").eq('rfq_id', rfq_id).execute()
        return response.data
    
    # ========================================================================
    # VENDOR OPERATIONS
    # ========================================================================
    
    def add_vendors(self, rfq_id: int, vendors: List[Dict]):
        """Add multiple vendors to an RFQ"""
        sent_at = datetime.now().isoformat()
        vendors_data = []
        for vendor in vendors:
            vendors_data.append({
                'rfq_id': rfq_id,
                'name': vendor['name'],
                'email': vendor['email'],
                'sent_at': sent_at,
                'response_status': 'pending'
            })
        self.supabase.table('vendors').insert(vendors_data).execute()
        
        # Update total_vendors count
        self.supabase.table('rfqs').update({
            'total_vendors': len(vendors)
        }).eq('id', rfq_id).execute()
    
    def get_vendors(self, rfq_id: int) -> List[Dict]:
        """Get all vendors for an RFQ"""
        response = self.supabase.table('vendors').select("*").eq('rfq_id', rfq_id).execute()
        return response.data
    
    def update_vendor_status(self, vendor_id: int, status: str):
        """Update vendor response status"""
        # Update vendor
        self.supabase.table('vendors').update({
            'response_status': status,
            'responded_at': datetime.now().isoformat()
        }).eq('id', vendor_id).execute()
        
        # Get vendor's RFQ ID
        vendor_response = self.supabase.table('vendors').select('rfq_id').eq('id', vendor_id).execute()
        if vendor_response.data:
            rfq_id = vendor_response.data[0]['rfq_id']
            
            # Count responded vendors
            responded_response = self.supabase.table('vendors').select('id').eq('rfq_id', rfq_id).eq('response_status', 'responded').execute()
            responded_count = len(responded_response.data)
            
            # Update RFQ responded count
            self.supabase.table('rfqs').update({
                'responded_vendors': responded_count
            }).eq('id', rfq_id).execute()
    
    
    def update_vendor_followup(self, vendor_id: int):
        """Update vendor follow-up tracking when reminder is sent"""
        # Get current followup count
        vendor_response = self.supabase.table('vendors').select('followup_sent_count').eq('id', vendor_id).execute()
        current_count = vendor_response.data[0]['followup_sent_count'] if vendor_response.data else 0
        
        # Update vendor
        self.supabase.table('vendors').update({
            'followup_sent_count': current_count + 1,
            'last_followup_at': datetime.now().isoformat()
        }).eq('id', vendor_id).execute()
    
    # ========================================================================
    # RESPONSE OPERATIONS
    # ========================================================================
    
    def add_response(self, vendor_id: int, email_subject: str, 
                    email_body: str, parsed_json: str, 
                    is_quotation: bool, ai_provider: str) -> int:
        """Add a vendor response"""
        response = self.supabase.table('responses').insert({
            'vendor_id': vendor_id,
            'email_subject': email_subject,
            'email_body': email_body,
            'parsed_json': parsed_json,
            'is_quotation': is_quotation,
            'ai_provider': ai_provider,
            'received_at': datetime.now().isoformat()
        }).execute()
        
        return response.data[0]['id']
    
    def get_responses(self, rfq_id: int) -> List[Dict]:
        """Get all responses for an RFQ"""
        # Get vendors for this RFQ
        vendors_response = self.supabase.table('vendors').select('id').eq('rfq_id', rfq_id).execute()
        vendor_ids = [v['id'] for v in vendors_response.data]
        
        if not vendor_ids:
            return []
        
        # Get responses for these vendors
        responses = self.supabase.table('responses').select("*").in_('vendor_id', vendor_ids).execute()
        return responses.data
    
    def add_quotation(self, response_id: int, item_name: str, 
                      price: str, unit: str, notes: str) -> int:
        """Add a quotation line item"""
        response = self.supabase.table('quotations').insert({
            'response_id': response_id,
            'item_name': item_name,
            'price': price,
            'unit': unit,
            'notes': notes
        }).execute()
        
        return response.data[0]['id']
    
    def get_quotations(self, response_id: int) -> List[Dict]:
        """Get all quotations for a response"""
        response = self.supabase.table('quotations').select("*").eq('response_id', response_id).execute()
        return response.data
