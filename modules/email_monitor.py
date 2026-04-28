"""
email_monitor.py
================
PURPOSE: Monitor email inbox for vendor replies
USED BY: app.py (main monitoring thread)
DEPENDS ON: imaplib, email (Python standard library), BeautifulSoup4

SUPPORTS: Gmail, Outlook, Yahoo, and any IMAP-enabled email provider

This module:
1. Connects to any IMAP server via configurable settings
2. Searches for emails from vendors
3. Extracts HTML content
4. Parses HTML tables
5. Extracts attachments (Excel, PDF, etc.)
6. Prepares clean text for AI parsing
"""

import imaplib  # For reading emails via IMAP
import email  # For parsing email messages
from email.header import decode_header  # For decoding email headers
from typing import List, Dict, Optional, Tuple  # For type hints
from bs4 import BeautifulSoup  # For parsing HTML
import re  # For text cleaning
from difflib import SequenceMatcher  # For fuzzy string matching
import os  # For environment variables


# Email provider configurations
EMAIL_PROVIDERS = {
    "gmail": {
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "name": "Gmail"
    },
    "outlook": {
        "imap_server": "outlook.office365.com",
        "imap_port": 993,
        "name": "Outlook/Office 365"
    },
    "hotmail": {
        "imap_server": "imap-mail.outlook.com",
        "imap_port": 993,
        "name": "Hotmail"
    },
    "yahoo": {
        "imap_server": "imap.mail.yahoo.com",
        "imap_port": 993,
        "name": "Yahoo Mail"
    },
    "custom": {
        "imap_server": None,  # Set via environment variable
        "imap_port": 993,
        "name": "Custom IMAP Server"
    }
}


def get_imap_settings() -> Dict[str, any]:
    """
    Get IMAP settings from environment variables or use defaults.
    
    Environment Variables:
        EMAIL_PROVIDER: gmail, outlook, hotmail, yahoo, or custom
        IMAP_SERVER: Custom IMAP server (if EMAIL_PROVIDER=custom)
        IMAP_PORT: Custom IMAP port (default: 993)
    
    Returns:
        Dictionary with imap_server, imap_port, provider_name
    """
    # Get provider from environment (default: gmail)
    provider = os.getenv('EMAIL_PROVIDER', 'gmail').lower()
    
    if provider in EMAIL_PROVIDERS:
        config = EMAIL_PROVIDERS[provider].copy()
        
        # For custom provider, check environment variables
        if provider == "custom":
            config["imap_server"] = os.getenv('IMAP_SERVER')
            config["imap_port"] = int(os.getenv('IMAP_PORT', '993'))
            
            if not config["imap_server"]:
                raise ValueError(
                    "EMAIL_PROVIDER is set to 'custom' but IMAP_SERVER is not configured. "
                    "Please set IMAP_SERVER environment variable."
                )
        else:
            # Allow override even for known providers
            if os.getenv('IMAP_SERVER'):
                config["imap_server"] = os.getenv('IMAP_SERVER')
            if os.getenv('IMAP_PORT'):
                config["imap_port"] = int(os.getenv('IMAP_PORT'))
        
        return config
    else:
        raise ValueError(
            f"Unknown EMAIL_PROVIDER: {provider}. "
            f"Supported: {', '.join(EMAIL_PROVIDERS.keys())}"
        )


def connect_to_inbox(email_address: str, password: str) -> Optional[imaplib.IMAP4_SSL]:
    """
    Connect to email inbox via IMAP (supports Gmail, Outlook, Yahoo, etc.).
    
    Args:
        email_address: Email address
        password: Email password or App Password
        
    Returns:
        IMAP connection object or None if failed
    """
    
    try:
        # Get IMAP settings (configurable via environment)
        imap_config = get_imap_settings()
        imap_server = imap_config["imap_server"]
        imap_port = imap_config["imap_port"]
        provider_name = imap_config["name"]
        
        print(f"[INFO] Connecting to {provider_name} ({imap_server}:{imap_port})...")
        
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        
        # Login
        mail.login(email_address, password)
        
        # Select inbox folder
        mail.select("INBOX")
        
        print(f"[✓] Connected to {provider_name} inbox successfully")
        
        return mail
        
    except imaplib.IMAP4.error as e:
        print(f"[✗] IMAP authentication error: {str(e)}")
        print(f"[HINT] For Outlook/Hotmail, ensure IMAP is enabled in account settings")
        print(f"[HINT] For Gmail, use App Passwords (not your regular password)")
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
            content_disposition = part.get_content_disposition()
            
            # Skip attachments (we handle them separately)
            if content_disposition == "attachment":
                continue
            
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


