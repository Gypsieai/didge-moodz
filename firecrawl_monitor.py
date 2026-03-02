"""
Firecrawl-based Trend Monitor for DIDGERI-BOOM
Provides TikTok trend data using Firecrawl's search and crawl capabilities.
"""

from typing import List, Dict, Any
from firecrawl import FirecrawlApp
from config import FIRECRAWL_API_KEY, NICHE_KEYWORDS
import json

class FirecrawlMonitor:
    """Uses Firecrawl to scrape trending TikTok data."""

    def __init__(self):
        self.app = FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None

    async def fetch_trending_sounds(self) -> List[Dict[str, Any]]:
        """Search for currently trending TikTok sounds."""
        if not self.app:
            return []

        try:
            # Search for trending sounds
            search_query = "trending tiktok sounds today"
            results = self.app.search(search_query, limit=5)
            
            sounds = []
            for result in results.get("data", []):
                # Process results into a standard format
                sounds.append({
                    "title": result.get("title", "Unknown Sound"),
                    "url": result.get("url", ""),
                    "snippet": result.get("description", ""),
                    "source": "firecrawl_search"
                })
            return sounds
        except Exception:
            return []

    async def fetch_trending_hashtags(self) -> List[Dict[str, Any]]:
        """Search for currently trending TikTok hashtags."""
        if not self.app:
            return []

        try:
            # Search for trending hashtags
            search_query = "trending tiktok hashtags today"
            results = self.app.search(search_query, limit=5)
            
            hashtags = []
            for result in results.get("data", []):
                hashtags.append({
                    "name": result.get("title", "").split()[0].replace("#", ""), # Naive extraction
                    "full_name": result.get("title", "unknown"),
                    "url": result.get("url", ""),
                    "source": "firecrawl_search"
                })
            return hashtags
        except Exception:
            return []

    def is_configured(self) -> bool:
        """Check if Firecrawl is ready to use."""
        return self.app is not None
