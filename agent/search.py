"""Search module for Composio Toolkit Research.

Provides cached search via Tavily API with graceful fallback.
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


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Search web using Tavily with local disk caching."""
    cache_path = _get_cache_path(query)
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    tavily_key = os.getenv("TAVILY_API_KEY")
    results = []

    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
                include_raw_content=False,
            )
            raw_results = response.get("results", [])
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                })
        except Exception as e:
            print(f"[Warning] Tavily search failed for '{query}': {e}")

    # Fallback to duckduckgo via httpx if no results
    if not results:
        try:
            import httpx
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = httpx.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.select(".result__a")
                snippets = soup.select(".result__snippet")
                for i, link in enumerate(links[:max_results]):
                    href = link.get("href", "")
                    title = link.get_text(strip=True)
                    snippet = snippets[i].get_text(strip=True) if i < len(snippets) else ""
                    if href:
                        results.append({
                            "title": title,
                            "url": href,
                            "content": snippet,
                            "score": 0.5,
                        })
        except Exception as e:
            print(f"[Warning] Fallback search failed for '{query}': {e}")

    # Save to cache
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    except Exception:
        pass

    return results
