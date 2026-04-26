"""
qcf_generator.py
================
PURPOSE: Generate QCF (Quotation Comparison Format) Excel file
USED BY: app.py (after monitoring completes)
DEPENDS ON: pandas, openpyxl

This module creates a final Excel report comparing all vendor quotations.
"""

import pandas as pd  # For creating DataFrames and Excel files
from datetime import datetime  # For timestamping
import os  # For file operations
from typing import Dict, List  # For type hints


def generate_qcf_excel(responses: Dict, output_dir: str = "data/outputs") -> str:
    """
    Generate QCF Excel file from vendor responses.
    
    Creates an Excel file with columns:
    - Vendor Name
    - Vendor Email
    - Status (Replied, No Response, Quotation)
    - Item Count
    - Response Time
    - Items (detailed breakdown)
    - Notes
    
    Args:
        responses: Dictionary of vendor responses from SystemState
        output_dir: Directory to save the file
        
    Returns:
        Path to generated Excel file
    """
    
    # Step 1: Prepare data for DataFrame
    qcf_data = []
    
    for email, response in responses.items():
        # Basic information
        row = {
            "Vendor Name": response.get("name", "Unknown"),
            "Vendor Email": email,
            "Status": response.get("status", "Pending"),
            "Item Count": response.get("items", 0),
            "Response Time": "",
            "Items": "",
            "Notes": ""
        }
        
        # Format timestamp
        timestamp = response.get("timestamp")
        if timestamp:
            row["Response Time"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Extract items and notes from parsed data
        parsed_data = response.get("parsed_data")
        if parsed_data and parsed_data.get("is_quotation"):
            # Format items
            items_list = parsed_data.get("items", [])
            items_text = ""
            
            for item in items_list:
                item_name = item.get("item_name", "")
                price = item.get("price", "")
                delivery = item.get("delivery", "")
                
                items_text += f"{item_name}: {price}"
                if delivery:
                    items_text += f" (Delivery: {delivery})"
                items_text += "; "
            
            row["Items"] = items_text.rstrip("; ")
            row["Notes"] = parsed_data.get("notes", "")
        
        qcf_data.append(row)
    
    # Step 2: Create DataFrame
    df = pd.DataFrame(qcf_data)
    
    # Step 3: Sort by status (Quotation first, then Replied, then Pending)
    status_order = {"✅ Quotation": 0, "⚠️ Replied (No quotation)": 1, "Pending": 2}
    df["_sort_key"] = df["Status"].map(lambda x: status_order.get(x, 99))
    df = df.sort_values("_sort_key").drop("_sort_key", axis=1)
    
    # Step 4: Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"qcf_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 5: Write to Excel with formatting
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Quotation Comparison")
        
        # Get the worksheet
        worksheet = writer.sheets["Quotation Comparison"]
        
        # Adjust column widths
        for idx, col in enumerate(df.columns, 1):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(64 + idx)].width = min(max_length + 2, 50)
    
    print(f"\n[✓] QCF Excel generated: {filepath}")
    return filepath


def generate_detailed_qcf(responses: Dict, output_dir: str = "data/outputs") -> str:
    """
    Generate a detailed QCF with separate sheets for each vendor.
    
    Args:
        responses: Dictionary of vendor responses
        output_dir: Output directory
        
    Returns:
        Path to generated Excel file
    """
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"qcf_detailed_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        
        # Sheet 1: Summary
        summary_data = []
        for email, response in responses.items():
            summary_data.append({
                "Vendor Name": response.get("name", "Unknown"),
                "Email": email,
                "Status": response.get("status", "Pending"),
                "Items": response.get("items", 0),
                "Timestamp": response.get("timestamp", "").strftime("%Y-%m-%d %H:%M:%S") if response.get("timestamp") else ""
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
        
        # Sheet 2+: Individual vendor details
        for email, response in responses.items():
            parsed_data = response.get("parsed_data")
            
            if parsed_data and parsed_data.get("is_quotation"):
                vendor_name = response.get("name", "Unknown")[:25]  # Limit sheet name length
                
                items = parsed_data.get("items", [])
                if items:
                    df_vendor = pd.DataFrame(items)
                    df_vendor.to_excel(writer, index=False, sheet_name=vendor_name)
    
    print(f"[✓] Detailed QCF generated: {filepath}")
    return filepath


def create_comparison_report(responses: Dict) -> str:
    """
    Create a text summary of all responses.
    
    Args:
        responses: Dictionary of vendor responses
        
    Returns:
        Formatted text report
    """
    
    report = "\n" + "="*60 + "\n"
    report += "QUOTATION COMPARISON REPORT\n"
    report += "="*60 + "\n\n"
    
    # Summary statistics
    total = len(responses)
    quotations = sum(1 for r in responses.values() if r["status"] == "✅ Quotation")
    replied = sum(1 for r in responses.values() if r["status"] == "⚠️ Replied (No quotation)")
    pending = sum(1 for r in responses.values() if r["status"] == "Pending")
    
    report += f"Total Vendors: {total}\n"
    report += f"Quotations Received: {quotations}\n"
    report += f"Replies (No Quotation): {replied}\n"
    report += f"No Response: {pending}\n"
    report += "\n" + "-"*60 + "\n\n"
    
    # Detailed list
    for email, response in responses.items():
        report += f"Vendor: {response['name']}\n"
        report += f"Email: {email}\n"
        report += f"Status: {response['status']}\n"
        
        if response.get("timestamp"):
            report += f"Time: {response['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if response.get("parsed_data"):
            parsed = response["parsed_data"]
            if parsed.get("is_quotation"):
                report += f"Items: {len(parsed.get('items', []))}\n"
                
                for item in parsed.get("items", []):
                    report += f"  - {item.get('item_name')}: {item.get('price')}\n"
                
                if parsed.get("notes"):
                    report += f"Notes: {parsed['notes']}\n"
        
        report += "\n" + "-"*60 + "\n\n"
    
    return report
