"""Fetch and web page caching module.

Fetches web pages, extracts textual documentation, and caches content by SHA256(URL).
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

CACHE_DIR = Path("cache/pages")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()


def get_cache_path(url: str) -> Path:
    return CACHE_DIR / f"{get_url_hash(url)}.json"


def clean_html(html_content: str) -> str:
    """Extract clean readable text from HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script, style, meta, nav, footer, header
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()
    
    # Get text
    text = soup.get_text(separator="\n")
    # Clean excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def fetch_page(url: str, timeout: float = 15.0) -> Dict[str, Any]:
    """Fetch a web page with disk caching."""
    if not url or url == "unknown" or not url.startswith("http"):
        return {"url": url, "status_code": 0, "text": "", "error": "Invalid URL"}

    cache_file = get_cache_path(url)
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    result = {
        "url": url,
        "status_code": 0,
        "text": "",
        "error": None,
    }

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            result["status_code"] = resp.status_code
            if resp.status_code == 200:
                result["text"] = clean_html(resp.text)
                # Keep text bounded to ~25,000 chars to avoid blowing up context
                if len(result["text"]) > 35000:
                    result["text"] = result["text"][:35000]
            else:
                result["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        result["error"] = str(e)

    # Cache successful or failed attempt
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass

    return result


def is_quote_in_cache(url: str, quote: str) -> bool:
    """Verify whether a quote appears in the cached page content (fuzzy / case-insensitive)."""
    if not url or url == "unknown" or not quote or quote == "unknown":
        return False
    cache_file = get_cache_path(url)
    if not cache_file.exists():
        return False
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("text", "").lower()
        q_norm = quote.strip().lower()
        # Direct substring match
        if q_norm in text:
            return True
        # Match significant token subset (for slight spacing/punctuation differences)
        tokens = [t for t in q_norm.split() if len(t) > 3]
        if len(tokens) >= 3:
            matched = sum(1 for t in tokens if t in text)
            if matched / len(tokens) >= 0.8:
                return True
        return False
    except Exception:
        return False
