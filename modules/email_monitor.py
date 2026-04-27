"""
email_monitor.py
================
PURPOSE: Monitor Gmail inbox for vendor replies
USED BY: app.py (main monitoring thread)
DEPENDS ON: imaplib, email (Python standard library), BeautifulSoup4

This module:
1. Connects to Gmail via IMAP
2. Searches for emails from vendors
3. Extracts HTML content
4. Parses HTML tables
5. Prepares clean text for AI parsing
"""

import imaplib  # For reading emails via IMAP
import email  # For parsing email messages
from email.header import decode_header  # For decoding email headers
from typing import List, Dict, Optional  # For type hints
from bs4 import BeautifulSoup  # For parsing HTML
import re  # For text cleaning


def connect_to_inbox(email_address: str, password: str) -> Optional[imaplib.IMAP4_SSL]:
    """
    Connect to Gmail inbox via IMAP.
    
    Args:
        email_address: Gmail address
        password: Gmail App Password
        
    Returns:
        IMAP connection object or None if failed
    """
    
    try:
        # Gmail IMAP settings
        imap_server = "imap.gmail.com"
        imap_port = 993  # SSL port
        
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        
        # Login
        mail.login(email_address, password)
        
        # Select inbox folder
        mail.select("INBOX")
        
        return mail
        
    except imaplib.IMAP4.error as e:
        print(f"[✗] IMAP authentication error: {str(e)}")
        return None
        
    except Exception as e:
        print(f"[✗] Error connecting to inbox: {str(e)}")
        return None


def extract_html_from_email(msg) -> str:
    """
    Extract HTML content from email message.
    
    Emails can have multiple parts (plain text, HTML, attachments).
    This function prioritizes HTML content.
    
    Args:
        msg: Email message object
        
    Returns:
        HTML content as string (or plain text if no HTML)
    """
    
    html_content = ""
    text_content = ""
    
    # Check if message has multiple parts
    if msg.is_multipart():
        # Iterate through email parts
        for part in msg.walk():
            content_type = part.get_content_type()
            
            try:
                # Get the content
                payload = part.get_payload(decode=True)
                
                if payload:
                    # Decode bytes to string
                    content = payload.decode('utf-8', errors='ignore')
                    
                    # Prioritize HTML content
                    if content_type == "text/html":
                        html_content = content
                    elif content_type == "text/plain" and not html_content:
                        text_content = content
                        
            except Exception as e:
                continue
    
    else:
        # Single part message
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                content = payload.decode('utf-8', errors='ignore')
                
                if msg.get_content_type() == "text/html":
                    html_content = content
                else:
                    text_content = content
                    
        except Exception as e:
            pass
    
    # Return HTML if available, otherwise plain text
    return html_content if html_content else text_content


def parse_html_tables(html_content: str) -> List[List[str]]:
    """
    Extract tables from HTML content using BeautifulSoup.
    
    This is CRITICAL for handling vendor quotations sent as HTML tables.
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        List of tables, where each table is a list of rows,
        and each row is a list of cell values
    """
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    
    extracted_tables = []
    
    for table in tables:
        table_data = []
        
        # Extract all rows
        rows = table.find_all('tr')
        
        for row in rows:
            # Extract cells (th or td)
            cells = row.find_all(['th', 'td'])
            
            # Get text from each cell
            row_data = [cell.get_text(strip=True) for cell in cells]
            
            # Only add non-empty rows
            if any(row_data):
                table_data.append(row_data)
        
        if table_data:
            extracted_tables.append(table_data)
    
    return extracted_tables


def convert_tables_to_text(tables: List[List[List[str]]]) -> str:
    """
    Convert parsed HTML tables to clean readable text.
    
    Format:
    Item | Price | Delivery
    Bolt | 10 | 2 days
    Nut  | 5  | 1 day
    
    Args:
        tables: List of parsed tables
        
    Returns:
        Formatted text representation
    """
    
    if not tables:
        return ""
    
    text_output = "\n\n=== TABLES FOUND IN EMAIL ===\n\n"
    
    for idx, table in enumerate(tables, 1):
        text_output += f"--- Table {idx} ---\n"
        
        for row in table:
            # Join cells with pipe separator
            text_output += " | ".join(row) + "\n"
        
        text_output += "\n"
    
    return text_output