def extract_attachments_from_email(msg) -> List[Dict]:
    """
    Extract attachments from email message.
    
    CRITICAL for handling Excel quotations, PDFs, and other file attachments.
    
    Args:
        msg: Email message object
        
    Returns:
        List of attachment dictionaries:
        [
            {
                "filename": "quotation.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "content": b'<binary data>',
                "size": 12345
            }
        ]
    """
    
    attachments = []
    
    if not msg.is_multipart():
        return attachments
    
    print(f"[DEBUG] Checking email for attachments...")
    
    for part in msg.walk():
        # Get content disposition (attachment vs inline)
        content_disposition = part.get_content_disposition()
        
        # Check if this is an attachment
        if content_disposition == "attachment":
            try:
                # Get filename (may be encoded)
                filename = part.get_filename()
                
                if filename:
                    # Decode filename if needed
                    decoded_filename = decode_header(filename)
                    if decoded_filename and decoded_filename[0][1]:
                        filename = decoded_filename[0][0].decode(decoded_filename[0][1])
                    elif isinstance(decoded_filename[0][0], bytes):
                        filename = decoded_filename[0][0].decode('utf-8', errors='ignore')
                    else:
                        filename = decoded_filename[0][0]
                
                # Get content type
                content_type = part.get_content_type()
                
                # Get binary content
                content = part.get_payload(decode=True)
                
                if content:
                    attachment_info = {
                        "filename": filename or "unnamed_attachment",
                        "content_type": content_type,
                        "content": content,
                        "size": len(content)
                    }
                    
                    attachments.append(attachment_info)
                    
                    print(f"[DEBUG]   ✓ Found attachment: {filename} ({content_type}, {len(content)} bytes)")
                    
            except Exception as e:
                print(f"[WARNING] Error extracting attachment: {e}")
                continue
    
    if attachments:
        print(f"[✓] Extracted {len(attachments)} attachment(s)")
    else:
        print(f"[DEBUG] No attachments found in email")
    
    return attachments


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


