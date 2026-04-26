"""
excel_reader.py
===============
PURPOSE: Read vendor and RFQ data from Excel file
USED BY: app.py (main application)
DEPENDS ON: pandas, openpyxl

This module reads two sheets from an Excel file:
1. Vendors sheet: Contains vendor name and email
2. RFQ sheet: Contains items to be quoted
"""

import pandas as pd  # For reading Excel files
from typing import Tuple, List, Dict  # For type hints
import os  # For file operations


def read_excel_file(file_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Read vendors and RFQ data from Excel file.
    
    The Excel file must have two sheets:
    - Sheet 1 (Vendors): columns = [name, email]
    - Sheet 2 (RFQ): columns = [item_name, quantity, unit, description]
    
    Args:
        file_path: Path to the Excel file
        
    Returns:
        Tuple of (vendors_list, rfq_items_list)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required sheets or columns are missing
    """
    
    # Step 1: Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    try:
        # Step 2: Read all sheets from Excel
        # engine='openpyxl' is used for .xlsx files
        excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
        
        # Get list of sheet names
        sheet_names = list(excel_data.keys())
        
        if len(sheet_names) < 2:
            raise ValueError(f"Excel file must have at least 2 sheets. Found: {len(sheet_names)}")
        
        # Step 3: Read Vendors sheet (first sheet)
        vendors_sheet = excel_data[sheet_names[0]]
        
        # Check required columns
        required_vendor_cols = ['name', 'email']
        for col in required_vendor_cols:
            if col not in vendors_sheet.columns:
                raise ValueError(f"Vendors sheet missing column: {col}")
        
        # Convert to list of dictionaries
        # Each row becomes a dictionary: {name: "ABC Corp", email: "abc@vendor.com"}
        vendors = vendors_sheet[required_vendor_cols].to_dict('records')
        
        # Remove any rows with missing data
        vendors = [v for v in vendors if pd.notna(v['name']) and pd.notna(v['email'])]
        
        print(f"[INFO] Loaded {len(vendors)} vendors")
        
        # Step 4: Read RFQ sheet (second sheet)
        rfq_sheet = excel_data[sheet_names[1]]
        
        # Check required columns
        required_rfq_cols = ['item_name', 'quantity', 'unit', 'description']
        for col in required_rfq_cols:
            if col not in rfq_sheet.columns:
                raise ValueError(f"RFQ sheet missing column: {col}")
        
        # Convert to list of dictionaries
        rfq_items = rfq_sheet[required_rfq_cols].to_dict('records')
        
        # Remove any rows with missing item_name
        rfq_items = [item for item in rfq_items if pd.notna(item['item_name'])]
        
        # Fill NaN values with empty strings for other fields
        for item in rfq_items:
            for key in item:
                if pd.isna(item[key]):
                    item[key] = ""
        
        print(f"[INFO] Loaded {len(rfq_items)} RFQ items")
        
        return vendors, rfq_items
        
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")


def validate_excel_data(vendors: List[Dict], rfq_items: List[Dict]) -> bool:
    """
    Validate that the Excel data is properly formatted.
    
    Args:
        vendors: List of vendor dictionaries
        rfq_items: List of RFQ item dictionaries
        
    Returns:
        True if valid, raises ValueError if not
    """
    
    # Check vendors
    if not vendors:
        raise ValueError("No vendors found in Excel file")
    
    # Check for duplicate emails
    emails = [v['email'].lower() for v in vendors]
    if len(emails) != len(set(emails)):
        raise ValueError("Duplicate vendor emails found")
    
    # Check RFQ items
    if not rfq_items:
        raise ValueError("No RFQ items found in Excel file")
    
    print("[INFO] Excel data validation passed")
    return True
