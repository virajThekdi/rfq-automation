"""
email_generator.py
==================
PURPOSE: Generate HTML email content from RFQ data
USED BY: app.py, email_sender.py
DEPENDS ON: None (uses only Python standard library)

This module converts RFQ items into a nicely formatted HTML table
that can be sent via email.
"""

from typing import List, Dict  # For type hints


def generate_html_table(rfq_items: List[Dict]) -> str:
    """
    Convert RFQ items into an HTML table.
    
    Takes a list of RFQ items and creates a professional-looking
    HTML table that vendors can easily read.
    
    Args:
        rfq_items: List of dictionaries with keys: item_name (or name), quantity, unit, description
        
    Returns:
        HTML string containing the formatted table
    """
    
    # Start building HTML with inline CSS for better email compatibility
    html = """
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
        <thead>
            <tr style="background-color: #4CAF50; color: white;">
                <th style="text-align: left;">Item Name</th>
                <th style="text-align: left;">Quantity</th>
                <th style="text-align: left;">Unit</th>
                <th style="text-align: left;">Description</th>
            </tr>
        </thead>
        <tbody>
    """
    
    # Add a row for each RFQ item
    for idx, item in enumerate(rfq_items):
        # Alternate row colors for better readability
        bg_color = "#f2f2f2" if idx % 2 == 0 else "#ffffff"
        
        # Handle both 'item_name' and 'name' keys
        item_name = item.get('item_name', item.get('name', ''))
        
        html += f"""
            <tr style="background-color: {bg_color};">
                <td>{item_name}</td>
                <td>{item.get('quantity', '')}</td>
                <td>{item.get('unit', '')}</td>
                <td>{item.get('description', '')}</td>
            </tr>
        """
    
    # Close the table
    html += """
        </tbody>
    </table>
    """
    
    return html


def generate_email_body(subject: str, body_text: str, rfq_items: List[Dict], 
                       footer: str) -> str:
    """
    Generate complete HTML email body with RFQ table.
    
    Creates a full HTML email with:
    - Custom greeting/body text
    - HTML table of RFQ items
    - Footer text
    
    Args:
        subject: Email subject (for reference)
        body_text: Custom message before the table
        rfq_items: List of RFQ items
        footer: Footer message
        
    Returns:
        Complete HTML email body
    """
    
    # Generate the RFQ table
    table_html = generate_html_table(rfq_items)
    
    # Combine into full email body
    full_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            
            <!-- Custom body text -->
            <p>{body_text}</p>
            
            <br>
            
            <!-- RFQ Table -->
            {table_html}
            
            <br>
            
            <!-- Footer -->
            <p style="color: #666;">{footer}</p>
            
            <br>
            
            <!-- System signature -->
            <p style="font-size: 12px; color: #999; border-top: 1px solid #ddd; padding-top: 10px;">
                This is an automated RFQ (Request for Quotation) email. Please reply with your quotation.
            </p>
            
        </div>
    </body>
    </html>
    """
    
    return full_html


def generate_rfq_email(vendor_name: str, subject: str, body: str, 
                       items: List[Dict], footer: str) -> str:
    """
    Generate personalized RFQ email for a vendor.
    
    Args:
        vendor_name: Name of the vendor
        subject: Email subject
        body: Email body text
        items: List of RFQ items
        footer: Email footer
        
    Returns:
        Complete HTML email body
    """
    
    # Personalize body with vendor name
    personalized_body = f"Dear {vendor_name},\n\n{body}"
    
    return generate_email_body(subject, personalized_body, items, footer)


def generate_followup_body(original_subject: str, body_text: str, 
                          rfq_items: List[Dict], footer: str, 
                          followup_number: int) -> str:
    """
    Generate follow-up email body.
    
    Similar to the original email but with a follow-up message.
    
    Args:
        original_subject: Original email subject
        body_text: Original body text
        rfq_items: List of RFQ items
        footer: Footer text
        followup_number: Which follow-up this is (1, 2, etc.)
        
    Returns:
        HTML email body for follow-up
    """
    
    # Generate the RFQ table
    table_html = generate_html_table(rfq_items)
    
    # Create follow-up message
    followup_msg = f"<p><strong>FOLLOW-UP #{followup_number}</strong>: This is a reminder regarding our RFQ request.</p>"
    
    # Combine into full email body
    full_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            
            <!-- Follow-up notice -->
            {followup_msg}
            
            <!-- Original body text -->
            <p>{body_text}</p>
            
            <br>
            
            <!-- RFQ Table -->
            {table_html}
            
            <br>
            
            <!-- Footer -->
            <p style="color: #666;">{footer}</p>
            
            <br>
            
            <!-- System signature -->
            <p style="font-size: 12px; color: #999; border-top: 1px solid #ddd; padding-top: 10px;">
                This is an automated follow-up email. Please reply with your quotation if you haven't already.
            </p>
            
        </div>
    </body>
    </html>
    """
    
    return full_html