def clean_html_to_text(html_content: str) -> str:
    """
    Convert HTML to clean text, preserving tables.
    
    This is the MAIN PREPROCESSING step before AI parsing.
    
    Steps:
    1. Extract HTML content
    2. Parse HTML tables
    3. Convert tables to text
    4. Extract plain text
    5. Combine everything
    
    Args:
        html_content: Raw HTML string
        
    Returns:
        Clean, readable text ready for AI parsing
    """
    
    # Step 1: Parse tables first
    tables = parse_html_tables(html_content)
    table_text = convert_tables_to_text(tables)
    
    # Step 2: Extract plain text from HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Step 3: Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    # Step 4: Combine table text with body text
    final_text = table_text + "\n\n=== EMAIL BODY ===\n\n" + text
    
    return final_text


def search_vendor_replies(mail: imaplib.IMAP4_SSL, vendor_emails: List[str],
                         original_subject: str, since_date: str = None) -> Dict[str, str]:
    """
    Search inbox AND sent folder for replies from specific vendors.
    
    IMPORTANT: Searches for emails with "Re:" in subject or replies TO the system email.
    This handles self-testing where both sender and receiver are the same email.
    
    Args:
        mail: IMAP connection object
        vendor_emails: List of vendor email addresses to check
        original_subject: Original RFQ subject (to match replies)
        since_date: Date to search from (format: "DD-MMM-YYYY", e.g., "01-Jan-2026")
        
    Returns:
        Dictionary mapping vendor email to their reply content
    """
    
    replies = {}
    
    # Define folders to search
    folders_to_search = ["INBOX", "[Gmail]/Sent Mail", "[Gmail]/Sent"]
    
    for vendor_email in vendor_emails:
        try:
            found_email = False
            
            # Search in multiple folders
            for folder in folders_to_search:
                if found_email:
                    break
                
                try:
                    # Select folder
                    mail.select(folder)
                    
                    # Strategy 1: Search for emails with "Re:" in subject from vendor
                    search_criteria = f'(SUBJECT "Re:" FROM "{vendor_email}")'
                    
                    # Add date filter if provided
                    if since_date:
                        search_criteria = f'(SINCE "{since_date}" SUBJECT "Re:" FROM "{vendor_email}")'
                    
                    # Search folder
                    status, message_ids = mail.search(None, search_criteria)
                    
                    if status != "OK":
                        continue
                    
                    # Get list of email IDs
                    email_ids = message_ids[0].split()
                    
                    if not email_ids:
                        # Strategy 2: If no "Re:" found, search for ANY email from vendor after RFQ
                        # and filter out the original RFQ by checking if it matches original subject
                        search_criteria = f'(FROM "{vendor_email}")'
                        if since_date:
                            search_criteria = f'(SINCE "{since_date}" FROM "{vendor_email}")'
                        
                        status, message_ids = mail.search(None, search_criteria)
                        if status == "OK":
                            email_ids = message_ids[0].split()
                    
                    if not email_ids:
                        continue  # No emails from this vendor in this folder
                    
                    # Check ALL emails from this vendor (not just the latest)
                    # to find ones that are replies (not the original RFQ)
                    for email_id in reversed(email_ids):  # Start with most recent
                        try:
                            # Fetch the email
                            status, msg_data = mail.fetch(email_id, "(RFC822)")
                            
                            if status != "OK":
                                continue
                            
                            # Parse email
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            
                            # Get subject
                            subject = msg.get("Subject", "")
                            
                            # Check if this is a REPLY (not the original RFQ)
                            # A reply should either:
                            # 1. Have "Re:" in subject, OR
                            # 2. Have different subject than original RFQ, OR
                            # 3. Be sent AFTER the RFQ (checked by examining all emails)
                            
                            is_reply = False
                            
                            # Check 1: Has "Re:" or "RE:" in subject
                            if "re:" in subject.lower():
                                is_reply = True
                                print(f"[DEBUG] Found email with 'Re:' in subject: {subject}")
                            
                            # Check 2: Subject is different from original RFQ subject
                            elif subject.strip() != original_subject.strip():
                                is_reply = True
                                print(f"[DEBUG] Found email with different subject: {subject}")
                            
                            # Check 3: If we have multiple emails, assume later ones are replies
                            elif len(email_ids) > 1 and email_id != email_ids[0]:
                                is_reply = True
                                print(f"[DEBUG] Found later email (not first one)")
                            
                            if is_reply:
                                # Extract HTML content
                                html_content = extract_html_from_email(msg)
                                
                                # Convert HTML to clean text (with tables parsed)
                                clean_text = clean_html_to_text(html_content)
                                
                                # Store the cleaned content
                                replies[vendor_email] = clean_text
                                found_email = True
                                
                                print(f"[✓] Found reply from {vendor_email} in {folder}")
                                print(f"[✓] Subject: {subject}")
                                break  # Found a reply, stop checking more emails
                            else:
                                print(f"[DEBUG] Skipping email (appears to be original RFQ): {subject}")
                        
                        except Exception as email_error:
                            print(f"[DEBUG] Error checking email {email_id}: {email_error}")
                            continue
                    
                except Exception as folder_error:
                    # Silently skip folders that don't exist or can't be accessed
                    continue
            
            if not found_email:
                print(f"[INFO] No reply found from {vendor_email} in any folder")
                
        except Exception as e:
            print(f"[✗] Error checking {vendor_email}: {str(e)}")
            continue
    
    return replies

