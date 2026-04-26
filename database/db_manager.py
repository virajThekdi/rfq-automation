"""database/db_manager.py
Database operations for RFQ Streamlit app
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

DB_PATH = "database/rfq_system.db"

class DatabaseManager:
    """Manages all database operations for RFQ system"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema"""
        # Read schema from schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema)
            conn.commit()
            conn.close()
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    # ========================================================================
    # RFQ OPERATIONS
    # ========================================================================
    
    def create_rfq(self, subject: str, body: str, footer: str, 
                   deadline_minutes: int, followup_count: int, 
                   followup_interval: int) -> int:
        """Create a new RFQ and return its ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        deadline = datetime.now()
        deadline = deadline + timedelta(minutes=deadline_minutes)
        deadline_str = deadline.isoformat()
        
        cursor.execute(
            """INSERT INTO rfqs 
               (subject, body, footer, deadline_minutes, deadline_time, 
                followup_count, followup_interval, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
            (subject, body, footer, deadline_minutes, deadline_str, 
             followup_count, followup_interval, now)
        )
        rfq_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rfq_id
    
    def get_rfq(self, rfq_id: int) -> Optional[Dict]:
        """Get RFQ by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rfqs WHERE id = ?", (rfq_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_active_rfqs(self) -> List[Dict]:
        """Get all active RFQs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM rfqs 
               WHERE status = 'active' 
               ORDER BY created_at DESC"""
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_rfq_status(self, rfq_id: int, status: str):
        """Update RFQ status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        completed_at = datetime.now().isoformat() if status == 'completed' else None
        cursor.execute(
            """UPDATE rfqs 
               SET status = ?, completed_at = ? 
               WHERE id = ?""",
            (status, completed_at, rfq_id)
        )
        conn.commit()
        conn.close()
    
    # ========================================================================
    # ITEM OPERATIONS
    # ========================================================================
    
    def add_items(self, rfq_id: int, items: List[Dict]):
        """Add multiple items to an RFQ"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for item in items:
            cursor.execute(
                """INSERT INTO items (rfq_id, name, description, quantity, unit)
                   VALUES (?, ?, ?, ?, ?)""",
                (rfq_id, item['name'], item.get('description', ''),
                 item.get('quantity', ''), item.get('unit', ''))
            )
        conn.commit()
        conn.close()
    
    def get_items(self, rfq_id: int) -> List[Dict]:
        """Get all items for an RFQ"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE rfq_id = ?", (rfq_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # VENDOR OPERATIONS
    # ========================================================================
    
    def add_vendors(self, rfq_id: int, vendors: List[Dict]):
        """Add multiple vendors to an RFQ"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sent_at = datetime.now().isoformat()
        for vendor in vendors:
            cursor.execute(
                """INSERT INTO vendors (rfq_id, name, email, sent_at)
                   VALUES (?, ?, ?, ?)""",
                (rfq_id, vendor['name'], vendor['email'], sent_at)
            )
        
        # Update total_vendors count in rfqs table
        cursor.execute(
            "UPDATE rfqs SET total_vendors = ? WHERE id = ?",
            (len(vendors), rfq_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_vendors(self, rfq_id: int) -> List[Dict]:
        """Get all vendors for an RFQ"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE rfq_id = ?", (rfq_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_vendor_responded(self, vendor_id: int):
        """Mark vendor as responded"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        responded_at = datetime.now().isoformat()
        cursor.execute(
            """UPDATE vendors 
               SET response_status = 'responded', responded_at = ? 
               WHERE id = ?""",
            (responded_at, vendor_id)
        )
        
        # Update responded_vendors count in rfqs table
        cursor.execute(
            """SELECT rfq_id FROM vendors WHERE id = ?""", (vendor_id,)
        )
        rfq_id = cursor.fetchone()[0]
        
        cursor.execute(
            """UPDATE rfqs 
               SET responded_vendors = (
                   SELECT COUNT(*) FROM vendors 
                   WHERE rfq_id = ? AND response_status = 'responded'
               )
               WHERE id = ?""",
            (rfq_id, rfq_id)
        )
        
        conn.commit()
        conn.close()
    

    
    def update_vendor_followup(self, vendor_id: int):
        """Update vendor follow-up tracking when reminder is sent"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute(
            """UPDATE vendors 
               SET followup_sent_count = followup_sent_count + 1,
                   last_followup_at = ?
               WHERE id = ?""",
            (now, vendor_id)
        )
        
        conn.commit()
        conn.close()
    # ========================================================================
    # RESPONSE OPERATIONS
    # ========================================================================
    
    def add_response(self, vendor_id: int, email_subject: str, 
                    email_body: str, parsed_json: str, 
                    is_quotation: bool, ai_provider: str) -> int:
        """Add a response from a vendor"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        received_at = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO responses 
               (vendor_id, email_subject, email_body, received_at, 
                parsed_json, is_quotation, ai_provider)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (vendor_id, email_subject, email_body, received_at, 
             parsed_json, 1 if is_quotation else 0, ai_provider)
        )
        response_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Mark vendor as responded
        self.mark_vendor_responded(vendor_id)
        
        return response_id
    
    def get_responses(self, rfq_id: int) -> List[Dict]:
        """Get all responses for an RFQ"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.*, v.name as vendor_name, v.email as vendor_email
               FROM responses r
               JOIN vendors v ON r.vendor_id = v.id
               WHERE v.rfq_id = ?
               ORDER BY r.received_at DESC""",
            (rfq_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    
    # ========================================================================
    # QUOTATION OPERATIONS
    # ========================================================================
    
    def add_quotation(self, response_id: int, item_name: str, 
                     price: str, unit: str = "", notes: str = "") -> int:
        """Add a quotation line item"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Convert price to float if possible
        try:
            price_float = float(price.replace(',', '').replace('₹', '').replace('$', '').strip())
        except:
            price_float = None
        
        cursor.execute(
            """INSERT INTO quotations 
               (response_id, item_name, price, unit, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (response_id, item_name, price_float, unit, notes)
        )
        quotation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return quotation_id
    
    def get_quotations(self, response_id: int) -> List[Dict]:
        """Get all quotation line items for a response"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM quotations WHERE response_id = ?", 
            (response_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_all_quotations_for_rfq(self, rfq_id: int) -> List[Dict]:
        """Get all quotations for an RFQ with vendor details"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT q.*, v.name as vendor_name, v.email as vendor_email,
                      r.received_at
               FROM quotations q
               JOIN responses r ON q.response_id = r.id
               JOIN vendors v ON r.vendor_id = v.id
               WHERE v.rfq_id = ?
               ORDER BY v.name, q.item_name""",
            (rfq_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Usage example
if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
