
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
import re

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


def _detect_column_mapping(header_row: List[str]) -> Dict[str, int]:
    """
    Intelligently detect which columns contain item name, price, quantity, etc.
    
    Args:
        header_row: List of column headers
        
    Returns:
        Dictionary mapping field names to column indices
    """
    mapping = {
        "item_name": None,
        "price": None,
        "quantity": None,
        "unit": None,
        "description": None
    }
    
    # Normalize headers to lowercase for matching
    headers_lower = [h.lower().strip() for h in header_row]
    
    for idx, header in enumerate(headers_lower):
        # Item name detection
        if mapping["item_name"] is None:
            if any(keyword in header for keyword in ["item", "product", "material", "part"]):
                # Avoid "unit" which also contains "item"
                if "unit" not in header:
                    mapping["item_name"] = idx
        
        # Price detection (prioritize "unit price" over "total")
        if any(keyword in header for keyword in ["unit price", "rate", "unit cost"]):
            mapping["price"] = idx
        elif mapping["price"] is None and any(keyword in header for keyword in ["price", "cost", "inr", "rs", "₹"]):
            # Only use generic "price" if we haven't found "unit price"
            if "total" not in header:
                mapping["price"] = idx
        
        # Quantity detection
        if mapping["quantity"] is None:
            if any(keyword in header for keyword in ["quantity", "qty", "amount", "no."]):
                mapping["quantity"] = idx
        
        # Unit detection
        if mapping["unit"] is None:
            if "unit" in header and "price" not in header:
                mapping["unit"] = idx
        
        # Description detection
        if mapping["description"] is None:
            if any(keyword in header for keyword in ["description", "spec", "detail"]):
                mapping["description"] = idx
    
    # Fallback: If no price column found, look for numeric values with currency
    if mapping["price"] is None:
        for idx, header in enumerate(headers_lower):
            if re.search(r'(inr|rs|₹|\$|price)', header):
                mapping["price"] = idx
                break
    
    print(f"[DEBUG] Detected column mapping: {mapping}")
    return mapping


def _parse_html(content: str) -> Dict:
    """
    Parse HTML tables using BeautifulSoup with INTELLIGENT column detection.
    
    Now detects which columns contain item name, price, quantity, etc.
    by analyzing the header row.
    """
    try:
        tables = email_monitor.parse_html_tables(content)
        items = []
        
        print(f"[DEBUG] Found {len(tables)} HTML table(s)")
        
        for table_idx, table in enumerate(tables):
            if len(table) < 2:
                print(f"[DEBUG] Table {table_idx + 1} has no data rows, skipping")
                continue
            
            # First row is header
            header_row = table[0]
            print(f"[DEBUG] Table {table_idx + 1} headers: {header_row}")
            
            # Detect column mapping
            mapping = _detect_column_mapping(header_row)
            
            # Check if we found essential columns
            if mapping["item_name"] is None:
                print(f"[WARNING] Could not detect item name column in table {table_idx + 1}")
                continue
            
            if mapping["price"] is None:
                print(f"[WARNING] Could not detect price column in table {table_idx + 1}")
                # Don't skip - we'll try to extract it anyway
            
            # Process data rows
            for row_idx, row in enumerate(table[1:], start=1):
                if not row or len(row) == 0:
                    continue
                
                # Extract values based on detected mapping
                item = {}
                
                # Item name (required)
                if mapping["item_name"] is not None and mapping["item_name"] < len(row):
                    item["item_name"] = row[mapping["item_name"]].strip()
                else:
                    item["item_name"] = ""
                
                # Price
                if mapping["price"] is not None and mapping["price"] < len(row):
                    item["price"] = row[mapping["price"]].strip()
                else:
                    # Fallback: search for first numeric value
                    for cell in row:
                        if re.search(r'[\d,]+\.?\d*', cell):
                            item["price"] = cell.strip()
                            break
                    if "price" not in item:
                        item["price"] = ""
                
                # Quantity
                if mapping["quantity"] is not None and mapping["quantity"] < len(row):
                    item["quantity"] = row[mapping["quantity"]].strip()
                else:
                    item["quantity"] = ""
                
                # Unit
                if mapping["unit"] is not None and mapping["unit"] < len(row):
                    item["unit"] = row[mapping["unit"]].strip()
                else:
                    item["unit"] = ""
                
                # Description
                if mapping["description"] is not None and mapping["description"] < len(row):
                    item["notes"] = row[mapping["description"]].strip()
                else:
                    item["notes"] = ""
                
                # Only add if we have at least item name
                if item.get("item_name"):
                    items.append(item)
                    print(f"[DEBUG] Extracted item: {item['item_name']} - {item.get('price', 'N/A')}")
        
        if items:
            print(f"[✓] Successfully parsed {len(items)} items from HTML table(s)")
            return {
                "format": "html",
                "items": items,
                "needs_ai": False  # Clean HTML tables don't need AI
            }
        else:
            print(f"[WARNING] No items extracted from HTML tables")
            return {
                "format": "html",
                "raw_content": content,
                "needs_ai": True
            }
            
    except Exception as e:
        print(f"[✗] HTML parsing failed: {e}")
        import traceback
        traceback.print_exc()
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
