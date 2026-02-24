"""
DIDGERI-BOOM Analytics & Monetization Tracker
Tracks performance metrics and monetization progress.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import (
    CREATOR_REWARDS_MIN_FOLLOWERS, CREATOR_REWARDS_MIN_VIEWS_30D,
    CREATOR_REWARDS_MIN_VIDEO_LENGTH, TIKTOK_SHOP_MIN_FOLLOWERS,
    LIVE_GIFTS_MIN_FOLLOWERS, DATA_DIR,
)


class Analytics:
    """Tracks video and account performance metrics."""

    def __init__(self):
        self.data_file = DATA_DIR / "analytics.json"
        self._data = self._load_data()

    def record_video(self, video_data: dict):
        """Record a posted video's initial data."""
        entry = {
            "video_id": video_data.get("publish_id", f"vid_{int(datetime.now().timestamp())}"),
            "filename": video_data.get("video", "unknown"),
            "caption": video_data.get("caption", ""),
            "posted_at": video_data.get("uploaded_at", datetime.now().isoformat()),
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "saves": 0,
            "watch_time_avg": 0,
            "last_updated": datetime.now().isoformat(),
        }
        self._data["videos"].append(entry)
        self._save_data()

    def update_video_stats(self, video_id: str, stats: dict):
        """Update a video's performance metrics."""
        for video in self._data["videos"]:
            if video["video_id"] == video_id:
                video.update(stats)
                video["last_updated"] = datetime.now().isoformat()
                break
        self._save_data()

    def update_account_stats(self, stats: dict):
        """Update account-level metrics."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "followers": stats.get("followers", 0),
            "following": stats.get("following", 0),
            "total_likes": stats.get("total_likes", 0),
            "total_views": stats.get("total_views", 0),
        }
        self._data["account_history"].append(entry)
        self._data["current_stats"] = entry
        self._save_data()

    def get_dashboard_data(self) -> dict:
        """Get complete analytics data for the dashboard."""
        videos = self._data.get("videos", [])
        account = self._data.get("current_stats", self._demo_stats())
        history = self._data.get("account_history", [])

        if videos:
            # Calculate from tracked videos
            total_views = sum(v.get("views", 0) for v in videos)
            total_likes = sum(v.get("likes", 0) for v in videos)
            total_engagement = total_likes + sum(v.get("comments", 0) for v in videos) + sum(v.get("shares", 0) for v in videos)
            avg_engagement_rate = (total_engagement / max(total_views, 1)) * 100

            # Views in last 30 days
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            recent_videos = [
                v for v in videos
                if v.get("posted_at", "") >= thirty_days_ago
            ]
            views_30d = sum(v.get("views", 0) for v in recent_videos)
        else:
            # Fallback to account-level stats when no videos are tracked
            total_views = account.get("total_views", 0)
            total_likes = account.get("total_likes", 0)
            total_engagement = total_likes
            avg_engagement_rate = (total_engagement / max(total_views, 1)) * 100
            views_30d = account.get("views_30d", 0)

        # Best performing video
        best_video = max(videos, key=lambda v: v.get("views", 0)) if videos else None

        return {
            "account": account,
            "totals": {
                "total_videos": len(videos),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_engagement": total_engagement,
                "avg_engagement_rate": round(avg_engagement_rate, 2),
                "views_30d": views_30d,
            },
            "best_video": best_video,
            "recent_videos": videos[-10:],
            "history": history[-30:],
        }

    def _demo_stats(self) -> dict:
        """Fallback account stats from last known scrape (14 Feb 2026)."""
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "followers": 43_600,
            "following": 684,
            "total_likes": 1_200_000,
            "total_views": 10_100_000,
            "views_30d": 680_000,  # Estimated from recent visible videos
        }

    def _load_data(self) -> dict:
        try:
            if self.data_file.exists():
                return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {
            "videos": [],
            "account_history": [],
            "current_stats": self._demo_stats(),
        }

    def _save_data(self):
        try:
            self.data_file.write_text(
                json.dumps(self._data, indent=2, default=str), encoding="utf-8"
            )
        except Exception:
            pass


class MonetizationTracker:
    """Tracks progress toward TikTok monetization milestones."""

    def __init__(self, analytics: Analytics):
        self.analytics = analytics
        self.data_file = DATA_DIR / "monetization.json"
        self._data = self._load_data()

    def get_monetization_dashboard(self) -> dict:
        """Get complete monetization status and progress."""
        stats = self.analytics._data.get("current_stats", self.analytics._demo_stats())
        dash_data = self.analytics.get_dashboard_data()

        followers = stats.get("followers", 0)
        views_30d = dash_data["totals"]["views_30d"]

        return {
            "creator_rewards": self._check_creator_rewards(followers, views_30d),
            "tiktok_shop": self._check_tiktok_shop(followers),
            "live_gifts": self._check_live_gifts(followers),
            "brand_deals": self._check_brand_deals(followers, dash_data),
            "revenue_estimate": self._estimate_revenue(views_30d, followers),
            "total_estimated_monthly": self._total_monthly_estimate(views_30d, followers),
            "roadmap": self._generate_roadmap(followers, views_30d),
        }

    def _check_creator_rewards(self, followers: int, views_30d: int) -> dict:
        """Check Creator Rewards Program eligibility."""
        follower_progress = min(100, (followers / CREATOR_REWARDS_MIN_FOLLOWERS) * 100)
        views_progress = min(100, (views_30d / CREATOR_REWARDS_MIN_VIEWS_30D) * 100)
        eligible = follower_progress >= 100 and views_progress >= 100

        return {
            "name": "Creator Rewards Program",
            "eligible": eligible,
            "requirements": {
                "followers": {
                    "current": followers,
                    "required": CREATOR_REWARDS_MIN_FOLLOWERS,
                    "progress": round(follower_progress, 1),
                    "remaining": max(0, CREATOR_REWARDS_MIN_FOLLOWERS - followers),
                },
                "views_30d": {
                    "current": views_30d,
                    "required": CREATOR_REWARDS_MIN_VIEWS_30D,
                    "progress": round(views_progress, 1),
                    "remaining": max(0, CREATOR_REWARDS_MIN_VIEWS_30D - views_30d),
                },
                "min_video_length": f"{CREATOR_REWARDS_MIN_VIDEO_LENGTH}s (1 minute+)",
            },
            "estimated_rpm": "$0.50 - $1.50",
            "status": "✅ ELIGIBLE" if eligible else "⏳ IN PROGRESS",
        }

    def _check_tiktok_shop(self, followers: int) -> dict:
        """Check TikTok Shop eligibility."""
        progress = min(100, (followers / TIKTOK_SHOP_MIN_FOLLOWERS) * 100)
        return {
            "name": "TikTok Shop",
            "eligible": progress >= 100,
            "progress": round(progress, 1),
            "current_followers": followers,
            "required_followers": TIKTOK_SHOP_MIN_FOLLOWERS,
            "potential": "Sell didgeridoos, merch, lesson packages",
            "status": "✅ ELIGIBLE" if progress >= 100 else "⏳ IN PROGRESS",
        }

    def _check_live_gifts(self, followers: int) -> dict:
        """Check TikTok Live Gift eligibility."""
        progress = min(100, (followers / LIVE_GIFTS_MIN_FOLLOWERS) * 100)
        return {
            "name": "Live Gifts",
            "eligible": progress >= 100,
            "progress": round(progress, 1),
            "current_followers": followers,
            "required_followers": LIVE_GIFTS_MIN_FOLLOWERS,
            "potential": "Live didgeridoo sessions → direct viewer tips",
            "status": "✅ ELIGIBLE" if progress >= 100 else "⏳ IN PROGRESS",
        }

    def _check_brand_deals(self, followers: int, dash_data: dict) -> dict:
        """Assess brand deal readiness."""
        eng_rate = dash_data["totals"]["avg_engagement_rate"]

        # Brand deals typically require 5K+ followers and good engagement
        readiness = 0
        if followers >= 5000:
            readiness += 40
        elif followers >= 1000:
            readiness += 20

        if eng_rate >= 5:
            readiness += 40
        elif eng_rate >= 2:
            readiness += 20

        if dash_data["totals"]["total_videos"] >= 20:
            readiness += 20

        return {
            "name": "Brand Deals & Sponsorships",
            "readiness_score": min(100, readiness),
            "engagement_rate": round(eng_rate, 2),
            "potential_brands": [
                "Music instrument companies",
                "Australian tourism",
                "Meditation/wellness apps",
                "Outdoor/adventure brands",
                "Cultural events & festivals",
            ],
            "estimated_rate": "$50-500 per post" if followers >= 5000 else "Build to 5K followers first",
            "status": "✅ READY" if readiness >= 80 else "⏳ BUILDING",
        }

    def _estimate_revenue(self, views_30d: int, followers: int) -> dict:
        """Estimate monthly revenue from each stream."""
        # Creator Rewards: ~$0.50-1.50 per 1K views (qualified views on 1min+ content)
        cr_low = (views_30d / 1000) * 0.50 if views_30d > CREATOR_REWARDS_MIN_VIEWS_30D else 0
        cr_high = (views_30d / 1000) * 1.50 if views_30d > CREATOR_REWARDS_MIN_VIEWS_30D else 0

        # Live gifts estimate (if eligible)
        live_low = 50 if followers >= LIVE_GIFTS_MIN_FOLLOWERS else 0
        live_high = 300 if followers >= LIVE_GIFTS_MIN_FOLLOWERS else 0

        return {
            "creator_rewards": {"low": round(cr_low, 2), "high": round(cr_high, 2)},
            "live_gifts": {"low": live_low, "high": live_high},
            "brand_deals": {"low": 0 if followers < 5000 else 200, "high": 0 if followers < 5000 else 2000},
        }

    def _total_monthly_estimate(self, views_30d: int, followers: int) -> dict:
        """Total monthly revenue estimate."""
        rev = self._estimate_revenue(views_30d, followers)
        low = sum(v["low"] for v in rev.values())
        high = sum(v["high"] for v in rev.values())
        return {"low": round(low, 2), "high": round(high, 2), "currency": "USD"}

    def _generate_roadmap(self, followers: int, views_30d: int) -> list[dict]:
        """Generate a monetization roadmap."""
        roadmap = []

        if followers < LIVE_GIFTS_MIN_FOLLOWERS:
            roadmap.append({
                "milestone": "🎯 1,000 Followers",
                "unlocks": "TikTok Live Gifts",
                "remaining": LIVE_GIFTS_MIN_FOLLOWERS - followers,
                "estimated_weeks": max(1, (LIVE_GIFTS_MIN_FOLLOWERS - followers) // 100),
            })

        if followers < TIKTOK_SHOP_MIN_FOLLOWERS:
            roadmap.append({
                "milestone": "🛒 5,000 Followers",
                "unlocks": "TikTok Shop + Brand Deals",
                "remaining": TIKTOK_SHOP_MIN_FOLLOWERS - followers,
                "estimated_weeks": max(1, (TIKTOK_SHOP_MIN_FOLLOWERS - followers) // 150),
            })

        if followers < CREATOR_REWARDS_MIN_FOLLOWERS:
            roadmap.append({
                "milestone": "💰 10,000 Followers",
                "unlocks": "Creator Rewards Program",
                "remaining": CREATOR_REWARDS_MIN_FOLLOWERS - followers,
                "estimated_weeks": max(1, (CREATOR_REWARDS_MIN_FOLLOWERS - followers) // 200),
            })

        roadmap.append({
            "milestone": "🚀 50,000 Followers",
            "unlocks": "Major Brand Deals ($500-5K per post)",
            "remaining": max(0, 50_000 - followers),
            "estimated_weeks": max(1, (max(0, 50_000 - followers)) // 500),
        })

        roadmap.append({
            "milestone": "👑 100,000 Followers",
            "unlocks": "Premium Sponsorships + Creator Marketplace",
            "remaining": max(0, 100_000 - followers),
            "estimated_weeks": max(1, (max(0, 100_000 - followers)) // 800),
        })

        return roadmap

    def _load_data(self) -> dict:
        try:
            if self.data_file.exists():
                return json.loads(self.data_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"history": []}

    def _save_data(self):
        try:
            self.data_file.write_text(
                json.dumps(self._data, indent=2, default=str), encoding="utf-8"
            )
        except Exception:
            pass
