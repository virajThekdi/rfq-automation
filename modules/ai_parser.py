"""
ai_parser.py
============
PURPOSE: Use Gemini AI to extract quotation data from email replies
USED BY: app.py (monitoring thread)
DEPENDS ON: google-generativeai

This module sends clean, preprocessed text to Gemini AI
and parses the AI's JSON response to extract quotation details.
"""

import google.generativeai as genai  # Gemini AI SDK
import json  # For parsing JSON responses
from typing import Dict, Optional  # For type hints


def initialize_gemini(api_key: str):
    """
    Initialize Gemini AI with API key.
    
    Args:
        api_key: Your Gemini API key
    """
    genai.configure(api_key=api_key)
    print("[INFO] Gemini AI initialized")


def create_ai_prompt(email_content: str) -> str:
    """
    Create the prompt for Gemini AI.
    
    The prompt must be clear and specific to get consistent JSON output.
    
    Args:
        email_content: Clean, preprocessed email text (with parsed tables)
        
    Returns:
        Complete prompt string
    """
    
    prompt = f"""Extract quotation details from the following email.

IMPORTANT INSTRUCTIONS:
- The email may contain tabular data that was converted from HTML tables
- Look for structured data in pipe-separated format (|)
- Understand rows as individual items with their prices and details
- Extract ALL items mentioned with prices
- Return ONLY valid JSON (no extra text, no markdown)

If the email contains a quotation with prices, return JSON in this format:
{{
    "is_quotation": true,
    "items": [
        {{
            "item_name": "name of item",
            "price": "price with currency",
            "unit": "unit of measurement",
            "delivery": "delivery time or date"
        }}
    ],
    "notes": "any additional notes or comments"
}}

If the email is just a reply without any quotation or prices, return:
{{
    "is_quotation": false
}}

EMAIL CONTENT:
{email_content}

Return ONLY the JSON object, nothing else."""

    return prompt


def parse_with_gemini(email_content: str, api_key: str) -> Optional[Dict]:
    """
    Send email content to Gemini AI and parse the response.
    
    This is the main AI parsing function.
    
    Args:
        email_content: Clean email text (preprocessed with tables)
        api_key: Gemini API key
        
    Returns:
        Parsed dictionary or None if parsing failed
    """
    
    try:
        # Step 1: Initialize model
        # Using Gemini Flash 1.5 as specified by user
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Step 2: Create prompt
        prompt = create_ai_prompt(email_content)
        
        # Step 3: Call AI
        print("[INFO] Calling Gemini AI...")
        response = model.generate_content(prompt)
        
        # Step 4: Extract text from response
        ai_text = response.text.strip()
        
        print(f"[DEBUG] AI Raw Response: {ai_text[:200]}...")  # Show first 200 chars
        
        # Step 5: Clean response (remove markdown code blocks if present)
        # Sometimes AI returns ```json ... ``` format
        if ai_text.startswith("```"):
            # Remove markdown code blocks
            ai_text = ai_text.strip("`")
            if ai_text.startswith("json"):
                ai_text = ai_text[4:].strip()
        
        # Step 6: Parse JSON
        parsed_data = json.loads(ai_text)
        
        print("[✓] AI parsing successful")
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"[✗] AI returned invalid JSON: {str(e)}")
        print(f"[DEBUG] AI Response: {ai_text}")
        return None
        
    except Exception as e:
        print(f"[✗] AI parsing error: {str(e)}")
        return None


def validate_quotation_data(parsed_data: Dict) -> bool:
    """
    Validate that the AI response has the correct structure.
    
    Args:
        parsed_data: Dictionary from AI
        
    Returns:
        True if valid, False otherwise
    """
    
    if not isinstance(parsed_data, dict):
        return False
    
    # Must have 'is_quotation' field
    if "is_quotation" not in parsed_data:
        return False
    
    # If it's a quotation, must have 'items'
    if parsed_data.get("is_quotation") == True:
        if "items" not in parsed_data:
            return False
        
        if not isinstance(parsed_data["items"], list):
            return False
        
        # Each item should have required fields
        for item in parsed_data["items"]:
            if not isinstance(item, dict):
                return False
    
    return True


def extract_quotation_summary(parsed_data: Dict) -> Dict:
    """
    Extract a summary from parsed quotation data.
    
    Args:
        parsed_data: Dictionary from AI
        
    Returns:
        Summary dictionary with key metrics
    """
    
    summary = {
        "is_quotation": parsed_data.get("is_quotation", False),
        "item_count": 0,
        "notes": parsed_data.get("notes", "")
    }
    
    if parsed_data.get("is_quotation"):
        items = parsed_data.get("items", [])
        summary["item_count"] = len(items)
    
    return summary


def parse_vendor_reply(email_content: str, api_key: str) -> tuple:
    """
    Complete pipeline to parse vendor reply.
    
    Args:
        email_content: Clean email text
        api_key: Gemini API key
        
    Returns:
        Tuple of (is_quotation: bool, item_count: int, parsed_data: dict)
    """
    
    # Parse with AI
    parsed_data = parse_with_gemini(email_content, api_key)
    
    if not parsed_data:
        # AI parsing failed
        return (False, 0, None)
    
    # Validate structure
    if not validate_quotation_data(parsed_data):
        print("[WARNING] AI returned invalid structure")
        return (False, 0, None)
    
    # Extract summary
    summary = extract_quotation_summary(parsed_data)
    
    return (
        summary["is_quotation"],
        summary["item_count"],
        parsed_data
    )
