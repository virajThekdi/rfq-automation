
"""
multi_ai_engine.py
==================
LAYER 3: MULTI-AI ENGINE
Provides AI fallback support across multiple providers

PROVIDERS:
1. Gemini (primary - already working)
2. OpenAI GPT-4 (fallback 1)
3. Grok (fallback 2)

STRATEGY:
Try providers in order until one succeeds
"""

import os
from typing import Dict, List, Optional

try:
    from . import ai_parser
except ImportError:
    import ai_parser


def detect_intent_multi(content: str, providers: List[str] = None) -> Dict:
    """
    Try multiple AI providers with automatic fallback.
    
    Args:
        content: Email content to analyze
        providers: List of provider names ["gemini", "openai", "grok"]
                   Default: ["gemini", "openai"]
    
    Returns:
        {
            "is_quotation": bool,
            "items": List[Dict],
            "notes": str,
            "provider_used": str
        }
    """
    if providers is None:
        providers = ["gemini", "openai"]  # Default: Gemini first, OpenAI fallback
    
    for provider in providers:
        try:
            print(f"[INFO] Trying {provider.upper()}...")
            
            if provider == "gemini":
                result = _try_gemini(content)
            elif provider == "openai":
                result = _try_openai(content)
            elif provider == "grok":
                result = _try_grok(content)
            else:
                print(f"[⚠] Unknown provider: {provider}")
                continue
            
            # Add provider info to result
            result["provider_used"] = provider
            print(f"[✓] {provider.upper()} succeeded!")
            return result
            
        except Exception as e:
            print(f"[⚠] {provider.upper()} failed: {str(e)}")
            continue
    
    # All providers failed
    print("[✗] All AI providers failed!")
    return {
        "is_quotation": False,
        "items": [],
        "notes": "All AI providers failed",
        "provider_used": "none"
    }


def _try_gemini(content: str) -> Dict:
    """
    Use Gemini AI (already implemented in ai_parser.py).
    """
    return ai_parser.parse_vendor_reply(content)


def _try_openai(content: str) -> Dict:
    """
    Use OpenAI GPT-4.
    """
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in environment")
        
        openai.api_key = api_key
        
        # Create prompt
        prompt = f"""
Analyze this email and determine if it contains a quotation with prices.

Email content:
{content[:3000]}

Respond ONLY with valid JSON in this exact format:
{{
    "is_quotation": true/false,
    "items": [
        {{"item_name": "item1", "price": "₹100", "delivery": "5 days"}},
        {{"item_name": "item2", "price": "₹200", "delivery": "7 days"}}
    ],
    "notes": "any additional notes"
}}
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        # Parse response
        import json
        result = json.loads(response.choices[0].message.content)
        return result
        
    except ImportError:
        raise Exception("openai package not installed. Run: pip install openai")
    except Exception as e:
        raise Exception(f"OpenAI error: {str(e)}")


def _try_grok(content: str) -> Dict:
    """
    Use Grok AI.
    """
    try:
        import requests
        import json
        
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            raise Exception("GROK_API_KEY not found in environment")
        
        # Grok uses OpenAI-compatible API
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
Analyze this email and determine if it contains a quotation with prices.

Email content:
{content[:3000]}

Respond ONLY with valid JSON in this exact format:
{{
    "is_quotation": true/false,
    "items": [
        {{"item_name": "item1", "price": "₹100", "delivery": "5 days"}}
    ],
    "notes": "any additional notes"
}}
"""
        
        payload = {
            "model": "grok-2-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = json.loads(response.json()["choices"][0]["message"]["content"])
        return result
        
    except Exception as e:
        raise Exception(f"Grok error: {str(e)}")


if __name__ == "__main__":
    print("Multi-AI Engine Module Loaded Successfully!")