def get_unread_count(mail: imaplib.IMAP4_SSL) -> int:
    """
    Get count of unread emails in inbox.
    
    Args:
        mail: IMAP connection object
        
    Returns:
        Number of unread emails
    """
    
    try:
        status, messages = mail.search(None, "UNSEEN")
        if status == "OK":
            return len(messages[0].split())
        return 0
    except:
        return 0


def check_new_responses(email_address: str, password: str, rfq_id: int, 
                       db_manager, ai_parser, gemini_api_key: str) -> Dict:
    """
    MAIN FUNCTION: Check inbox for vendor responses and process them.
    
    This is the COMPLETE INTEGRATION that ties everything together:
    1. Connect to inbox
    2. Get vendor list from database
    3. Search for replies from each vendor
    4. Parse content (Excel/HTML/Text/PDF)
    5. Use AI if needed
    6. Save to database
    7. Update vendor status
    
    Args:
        email_address: Gmail address to check
        password: Gmail App Password
        rfq_id: RFQ ID to check responses for
        db_manager: DatabaseManager instance
        ai_parser: AI Parser module
        gemini_api_key: Gemini API key for AI parsing
        
    Returns:
        Dictionary with results:
        {
            "success": bool,
            "new_responses": int,
            "processed": List[str],  # vendor emails
            "failed": List[str],     # vendor emails that failed
            "message": str
        }
    """
    
    results = {
        "success": False,
        "new_responses": 0,
        "processed": [],
        "failed": [],
        "message": ""
    }
    
    try:
        # Step 1: Get RFQ details
        print(f"\n[INFO] Checking responses for RFQ #{rfq_id}...")
        rfq = db_manager.get_rfq(rfq_id)
        
        if not rfq:
            results["message"] = f"RFQ #{rfq_id} not found"
            return results
        
        # Step 2: Get vendors who haven't responded yet
        vendors = db_manager.get_vendors(rfq_id)
        pending_vendors = [v for v in vendors if v['response_status'] == 'pending']
        
        if not pending_vendors:
            results["success"] = True
            results["message"] = "All vendors have already responded"
            return results
        
        print(f"[INFO] Found {len(pending_vendors)} pending vendors")
        
        # Step 3: Connect to inbox
        print("[INFO] Connecting to Gmail inbox...")
        mail = connect_to_inbox(email_address, password)
        
        if not mail:
            results["message"] = "Failed to connect to inbox"
            return results
        
        print("[✓] Connected to inbox")
        
        # Step 4: Search for replies from each pending vendor
        vendor_emails = [v['email'] for v in pending_vendors]
        
        # Get creation date for filtering (format: DD-MMM-YYYY)
        from datetime import datetime
        created_date = datetime.fromisoformat(rfq['created_at'])
        since_date = created_date.strftime("%d-%b-%Y")
        
        print(f"[INFO] Searching for emails since {since_date}...")
        replies = search_vendor_replies(mail, vendor_emails, 
                                       rfq['subject'], since_date)
        
        mail.logout()
        
        if not replies:
            results["success"] = True
            results["message"] = "No new responses found"
            return results
        
        print(f"[✓] Found {len(replies)} new response(s)")
        
        # Step 5: Process each response
        for vendor_email, email_content in replies.items():
            try:
                print(f"\n[INFO] Processing response from {vendor_email}...")
                
                # Find vendor in database
                vendor = next((v for v in pending_vendors if v['email'] == vendor_email), None)
                
                if not vendor:
                    print(f"[WARNING] Vendor {vendor_email} not found in database")
                    results["failed"].append(vendor_email)
                    continue
                
                # Step 6: Parse the content
                # Check if AI parsing is needed
                needs_ai = True
                parsed_data = None
                
                # Try structured parsing first (HTML tables, Excel, etc.)
                from . import format_detector, parser_engine
                
                # Detect format (Note: attachments not yet implemented)
                format_info = format_detector.detect_format(email_content, attachments=None)
                print(f"[INFO] Detected format: {format_info['format']}")
                
                # If HTML with tables, try parsing without AI
                if "table" in email_content.lower() or "<tr>" in email_content.lower():
                    print("[INFO] HTML table detected, parsing without AI...")
                    try:
                        parsed_result = parser_engine._parse_html(email_content)
                        if parsed_result.get("items") and not parsed_result.get("needs_ai", True):
                            parsed_data = {
                                "is_quotation": True,
                                "items": parsed_result["items"]
                            }
                            needs_ai = False
                            print("[✓] Parsed HTML table successfully (no AI needed)")
                    except Exception as e:
                        print(f"[WARNING] HTML parsing failed: {e}, will use AI")
                
                # Step 7: Use AI if needed
                if needs_ai:
                    print("[INFO] Using Gemini AI for parsing...")
                    is_quotation, item_count, parsed_data = ai_parser.parse_vendor_reply(
                        email_content, gemini_api_key
                    )
                    
                    if not parsed_data:
                        print("[WARNING] AI parsing failed")
                        # Still save the response as non-quotation
                        parsed_data = {"is_quotation": False}
                
                # Step 8: Save to database
                print("[INFO] Saving response to database...")
                
                # Convert parsed data to JSON string
                import json
                parsed_json = json.dumps(parsed_data, ensure_ascii=False)
                
                # Add response
                response_id = db_manager.add_response(
                    vendor_id=vendor['id'],
                    email_subject=f"Re: {rfq['subject']}",
                    email_body=email_content,
                    parsed_json=parsed_json,
                    is_quotation=parsed_data.get("is_quotation", False),
                    ai_provider="gemini" if needs_ai else "structured_parser"
                )
                
                # If it's a quotation, save line items
                if parsed_data.get("is_quotation") and parsed_data.get("items"):
                    print(f"[INFO] Saving {len(parsed_data['items'])} quotation items...")
                    
                    for item in parsed_data["items"]:
                        db_manager.add_quotation(
                            response_id=response_id,
                            item_name=item.get("item_name", item.get("name", "Unknown")),
                            price=str(item.get("price", "")),
                            unit=item.get("unit", ""),
                            notes=item.get("notes", "")
                        )
                    
                    print("[✓] Quotation items saved")
                
                # Step 9: Update vendor status
                db_manager.update_vendor_status(vendor['id'], 'responded')
                print(f"[✓] Vendor {vendor_email} status updated to 'responded'")
                
                results["processed"].append(vendor_email)
                results["new_responses"] += 1
                
            except Exception as e:
                print(f"[✗] Error processing {vendor_email}: {str(e)}")
                results["failed"].append(vendor_email)
                continue
        
        # Final results
        results["success"] = True
        if results["new_responses"] > 0:
            results["message"] = f"Successfully processed {results['new_responses']} response(s)"
        else:
            results["message"] = "No new responses found"
        
        return results
        
    except Exception as e:
        print(f"[✗] FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        results["message"] = f"Error: {str(e)}"
        return results
