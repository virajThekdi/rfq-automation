
"""
format_detector.py
==================
LAYER 1: FORMAT DETECTION
Detects content type BEFORE sending to parsers or AI

PHILOSOPHY:
- Parsing format = CODE's job
- Understanding meaning = AI's job

PRIORITY ORDER:
1. Excel attachments (95% confidence) - BEST case
2. HTML tables (90% confidence) - GOOD case  
3. Plain text with structure (75% confidence) - MEDIUM case
4. PDF attachments (70% confidence) - NEEDS AI help
5. Unstructured text (40% confidence) - AI FALLBACK
"""

from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re


class ContentFormat:
    """Enum-like class for content formats"""
    HTML_TABLE = "html_table"
    EXCEL = "excel"
    PDF = "pdf"
    PLAIN_TEXT_STRUCTURED = "plain_text_structured"  # Has prices/items
    PLAIN_TEXT_UNSTRUCTURED = "plain_text_unstructured"  # No clear structure
    UNKNOWN = "unknown"


def detect_format(content: str, attachments: List[Dict] = None) -> Dict:
    """
    MAIN FUNCTION: Detect content format.
    
    Args:
        content: Email body content (HTML or text)
        attachments: List of attachment dicts with 'filename' and 'content_type'
    
    Returns:
        {
            "primary_format": ContentFormat,
            "has_html": bool,
            "has_tables": bool,
            "has_attachments": bool,
            "attachment_types": [],
            "confidence": float,
            "extraction_strategy": str
        }
    """
    result = {
        "primary_format": ContentFormat.UNKNOWN,
        "has_html": False,
        "has_tables": False,
        "has_attachments": False,
        "attachment_types": [],
        "confidence": 0.0,
        "extraction_strategy": "ai_fallback"
    }
    
    # Check attachments FIRST (highest priority)
    if attachments and len(attachments) > 0:
        result["has_attachments"] = True
        
        for att in attachments:
            filename = att.get("filename", "").lower()
            content_type = att.get("content_type", "").lower()
            
            # Excel files (BEST case - structured data)
            if "excel" in content_type or filename.endswith(('.xlsx', '.xls', '.xlsm')):
                result["attachment_types"].append("excel")
                result["primary_format"] = ContentFormat.EXCEL
                result["confidence"] = 0.95
                result["extraction_strategy"] = "excel_parser"
                return result  # PRIORITY: Excel is most reliable
            
            # PDF files (needs special handling)
            elif "pdf" in content_type or filename.endswith('.pdf'):
                result["attachment_types"].append("pdf")
                result["primary_format"] = ContentFormat.PDF
                result["confidence"] = 0.70
                result["extraction_strategy"] = "pdf_parser_then_ai"
                return result
    
    # Check HTML content
    if _is_html(content):
        result["has_html"] = True
        
        # Check for HTML tables (GOOD case)
        if _has_html_tables(content):
            result["has_tables"] = True
            result["primary_format"] = ContentFormat.HTML_TABLE
            result["confidence"] = 0.90
            result["extraction_strategy"] = "html_parser"
            return result
    
    # Check plain text structure
    text_structure = _analyze_text_structure(content)
    
    if text_structure["has_prices"] and text_structure["has_items"]:
        result["primary_format"] = ContentFormat.PLAIN_TEXT_STRUCTURED
        result["confidence"] = 0.75
        result["extraction_strategy"] = "regex_then_ai"
        return result
    
    # Unstructured text (AI fallback)
    result["primary_format"] = ContentFormat.PLAIN_TEXT_UNSTRUCTURED
    result["confidence"] = 0.40
    result["extraction_strategy"] = "ai_only"
    
    return result


def _is_html(content: str) -> bool:
    """Check if content is HTML."""
    html_tags = ['<html', '<body', '<div', '<table', '<tr', '<td', '<p>']
    return any(tag in content.lower() for tag in html_tags)


def _has_html_tables(content: str) -> bool:
    """Check if HTML contains tables with meaningful content."""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) >= 2:  # At least header + 1 data row
                return True
        
        return False
    except:
        return False


def _analyze_text_structure(content: str) -> Dict:
    """
    Analyze plain text for structure.
    
    Returns:
        {
            "has_prices": bool,
            "has_items": bool,
            "has_currency": bool,
            "price_count": int,
            "table_like": bool
        }
    """
    result = {
        "has_prices": False,
        "has_items": False,
        "has_currency": False,
        "price_count": 0,
        "table_like": False
    }
    
    # Currency patterns
    currency_symbols = ['₹', 'Rs', 'Rs.', '$', 'USD', 'EUR', '£', 'INR']
    result["has_currency"] = any(sym in content for sym in currency_symbols)
    
    # Price patterns (number + currency or currency + number)
    price_patterns = [
        r'₹\s*\d+[\d,]*\.?\d*',  # ₹65 or ₹1,200.50
        r'Rs\.?\s*\d+[\d,]*\.?\d*',  # Rs 450 or Rs. 450
        r'\$\s*\d+[\d,]*\.?\d*',  # $100 or $1,000.50
        r'\d+[\d,]*\.?\d*\s*(?:₹|Rs|USD|INR)',  # 450 Rs or 100 USD
    ]
    
    price_matches = []
    for pattern in price_patterns:
        matches = re.findall(pattern, content)
        price_matches.extend(matches)
    
    result["price_count"] = len(price_matches)
    result["has_prices"] = result["price_count"] > 0
    
    # Item patterns (words followed by colon or dash, then price)
    item_patterns = [
        r'[A-Za-z][A-Za-z\s\d]+[:\-]\s*[₹$Rs]',  # Item: ₹ or Item - $
        r'^\s*\d+\.\s+[A-Za-z]',  # 1. Item or 2. Item (numbered list)
        r'^\s*[•\-\*]\s+[A-Za-z]',  # • Item or - Item or * Item
    ]
    
    item_count = 0
    for pattern in item_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        item_count += len(matches)
    
    result["has_items"] = item_count > 0
    
    # Table-like structure (has | or consistent spacing)
    has_pipes = content.count('|') > 3
    lines = content.split('\n')
    consistent_spacing = sum(1 for line in lines if len(line.split()) >= 3) > 2
    
    result["table_like"] = has_pipes or consistent_spacing
    
    return result


def should_use_ai(extraction_strategy: str) -> bool:
    """
    Determine if AI should be used for this content.
    
    RULE:
    - Clean Excel/HTML tables: NO AI (waste of API call)
    - Messy PDF/text: YES AI (validation needed)
    """
    no_ai_strategies = ["excel_parser", "html_parser"]
    return extraction_strategy not in no_ai_strategies


if __name__ == "__main__":
    # Self-test
    print("Format Detector Module Loaded Successfully!")