def fuzzy_match_subject(subject: str, original_subject: str, threshold: float = 0.6) -> float:
    """
    Calculate fuzzy similarity between two subjects.
    
    Uses SequenceMatcher to handle typos, extra text, and partial matches.
    
    Args:
        subject: Email subject to check
        original_subject: Original RFQ subject
        threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    
    # Normalize both subjects
    s1 = subject.lower().strip()
    s2 = original_subject.lower().strip()
    
    # Remove common reply prefixes
    for prefix in ["re:", "fwd:", "fw:", "reply:", "response:"]:
        if s1.startswith(prefix):
            s1 = s1[len(prefix):].strip()
    
    # Calculate similarity
    similarity = SequenceMatcher(None, s1, s2).ratio()
    
    return similarity


def is_reply_to_rfq(msg, original_subject: str, rfq_message_id: str = None) -> tuple:
    """
    Check if an email is a reply to the RFQ using MULTIPLE methods.
    
    Checks (in order of reliability):
    1. Email thread headers (In-Reply-To, References)
    2. Exact "Re: [subject]" match
    3. Fuzzy subject matching (partial/similar)
    4. Keyword-based matching
    
    Args:
        msg: Email message object
        original_subject: Original RFQ subject
        rfq_message_id: Message-ID of original RFQ (if available)
        
    Returns:
        Tuple of (is_reply: bool, confidence: str, match_reason: str)
    """
    
    subject = msg.get("Subject", "").strip()
    in_reply_to = msg.get("In-Reply-To", "").strip()
    references = msg.get("References", "").strip()
    
    print(f"[DEBUG] Checking if email is a reply...")
    print(f"[DEBUG]   Subject: '{subject}'")
    print(f"[DEBUG]   In-Reply-To: '{in_reply_to}'")
    print(f"[DEBUG]   References: '{references}'")
    
    # METHOD 1: Check email thread headers (MOST RELIABLE)
    if rfq_message_id:
        print(f"[DEBUG]   Checking thread headers against RFQ Message-ID: '{rfq_message_id}'")
        
        if in_reply_to and rfq_message_id in in_reply_to:
            print(f"[DEBUG]   ✓✓✓ MATCH via In-Reply-To header (HIGH CONFIDENCE)")
            return (True, "high", "Thread header match (In-Reply-To)")
        
        if references and rfq_message_id in references:
            print(f"[DEBUG]   ✓✓✓ MATCH via References header (HIGH CONFIDENCE)")
            return (True, "high", "Thread header match (References)")
    
    # METHOD 2: Exact "Re: [subject]" match
    normalized_subject = subject.lower().strip()
    
    if normalized_subject.startswith("re:"):
        subject_after_re = subject[3:].strip()
        
        if subject_after_re.lower() == original_subject.lower():
            print(f"[DEBUG]   ✓✓ MATCH via exact 'Re: [subject]' (MEDIUM CONFIDENCE)")
            return (True, "medium", "Exact Re: subject match")
    
    # METHOD 3: Fuzzy subject matching
    similarity = fuzzy_match_subject(subject, original_subject)
    print(f"[DEBUG]   Subject similarity score: {similarity:.2f}")
    
    if similarity >= 0.8:
        print(f"[DEBUG]   ✓ MATCH via high fuzzy similarity (MEDIUM CONFIDENCE)")
        return (True, "medium", f"Fuzzy match (similarity: {similarity:.2f})")
    
    if similarity >= 0.6:
        print(f"[DEBUG]   ✓ MATCH via moderate fuzzy similarity (LOW CONFIDENCE)")
        return (True, "low", f"Partial match (similarity: {similarity:.2f})")
    
    # METHOD 4: Keyword-based matching (LAST RESORT)
    # Check if subject contains key words from original
    original_keywords = set(original_subject.lower().split())
    subject_keywords = set(subject.lower().split())
    
    # Remove common words
    common_words = {"re", "fwd", "fw", "reply", "response", "the", "a", "an", "for", "to", "from"}
    original_keywords -= common_words
    subject_keywords -= common_words
    
    if original_keywords and subject_keywords:
        keyword_overlap = len(original_keywords & subject_keywords) / len(original_keywords)
        
        if keyword_overlap >= 0.6:
            print(f"[DEBUG]   ✓ MATCH via keyword overlap (LOW CONFIDENCE)")
            return (True, "low", f"Keyword overlap ({keyword_overlap:.2f})")
    
    print(f"[DEBUG]   ✗ No match found")
    return (False, "none", "No match")


def search_vendor_replies(mail: imaplib.IMAP4_SSL, vendor_emails: List[str],
                         original_subject: str, since_date: str = None, 
                         rfq_message_id: str = None) -> Dict[str, Tuple[str, List[Dict]]]:
    """
    Search inbox for REPLY emails from vendors using FLEXIBLE matching.
    
    IMPROVED APPROACH:
    1. Gets ALL emails from each vendor (with date filter)
    2. Uses multiple matching methods:
       - Email thread headers (In-Reply-To, References)
       - Exact "Re: [subject]" match
       - Fuzzy subject similarity
       - Keyword overlap
    3. Extracts BOTH email body AND attachments
    
    Args:
        mail: IMAP connection object
        vendor_emails: List of vendor email addresses to check
        original_subject: Original RFQ subject (WITHOUT "Re:")
        since_date: Date to search from (format: "DD-MMM-YYYY")
        rfq_message_id: Message-ID of original RFQ email (optional, for thread matching)
        
    Returns:
        Dictionary mapping vendor email to (content, attachments) tuple:
        {
            "vendor@email.com": (
                "email body text",
                [{"filename": "quote.xlsx", "content": b'...', ...}]
            )
        }
    """
    
    replies = {}
    
    print(f"\n[DEBUG] ===== EMAIL SEARCH STARTING =====")
    print(f"[DEBUG] Looking for replies to: '{original_subject}'")
    print(f"[DEBUG] RFQ Message-ID: '{rfq_message_id or 'Not available'}'")
    print(f"[DEBUG] Searching for emails since: {since_date}")
    print(f"[DEBUG] Vendor emails to check: {vendor_emails}")
    
    # Define folders to search (INBOX contains incoming emails)
    folders_to_search = ["INBOX"]
    
    for vendor_email in vendor_emails:
        try:
            print(f"\n[DEBUG] ----- Checking vendor: {vendor_email} -----")
            found_email = False
            
            # Search in each folder
            for folder in folders_to_search:
                if found_email:
                    break
                
                try:
                    # Select folder
                    status, msg_data = mail.select(folder)
                    if status != "OK":
                        print(f"[DEBUG] Cannot access folder: {folder}")
                        continue
                    
                    print(f"[DEBUG] Searching in folder: {folder}")
                    
                    # Get ALL emails from vendor with date filter
                    if since_date:
                        search_criteria = f'(SINCE "{since_date}" FROM "{vendor_email}")'
                    else:
                        search_criteria = f'(FROM "{vendor_email}")'
                    
                    print(f"[DEBUG] IMAP search: {search_criteria}")
                    
                    # Execute search
                    status, message_ids = mail.search(None, search_criteria)
                    
                    if status != "OK":
                        print(f"[DEBUG] Search failed in {folder}")
                        continue
                    
                    # Get email IDs
                    email_ids = message_ids[0].split()
                    
                    print(f"[DEBUG] Found {len(email_ids)} total emails from vendor in {folder}")
                    
                    if not email_ids:
                        print(f"[DEBUG] No emails from {vendor_email} found in {folder}")
                        continue
                    
                    # Track best match (in case multiple emails match)
                    best_match = None
                    best_confidence = "none"
                    
                    # Check each email to find replies
                    for email_id in reversed(email_ids):  # Start with most recent
                        try:
                            print(f"\n[DEBUG] --- Fetching email ID: {email_id.decode()} ---")
                            
                            # Fetch email
                            status, msg_data = mail.fetch(email_id, "(RFC822)")
                            
                            if status != "OK":
                                print(f"[DEBUG] Failed to fetch email {email_id}")
                                continue
                            
                            # Parse email
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            
                            # Extract metadata
                            subject = msg.get("Subject", "")
                            from_addr = msg.get("From", "")
                            to_addr = msg.get("To", "")
                            date_str = msg.get("Date", "")
                            
                            # Print email details
                            print(f"[DEBUG] Email Details:")
                            print(f"[DEBUG]   Subject: '{subject}'")
                            print(f"[DEBUG]   From: {from_addr}")
                            print(f"[DEBUG]   To: {to_addr}")
                            print(f"[DEBUG]   Date: {date_str}")
                            
                            # FLEXIBLE MATCHING: Check if this is a reply
                            is_reply, confidence, match_reason = is_reply_to_rfq(
                                msg, original_subject, rfq_message_id
                            )
                            
                            print(f"[DEBUG]   Match result: is_reply={is_reply}, confidence={confidence}")
                            print(f"[DEBUG]   Match reason: {match_reason}")
                            
                            # If it's a high confidence match, process immediately
                            if is_reply and confidence == "high":
                                print(f"[DEBUG] >>> HIGH CONFIDENCE REPLY FOUND! Processing...")
                                
                                # Extract content AND attachments
                                html_content = extract_html_from_email(msg)
                                clean_text = clean_html_to_text(html_content)
                                attachments = extract_attachments_from_email(msg)
                                
                                # Store result (tuple of content and attachments)
                                replies[vendor_email] = (clean_text, attachments)
                                found_email = True
                                
                                print(f"[✓✓✓] Successfully found reply from {vendor_email}")
                                print(f"[✓✓✓] Reply subject: '{subject}'")
                                print(f"[✓✓✓] Match reason: {match_reason}")
                                print(f"[✓✓✓] Content length: {len(clean_text)} characters")
                                print(f"[✓✓✓] Attachments: {len(attachments)}")
                                break
                            
                            # For medium/low confidence, track the best match
                            elif is_reply:
                                confidence_rank = {"high": 3, "medium": 2, "low": 1, "none": 0}
                                
                                if confidence_rank[confidence] > confidence_rank[best_confidence]:
                                    best_confidence = confidence
                                    best_match = {
                                        "msg": msg,
                                        "subject": subject,
                                        "match_reason": match_reason
                                    }
                                    print(f"[DEBUG]   >>> Saved as best match so far")
                        
                        except Exception as email_error:
                            print(f"[✗] Error processing email {email_id}: {email_error}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    # If no high-confidence match but we have a medium/low match, use it
                    if not found_email and best_match and best_confidence in ["medium", "low"]:
                        print(f"\n[DEBUG] >>> Using best match with {best_confidence} confidence")
                        
                        msg = best_match["msg"]
                        html_content = extract_html_from_email(msg)
                        clean_text = clean_html_to_text(html_content)
                        attachments = extract_attachments_from_email(msg)
                        
                        # Store result (tuple of content and attachments)
                        replies[vendor_email] = (clean_text, attachments)
                        found_email = True
                        
                        print(f"[✓✓] Found reply from {vendor_email} ({best_confidence} confidence)")
                        print(f"[✓✓] Reply subject: '{best_match['subject']}'")
                        print(f"[✓✓] Match reason: {best_match['match_reason']}")
                        print(f"[✓✓] Content length: {len(clean_text)} characters")
                        print(f"[✓✓] Attachments: {len(attachments)}")
                    
                except Exception as folder_error:
                    print(f"[✗] Error accessing folder {folder}: {folder_error}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not found_email:
                print(f"\n[INFO] >>> No reply found from {vendor_email} in any folder")
                
        except Exception as vendor_error:
            print(f"[✗] Error checking vendor {vendor_email}: {vendor_error}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n[DEBUG] ===== EMAIL SEARCH COMPLETE =====")
    print(f"[DEBUG] Total replies found: {len(replies)}")
    if replies:
        print(f"[DEBUG] Vendors who replied: {list(replies.keys())}")
    
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
    1. Connect to inbox (Gmail, Outlook, Yahoo, etc.)
    2. Get vendor list from database
    3. Search for replies from each vendor
    4. Extract email body AND attachments (Excel/PDF/etc.)
    5. Parse content using appropriate strategy
    6. Use AI if needed
    7. Save to database
    8. Update vendor status
    
    Args:
        email_address: Email address to check
        password: Email password or App Password
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
        
        print(f"[INFO] RFQ Subject: '{rfq['subject']}'")
        
        # Step 2: Get vendors who haven't responded yet
        vendors = db_manager.get_vendors(rfq_id)
        pending_vendors = [v for v in vendors if v['response_status'] == 'pending']
        
        if not pending_vendors:
            results["success"] = True
            results["message"] = "All vendors have already responded"
            return results
        
        print(f"[INFO] Found {len(pending_vendors)} pending vendors")
        for v in pending_vendors:
            print(f"[INFO]   - {v['email']}")
        
        # Step 3: Connect to inbox
        print("[INFO] Connecting to email inbox...")
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
        
        # Get RFQ message ID if available (for thread matching)
        rfq_message_id = rfq.get('message_id', None)
        
        replies = search_vendor_replies(mail, vendor_emails, 
                                       rfq['subject'], since_date, rfq_message_id)
        
        mail.logout()
        
        if not replies:
            results["success"] = True
            results["message"] = "No new responses found"
            return results
        
        print(f"[✓] Found {len(replies)} new response(s)")
        
        # Step 5: Process each response
        for vendor_email, (email_content, attachments) in replies.items():
            try:
                print(f"\n[INFO] Processing response from {vendor_email}...")
                print(f"[INFO] Email has {len(attachments)} attachment(s)")
                
                # Find vendor in database
                vendor = next((v for v in pending_vendors if v['email'] == vendor_email), None)
                
                if not vendor:
                    print(f"[WARNING] Vendor {vendor_email} not found in database")
                    results["failed"].append(vendor_email)
                    continue
                
                # Step 6: Parse the content using format detection
                needs_ai = True
                parsed_data = None
                
                # Import parsing modules
                from . import format_detector, parser_engine
                
                # Detect format (NOW WITH ATTACHMENTS!)
                format_info = format_detector.detect_format(email_content, attachments=attachments)
                print(f"[INFO] Detected format: {format_info['primary_format']}")
                print(f"[INFO] Extraction strategy: {format_info['extraction_strategy']}")
                print(f"[INFO] Confidence: {format_info['confidence']:.0%}")
                
                # Route to appropriate parser
                try:
                    parsed_result = parser_engine.parse_content(email_content, attachments)
                    
                    # Check if we got structured data without AI
                    if parsed_result.get("items") and not parsed_result.get("needs_ai", True):
                        parsed_data = {
                            "is_quotation": True,
                            "items": parsed_result["items"]
                        }
                        needs_ai = False
                        print(f"[✓] Parsed {format_info['primary_format']} successfully (no AI needed)")
                        print(f"[✓] Extracted {len(parsed_result['items'])} items")
                    else:
                        # Parser says we need AI
                        needs_ai = True
                        print(f"[INFO] Parser requires AI validation")
                        
                except Exception as e:
                    print(f"[WARNING] Structured parsing failed: {e}, will use AI")
                    needs_ai = True
                
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
                import traceback
                traceback.print_exc()
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
