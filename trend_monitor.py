"""
DIDGERI-BOOM Trend Monitor Engine
Monitors TikTok trends and recommends content ideas for Warren's didgeridoo niche.
"""

import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import httpx

from firecrawl_monitor import FirecrawlMonitor
from config import (
    APIFY_API_TOKEN, APIFY_TRENDING_SOUNDS_ACTOR,
    APIFY_TRENDING_HASHTAGS_ACTOR, FIRECRAWL_API_KEY,
    NICHE_KEYWORDS, DATA_DIR, TIMEZONE
)


class TrendMonitor:
    """Monitors TikTok trends and generates niche-specific recommendations."""

    def __init__(self):
        self.trends_file = DATA_DIR / "trends.json"
        self.recommendations_file = DATA_DIR / "recommendations.json"
        self._cached_trends = None
        self._cache_time = None
        self._cache_ttl = 3600  # 1 hour cache
        self.firecrawl = FirecrawlMonitor()

    # ── Public API ───────────────────────────────────────────────

    async def fetch_trending_sounds(self) -> list[dict]:
        """Fetch currently trending sounds from TikTok."""
        all_sounds = []
        
        # Try Apify
        if APIFY_API_TOKEN:
            all_sounds.extend(await self._fetch_apify_sounds())
        
        # Try Firecrawl
        if self.firecrawl.is_configured():
            fc_sounds = await self.firecrawl.fetch_trending_sounds()
            all_sounds.extend(fc_sounds)
            
        if not all_sounds:
            return self._get_demo_sounds()
            
        return all_sounds

    async def fetch_trending_hashtags(self) -> list[dict]:
        """Fetch currently trending hashtags from TikTok."""
        all_hashtags = []
        
        # Try Apify
        if APIFY_API_TOKEN:
            all_hashtags.extend(await self._fetch_apify_hashtags())
            
        # Try Firecrawl
        if self.firecrawl.is_configured():
            fc_hashtags = await self.firecrawl.fetch_trending_hashtags()
            all_hashtags.extend(fc_hashtags)
            
        if not all_hashtags:
            return self._get_demo_hashtags()
            
        return all_hashtags

    async def get_all_trends(self) -> dict:
        """Get all trends with niche relevance scoring."""
        if self._cached_trends and self._cache_time:
            elapsed = (datetime.now() - self._cache_time).total_seconds()
            if elapsed < self._cache_ttl:
                return self._cached_trends

        sounds = await self.fetch_trending_sounds()
        hashtags = await self.fetch_trending_hashtags()

        # Score each trend for niche relevance
        scored_sounds = [self._score_trend(s, "sound") for s in sounds]
        scored_hashtags = [self._score_trend(h, "hashtag") for h in hashtags]

        # Sort by composite score (virality × relevance)
        scored_sounds.sort(key=lambda x: x["composite_score"], reverse=True)
        scored_hashtags.sort(key=lambda x: x["composite_score"], reverse=True)

        trends = {
            "sounds": scored_sounds[:20],
            "hashtags": scored_hashtags[:30],
            "fetched_at": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(scored_sounds, scored_hashtags),
        }

        # Cache and persist
        self._cached_trends = trends
        self._cache_time = datetime.now()
        self._save_trends(trends)

        return trends

    def get_content_ideas(self, count: int = 5) -> list[dict]:
        """Generate content ideas based on current trends."""
        templates = [
            {
                "type": "cover",
                "title": "🎵 Didgeridoo Cover of '{sound}'",
                "description": "Play a trending song/sound on the didgeridoo. "
                               "These often go viral because of the unexpected instrument twist.",
                "difficulty": "medium",
                "viral_potential": "very high",
            },
            {
                "type": "reaction",
                "title": "😱 Reacting to '{sound}' with Didgeridoo",
                "description": "Play along with a trending video using a duet format. "
                               "The contrast between modern trends and ancient instrument = gold.",
                "difficulty": "easy",
                "viral_potential": "high",
            },
            {
                "type": "tutorial",
                "title": "🎓 How to Play Didgeridoo: {hashtag} Edition",
                "description": "Short tutorial clips showing technique. "
                               "Educational content performs well on TikTok algorithm.",
                "difficulty": "easy",
                "viral_potential": "medium",
            },
            {
                "type": "mashup",
                "title": "🔥 Didgeridoo × {sound} Mashup",
                "description": "Blend the didgeridoo drone with trending sounds. "
                               "Unexpected mashups get massive shares.",
                "difficulty": "hard",
                "viral_potential": "very high",
            },
            {
                "type": "asmr",
                "title": "😴 ASMR Didgeridoo Session",
                "description": "Close-up recording with deep drone sounds. "
                               "ASMR is consistently trending and the didgeridoo is perfect for it.",
                "difficulty": "easy",
                "viral_potential": "high",
            },
            {
                "type": "challenge",
                "title": "🏆 Didgeridoo Challenge: Can I Play '{sound}'?",
                "description": "Attempt trending challenges with a didgeridoo twist. "
                               "The challenge format drives engagement through comments.",
                "difficulty": "medium",
                "viral_potential": "very high",
            },
            {
                "type": "street_performance",
                "title": "🎶 Street Busking: People's Reactions!",
                "description": "Film public reactions to live didgeridoo performances. "
                               "Reaction content is consistently viral material.",
                "difficulty": "easy",
                "viral_potential": "very high",
            },
        ]

        selected = random.sample(templates, min(count, len(templates)))
        return selected

    # ── Apify Integration ────────────────────────────────────────

    async def _fetch_apify_sounds(self) -> list[dict]:
        """Fetch trending sounds via Apify scraper."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Start the Apify actor run
                run_url = (
                    f"https://api.apify.com/v2/acts/{APIFY_TRENDING_SOUNDS_ACTOR}"
                    f"/runs?token={APIFY_API_TOKEN}"
                )
                run_resp = await client.post(run_url, json={"maxItems": 50})
                run_data = run_resp.json()
                run_id = run_data.get("data", {}).get("id")

                if not run_id:
                    return self._get_demo_sounds()

                # Poll for completion
                for _ in range(30):
                    status_url = (
                        f"https://api.apify.com/v2/actor-runs/{run_id}"
                        f"?token={APIFY_API_TOKEN}"
                    )
                    status_resp = await client.get(status_url)
                    status = status_resp.json().get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        break
                    await _async_sleep(2)

                # Fetch results
                dataset_id = run_data.get("data", {}).get("defaultDatasetId")
                items_url = (
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                    f"?token={APIFY_API_TOKEN}"
                )
                items_resp = await client.get(items_url)
                return items_resp.json()

        except Exception:
            return self._get_demo_sounds()

    async def _fetch_apify_hashtags(self) -> list[dict]:
        """Fetch trending hashtags via Apify scraper."""
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                run_url = (
                    f"https://api.apify.com/v2/acts/{APIFY_TRENDING_HASHTAGS_ACTOR}"
                    f"/runs?token={APIFY_API_TOKEN}"
                )
                run_resp = await client.post(run_url, json={"maxItems": 50})
                run_data = run_resp.json()
                run_id = run_data.get("data", {}).get("id")

                if not run_id:
                    return self._get_demo_hashtags()

                for _ in range(30):
                    status_url = (
                        f"https://api.apify.com/v2/actor-runs/{run_id}"
                        f"?token={APIFY_API_TOKEN}"
                    )
                    status_resp = await client.get(status_url)
                    status = status_resp.json().get("data", {}).get("status")
                    if status == "SUCCEEDED":
                        break
                    await _async_sleep(2)

                dataset_id = run_data.get("data", {}).get("defaultDatasetId")
                items_url = (
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                    f"?token={APIFY_API_TOKEN}"
                )
                items_resp = await client.get(items_url)
                return items_resp.json()

        except Exception:
            return self._get_demo_hashtags()

    # ── Scoring Engine ───────────────────────────────────────────

    def _score_trend(self, trend: dict, trend_type: str) -> dict:
        """Score a trend for niche relevance and viral potential."""
        name = (
            trend.get("title", "") or trend.get("name", "") or
            trend.get("hashtagName", "") or ""
        ).lower()

        # Niche relevance (0-100)
        niche_score = 0
        matched_keywords = []
        for kw in NICHE_KEYWORDS:
            if kw in name:
                niche_score += 30
                matched_keywords.append(kw)

        # Music-related boost
        music_keywords = ["music", "song", "beat", "sound", "remix", "cover", "instrument"]
        for kw in music_keywords:
            if kw in name:
                niche_score += 15
                matched_keywords.append(kw)

        niche_score = min(niche_score, 100)

        # Virality score from view count / usage count
        views = trend.get("views", 0) or trend.get("videoCount", 0) or 0
        virality_score = min(100, int((views / 1_000_000) * 10)) if views else 50

        # Composite: even non-niche trends are useful (didgeridoo covers of ANY sound)
        # Higher weight to virality since Warren can adapt any trend to didgeridoo
        composite = (virality_score * 0.7) + (niche_score * 0.3)

        trend["niche_score"] = niche_score
        trend["virality_score"] = virality_score
        trend["composite_score"] = round(composite, 1)
        trend["matched_keywords"] = matched_keywords
        trend["trend_type"] = trend_type
        trend["didgeridoo_angle"] = self._suggest_angle(name, trend_type)

        return trend

    def _suggest_angle(self, name: str, trend_type: str) -> str:
        """Suggest how Warren can use this trend with his didgeridoo."""
        if trend_type == "sound":
            angles = [
                f"Play '{name}' on the didgeridoo — the contrast will blow minds",
                f"Duet with the original '{name}' using didgeridoo accompaniment",
                f"Create a didgeridoo remix of '{name}' — drone bass version",
                f"React to '{name}' then transition into a didgeridoo cover",
            ]
        else:
            angles = [
                f"Create a didgeridoo video tagged with #{name}",
                f"Show your didgeridoo skills using the #{name} trend format",
                f"Hop on #{name} with an unexpected didgeridoo twist",
            ]
        return random.choice(angles)

    def _generate_recommendations(
        self, sounds: list[dict], hashtags: list[dict]
    ) -> list[dict]:
        """Generate actionable content recommendations."""
        recommendations = []

        # Top 3 sound-based recommendations
        for sound in sounds[:3]:
            rec = {
                "type": "sound_cover",
                "priority": "high",
                "trend": sound.get("title", "Unknown"),
                "action": sound.get("didgeridoo_angle", ""),
                "hashtags": [
                    h.get("hashtagName", h.get("name", ""))
                    for h in hashtags[:5]
                ],
                "estimated_reach": sound.get("virality_score", 50) * 1000,
            }
            recommendations.append(rec)

        # Top 2 hashtag-based recommendations
        for hashtag in hashtags[:2]:
            tag_name = hashtag.get("hashtagName", hashtag.get("name", ""))
            rec = {
                "type": "hashtag_ride",
                "priority": "medium",
                "trend": f"#{tag_name}",
                "action": f"Create a didgeridoo clip for #{tag_name}",
                "estimated_reach": hashtag.get("virality_score", 50) * 500,
            }
            recommendations.append(rec)

        return recommendations

    # ── Demo Data (when no API keys configured) ──────────────────

    def _get_demo_sounds(self) -> list[dict]:
        """Return demo trending sounds for development/testing."""
        return [
            {"title": "Original Sound - EDM Remix", "views": 15_000_000, "rank": 1},
            {"title": "Lofi Beats to Chill To", "views": 8_500_000, "rank": 2},
            {"title": "Epic Tribal Drums", "views": 5_200_000, "rank": 3},
            {"title": "Meditation Bowl Sounds", "views": 4_100_000, "rank": 4},
            {"title": "Outback Sunrise Vibes", "views": 3_800_000, "rank": 5},
            {"title": "Bass Drop Challenge", "views": 12_000_000, "rank": 6},
            {"title": "Street Musician Magic", "views": 7_300_000, "rank": 7},
            {"title": "Acoustic Guitar Trend", "views": 6_100_000, "rank": 8},
            {"title": "Nature Sounds ASMR", "views": 9_400_000, "rank": 9},
            {"title": "World Music Fusion", "views": 2_900_000, "rank": 10},
        ]

    def _get_demo_hashtags(self) -> list[dict]:
        """Return demo trending hashtags for development/testing."""
        return [
            {"name": "fyp", "videoCount": 500_000_000, "rank": 1},
            {"name": "viral", "videoCount": 300_000_000, "rank": 2},
            {"name": "music", "videoCount": 200_000_000, "rank": 3},
            {"name": "talent", "videoCount": 80_000_000, "rank": 4},
            {"name": "streetmusic", "videoCount": 15_000_000, "rank": 5},
            {"name": "mindblowing", "videoCount": 45_000_000, "rank": 6},
            {"name": "indigenous", "videoCount": 8_000_000, "rank": 7},
            {"name": "australia", "videoCount": 25_000_000, "rank": 8},
            {"name": "satisfying", "videoCount": 150_000_000, "rank": 9},
            {"name": "musician", "videoCount": 60_000_000, "rank": 10},
        ]

    # ── Persistence ──────────────────────────────────────────────

    def _save_trends(self, trends: dict):
        """Persist trends to disk."""
        try:
            self.trends_file.write_text(
                json.dumps(trends, indent=2, default=str), encoding="utf-8"
            )
        except Exception:
            pass

    def load_cached_trends(self) -> Optional[dict]:
        """Load previously cached trends from disk."""
        try:
            if self.trends_file.exists():
                data = json.loads(self.trends_file.read_text(encoding="utf-8"))
                self._cached_trends = data
                return data
        except Exception:
            pass
        return None


async def _async_sleep(seconds: float):
    """Async-compatible sleep."""
    import asyncio
    await asyncio.sleep(seconds)
