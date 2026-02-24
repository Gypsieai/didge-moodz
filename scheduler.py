"""
DIDGERI-BOOM Scheduler
Manages optimal posting schedule and upload queue.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from config import (
    MAX_DAILY_POSTS, PEAK_HOURS, TIMEZONE,
    UPLOAD_QUEUE_DIR, DATA_DIR,
)


class PostScheduler:
    """Manages the upload queue and optimal posting schedule."""

    def __init__(self):
        self.schedule_file = DATA_DIR / "schedule.json"
        self._schedule = self._load_schedule()

    # ── Public API ───────────────────────────────────────────────

    def schedule_post(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        preferred_time: Optional[str] = None,
    ) -> dict:
        """Schedule a video for posting at an optimal time."""
        if preferred_time:
            post_time = datetime.fromisoformat(preferred_time)
        else:
            post_time = self._next_optimal_time()

        entry = {
            "id": f"post_{int(datetime.now().timestamp())}_{random.randint(100,999)}",
            "video_path": video_path,
            "caption": caption,
            "hashtags": hashtags,
            "scheduled_for": post_time.isoformat(),
            "status": "scheduled",  # scheduled | uploading | posted | failed
            "created_at": datetime.now().isoformat(),
        }

        self._schedule.append(entry)
        self._save_schedule()
        return entry

    def get_queue(self) -> list[dict]:
        """Get all scheduled posts, sorted by time."""
        return sorted(
            self._schedule,
            key=lambda x: x.get("scheduled_for", ""),
        )

    def get_pending(self) -> list[dict]:
        """Get posts that are due for upload."""
        now = datetime.now()
        return [
            p for p in self._schedule
            if p["status"] == "scheduled"
            and datetime.fromisoformat(p["scheduled_for"]) <= now
        ]

    def mark_posted(self, post_id: str):
        """Mark a scheduled post as uploaded."""
        for entry in self._schedule:
            if entry["id"] == post_id:
                entry["status"] = "posted"
                entry["posted_at"] = datetime.now().isoformat()
                break
        self._save_schedule()

    def mark_failed(self, post_id: str, error: str):
        """Mark a scheduled post as failed."""
        for entry in self._schedule:
            if entry["id"] == post_id:
                entry["status"] = "failed"
                entry["error"] = error
                break
        self._save_schedule()

    def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post."""
        for entry in self._schedule:
            if entry["id"] == post_id and entry["status"] == "scheduled":
                entry["status"] = "cancelled"
                self._save_schedule()
                return True
        return False

    def get_weekly_calendar(self) -> list[dict]:
        """Generate a weekly content calendar with optimal time slots."""
        calendar = []
        now = datetime.now()

        for day_offset in range(7):
            day = now + timedelta(days=day_offset)
            day_name = day.strftime("%A")
            day_str = day.strftime("%Y-%m-%d")

            # Get scheduled posts for this day
            day_posts = [
                p for p in self._schedule
                if p.get("scheduled_for", "").startswith(day_str)
            ]

            # Suggest optimal time slots
            slots = self._get_day_slots(day)
            remaining = MAX_DAILY_POSTS - len(day_posts)

            calendar.append({
                "date": day_str,
                "day_name": day_name,
                "scheduled_posts": day_posts,
                "suggested_slots": slots[:remaining],
                "posts_remaining": max(0, remaining),
            })

        return calendar

    # ── Optimal Timing ───────────────────────────────────────────

    def _next_optimal_time(self) -> datetime:
        """Calculate the next optimal posting time."""
        now = datetime.now()

        # Find next available peak hour
        for hour in sorted(PEAK_HOURS):
            candidate = now.replace(
                hour=hour,
                minute=random.randint(0, 20),  # Slight randomization
                second=0,
            )
            if candidate > now:
                # Check if we haven't exceeded daily limit for that day
                day_str = candidate.strftime("%Y-%m-%d")
                day_count = sum(
                    1 for p in self._schedule
                    if p.get("scheduled_for", "").startswith(day_str)
                    and p["status"] in ("scheduled", "posted")
                )
                if day_count < MAX_DAILY_POSTS:
                    return candidate

        # All today's slots used — try tomorrow
        tomorrow = now + timedelta(days=1)
        hour = PEAK_HOURS[0]
        return tomorrow.replace(
            hour=hour,
            minute=random.randint(0, 20),
            second=0,
        )

    def _get_day_slots(self, day: datetime) -> list[dict]:
        """Get optimal posting slots for a given day."""
        slots = []
        for hour in PEAK_HOURS[:MAX_DAILY_POSTS]:
            slot_time = day.replace(hour=hour, minute=0, second=0)
            engagement_label = self._engagement_label(hour)
            slots.append({
                "time": slot_time.strftime("%H:%M"),
                "datetime": slot_time.isoformat(),
                "engagement": engagement_label,
            })
        return slots

    def _engagement_label(self, hour: int) -> str:
        """Label expected engagement level for a posting hour."""
        if hour in (18, 19, 20, 21):
            return "🔥 Peak"
        elif hour in (7, 8, 12, 17):
            return "✅ Good"
        else:
            return "⚡ Moderate"

    # ── Persistence ──────────────────────────────────────────────

    def _load_schedule(self) -> list[dict]:
        try:
            if self.schedule_file.exists():
                return json.loads(self.schedule_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _save_schedule(self):
        try:
            self.schedule_file.write_text(
                json.dumps(self._schedule, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass
