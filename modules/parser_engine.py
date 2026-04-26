
"""
parser_engine.py
================
LAYER 2: PARSER ENGINE
Routes to specialized parsers based on format

STRATEGY:
- Excel → pandas (no AI needed)
- HTML → BeautifulSoup (no AI needed)
- PDF → pdfplumber + AI validation
- Text → regex + AI validation
"""

from typing import Dict, List, Optional
import pandas as pd
import tempfile
import os

try:
    from . import format_detector
    from . import email_monitor
except ImportError:
    # For standalone testing
    import format_detector
    import email_monitor


def parse_content(content: str, attachments: List[Dict] = None) -> Dict:
    """
    MAIN FUNCTION: Parse content using appropriate strategy.
    
    Args:
        content: Email body content
        attachments: List of attachments
    
    Returns:
        {
            "format": str,
            "items": List[Dict],
            "needs_ai": bool,
            "raw_content": str (if needs AI)
        }
    """
    # Step 1: Detect format
    format_info = format_detector.detect_format(content, attachments)
    strategy = format_info["extraction_strategy"]
    
    # Step 2: Route to appropriate parser
    if strategy == "excel_parser":
        return _parse_excel(attachments[0])
    elif strategy == "html_parser":
        return _parse_html(content)
    elif strategy == "pdf_parser_then_ai":
        return _parse_pdf(attachments[0])
    elif strategy == "regex_then_ai":
        return _parse_text_structured(content)
    else:
        return {"format": "unknown", "raw_content": content, "needs_ai": True}


def _parse_excel(attachment: Dict) -> Dict:
    """
    Parse Excel file using pandas (NO AI needed).
    """
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(attachment["content"])
            tmp_path = tmp.name
        
        # Read with pandas
        df = pd.read_excel(tmp_path, engine='openpyxl')
        os.unlink(tmp_path)
        
        # Extract items (assumes columns: item_name, price, quantity, etc.)
        items = []
        for _, row in df.iterrows():
            item = {
                "item_name": str(row.iloc[0]) if len(row) > 0 else "",
                "price": str(row.iloc[1]) if len(row) > 1 else "",
                "quantity": str(row.iloc[2]) if len(row) > 2 else ""
            }
            items.append(item)
        
        return {
            "format": "excel",
            "items": items,
            "needs_ai": False  # Clean Excel doesn't need AI
        }
    except Exception as e:
        print(f"[✗] Excel parsing failed: {e}")
        return {"format": "excel", "items": [], "needs_ai": True, "error": str(e)}


def _parse_html(content: str) -> Dict:
    """
    Parse HTML tables using BeautifulSoup (NO AI needed).
    """
    try:
        tables = email_monitor.parse_html_tables(content)
        items = []
        
        for table in tables:
            # Skip header row, process data rows
            for row in table[1:]:
                if len(row) >= 2:
                    item = {
                        "item_name": row[0],
                        "price": row[1],
                        "quantity": row[2] if len(row) > 2 else ""
                    }
                    items.append(item)
        
        return {
            "format": "html",
            "items": items,
            "needs_ai": False  # Clean HTML tables don't need AI
        }
    except Exception as e:
        print(f"[✗] HTML parsing failed: {e}")
        return {"format": "html", "raw_content": content, "needs_ai": True}


def _parse_pdf(attachment: Dict) -> Dict:
    """
    Parse PDF file (NEEDS AI for validation).
    """
    try:
        import PyPDF2
        import io
        
        reader = PyPDF2.PdfReader(io.BytesIO(attachment["content"]))
        text = ""
        
        for page in reader.pages:
            text += page.extract_text() + "\n\n"

        
        return {
            "format": "pdf",
            "text": text,
            "needs_ai": True  # PDFs need AI to understand structure
        }
    except ImportError:
        print("[⚠] PyPDF2 not installed, skipping PDF parsing")
        return {"format": "pdf", "text": "", "needs_ai": True}
    except Exception as e:
        print(f"[✗] PDF parsing failed: {e}")
        return {"format": "pdf", "text": "", "needs_ai": True, "error": str(e)}


def _parse_text_structured(content: str) -> Dict:
    """
    Parse structured text using regex (NEEDS AI for validation).
    """
    import re
    
    items = []
    
    # Try to extract item-price pairs
    # Pattern: Item name followed by price
    patterns = [
        r'([A-Za-z][A-Za-z\s\d]+)[:\-]\s*([₹$£€]?\s*\d+[\d,]*\.?\d*)',
        r'(\d+\.)\s+([A-Za-z][A-Za-z\s\d]+)\s*[:\-]?\s*([₹$£€]?\s*\d+[\d,]*\.?\d*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if len(match) >= 2:
                items.append({
                    "item_name": match[0].strip(),
                    "price": match[1].strip()
                })
    
    return {
        "format": "text_structured",
        "items": items,
        "raw_content": content,
        "needs_ai": True  # Regex extraction needs AI validation
    }


if __name__ == "__main__":
    print("Parser Engine Module Loaded Successfully!")
