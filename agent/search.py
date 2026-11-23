"""Search module for Composio Toolkit Research.

Provides cached search with graceful DuckDuckGo / direct fetching fallback
to protect Tavily API rate/usage limits.
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path("cache/searches")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_cache_path(query: str) -> Path:
    q_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{q_hash}.json"


def search_web(query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    """Search web with local disk caching and DDG fallback to preserve Tavily quota."""
    cache_path = _get_cache_path(query)
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached:
                    return cached
        except Exception:
            pass

    results = []

    # Quota Protection: Default to DuckDuckGo HTML / direct scraping to avoid burning Tavily credits
    try:
        import httpx
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            resp = client.get("https://html.duckduckgo.com/html/", params={"q": query})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.select(".result__a")
                snippets = soup.select(".result__snippet")
                for i, link in enumerate(links[:max_results]):
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    snippet = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                    # Filter internal duckduckgo redirect urls if present
                    if "duckduckgo.com/l/?uddg=" in href:
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "uddg" in parsed:
                            href = parsed["uddg"][0]
                    if href and href.startswith("http"):
                        results.append({
                            "title": title,
                            "url": href,
                            "content": snippet,
                            "score": 0.8,
                        })
    except Exception as e:
        print(f"[Search Fallback] DDG search exception for '{query}': {e}")

    # Save to disk cache
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    except Exception:
        pass

    return results
