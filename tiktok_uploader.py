"""
DIDGERI-BOOM TikTok Uploader
Handles video upload to TikTok via the Content Posting API.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx

from config import (
    TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
    TIKTOK_ACCESS_TOKEN, TIKTOK_REFRESH_TOKEN,
    TIKTOK_API_BASE, MAX_DAILY_POSTS, DATA_DIR,
)


class TikTokUploader:
    """Manages video uploads to TikTok via the Content Posting API."""

    def __init__(self):
        self.access_token = TIKTOK_ACCESS_TOKEN
        self.refresh_token = TIKTOK_REFRESH_TOKEN
        self.upload_log_path = DATA_DIR / "upload_log.json"
        self._upload_log = self._load_upload_log()

    # ── Public API ───────────────────────────────────────────────

    async def upload_video(
        self,
        video_path: Path,
        title: str,
        hashtags: list[str] = None,
        as_draft: bool = True,
    ) -> dict:
        """
        Upload a video to TikTok.

        Args:
            video_path: Path to the processed video file
            title: Video title/caption
            hashtags: List of hashtags to include
            as_draft: If True, uploads as draft (recommended for unaudited apps)
        """
        video_path = Path(video_path)
        if not video_path.exists():
            return {"error": f"Video not found: {video_path}"}

        # Check daily limit
        if self._daily_upload_count() >= MAX_DAILY_POSTS:
            return {"error": f"Daily upload limit reached ({MAX_DAILY_POSTS})"}

        # Build caption with hashtags
        caption = self._build_caption(title, hashtags or [])

        if not self.access_token:
            # No API configured — simulate upload
            return self._simulate_upload(video_path, caption)

        try:
            # Step 1: Initialize upload
            init_result = await self._init_upload(video_path, caption, as_draft)
            if "error" in init_result:
                return init_result

            publish_id = init_result.get("publish_id")
            upload_url = init_result.get("upload_url")

            if upload_url:
                # Step 2: Upload the video file
                upload_result = await self._upload_file(upload_url, video_path)
                if "error" in upload_result:
                    return upload_result

            # Step 3: Check publish status
            status = await self._check_publish_status(publish_id)

            # Log the upload
            log_entry = {
                "video": video_path.name,
                "caption": caption,
                "publish_id": publish_id,
                "status": status.get("status", "unknown"),
                "uploaded_at": datetime.now().isoformat(),
                "as_draft": as_draft,
            }
            self._log_upload(log_entry)

            return log_entry

        except Exception as e:
            return {"error": str(e)}

    async def get_upload_status(self, publish_id: str) -> dict:
        """Check the status of a previously initiated upload."""
        return await self._check_publish_status(publish_id)

    def get_upload_history(self, limit: int = 20) -> list[dict]:
        """Get recent upload history."""
        return self._upload_log[-limit:]

    def get_daily_stats(self) -> dict:
        """Get today's upload statistics."""
        count = self._daily_upload_count()
        return {
            "uploads_today": count,
            "remaining": MAX_DAILY_POSTS - count,
            "daily_limit": MAX_DAILY_POSTS,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

    # ── TikTok API Integration ───────────────────────────────────

    async def _init_upload(
        self, video_path: Path, caption: str, as_draft: bool
    ) -> dict:
        """Initialize a video upload via TikTok Content Posting API."""
        file_size = video_path.stat().st_size

        # Determine post mode
        if as_draft:
            post_mode = "MEDIA_UPLOAD"
        else:
            post_mode = "DIRECT_POST"

        payload = {
            "post_info": {
                "title": caption[:150],  # TikTok caption limit
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
            },
            "post_mode": post_mode,
        }

        url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            data = resp.json()

            if data.get("error", {}).get("code") != "ok":
                return {"error": data.get("error", {}).get("message", "Upload init failed")}

            return {
                "publish_id": data.get("data", {}).get("publish_id"),
                "upload_url": data.get("data", {}).get("upload_url"),
            }

    async def _upload_file(self, upload_url: str, video_path: Path) -> dict:
        """Upload the actual video file to TikTok's storage."""
        file_size = video_path.stat().st_size

        headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(file_size),
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            with open(video_path, "rb") as f:
                resp = await client.put(upload_url, content=f.read(), headers=headers)

            if resp.status_code not in (200, 201):
                return {"error": f"File upload failed: HTTP {resp.status_code}"}

            return {"status": "uploaded"}

    async def _check_publish_status(self, publish_id: str) -> dict:
        """Check the publish status of an uploaded video."""
        if not publish_id:
            return {"status": "unknown"}

        url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"publish_id": publish_id}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
                data = resp.json()
                status = data.get("data", {}).get("status", "unknown")
                return {"status": status, "publish_id": publish_id}
        except Exception:
            return {"status": "unknown", "publish_id": publish_id}

    # ── OAuth Flow ───────────────────────────────────────────────

    def get_auth_url(self) -> str:
        """Generate the TikTok OAuth authorization URL."""
        scopes = "user.info.basic,video.upload,video.publish"
        redirect_uri = "http://localhost:8000/auth/callback"
        return (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={TIKTOK_CLIENT_KEY}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
        )

    async def exchange_code(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        payload = {
            "client_key": TIKTOK_CLIENT_KEY,
            "client_secret": TIKTOK_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:8000/auth/callback",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=payload)
            data = resp.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                self.refresh_token = data.get("refresh_token", "")
                self._save_tokens(data)
                return {"status": "authenticated", "expires_in": data.get("expires_in")}

            return {"error": data.get("error_description", "Auth failed")}

    # ── Helpers ──────────────────────────────────────────────────

    def _build_caption(self, title: str, hashtags: list[str]) -> str:
        """Build a TikTok caption with title and hashtags."""
        tag_str = " ".join(
            f"#{h.lstrip('#')}" for h in hashtags
        )
        caption = f"{title} {tag_str}".strip()
        # TikTok caption limit ~2200 chars
        return caption[:2200]

    def _simulate_upload(self, video_path: Path, caption: str) -> dict:
        """Simulate an upload when no API keys are configured."""
        entry = {
            "video": video_path.name,
            "caption": caption,
            "publish_id": f"sim_{int(time.time())}",
            "status": "simulated",
            "uploaded_at": datetime.now().isoformat(),
            "as_draft": True,
            "note": "No TikTok API configured — upload simulated",
        }
        self._log_upload(entry)
        return entry

    def _daily_upload_count(self) -> int:
        """Count uploads made today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            1 for entry in self._upload_log
            if entry.get("uploaded_at", "").startswith(today)
        )

    def _log_upload(self, entry: dict):
        """Log an upload to the history."""
        self._upload_log.append(entry)
        self._save_upload_log()

    def _load_upload_log(self) -> list[dict]:
        """Load upload history from disk."""
        try:
            if self.upload_log_path.exists():
                return json.loads(
                    self.upload_log_path.read_text(encoding="utf-8")
                )
        except Exception:
            pass
        return []

    def _save_upload_log(self):
        """Persist upload history to disk."""
        try:
            self.upload_log_path.write_text(
                json.dumps(self._upload_log, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _save_tokens(self, token_data: dict):
        """Persist OAuth tokens to disk."""
        try:
            token_path = DATA_DIR / "tiktok_tokens.json"
            token_path.write_text(
                json.dumps(token_data, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
