"""
DIDGERI-BOOM Configuration Module
Central configuration for the TikTok AI Platform.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ── Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_VIDEO_DIR = Path(os.getenv("RAW_VIDEO_DIR", str(DATA_DIR / "raw_videos")))
PROCESSED_VIDEO_DIR = Path(os.getenv("PROCESSED_VIDEO_DIR", str(DATA_DIR / "processed_videos")))
UPLOAD_QUEUE_DIR = Path(os.getenv("UPLOAD_QUEUE_DIR", str(DATA_DIR / "upload_queue")))
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = DATA_DIR / "didgeri_boom.json"

# Ensure directories exist
for d in [RAW_VIDEO_DIR, PROCESSED_VIDEO_DIR, UPLOAD_QUEUE_DIR, DATA_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── TikTok API ───────────────────────────────────────────────────
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_REFRESH_TOKEN = os.getenv("TIKTOK_REFRESH_TOKEN", "")
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# ── Trend Monitoring ─────────────────────────────────────────────
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
APIFY_TRENDING_SOUNDS_ACTOR = "clockworks/tiktok-trending-sounds-scraper"
APIFY_TRENDING_HASHTAGS_ACTOR = "clockworks/tiktok-trending-hashtags"

# ── Video Settings ───────────────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
VIDEO_BITRATE = "4M"
AUDIO_BITRATE = "128k"
MAX_FILE_SIZE_MB = 287  # TikTok max
SUPPORTED_INPUT_FORMATS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# ── Whisper (Captions) ──────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# ── Scheduling ──────────────────────────────────────────────────
MAX_DAILY_POSTS = int(os.getenv("MAX_DAILY_POSTS", "3"))
TIMEZONE = os.getenv("TIMEZONE", "Australia/Brisbane")

# Peak posting hours (AEST) — optimized for global + AU audience
PEAK_HOURS = [7, 8, 12, 17, 18, 19, 20, 21]

# ── Monetization Thresholds ─────────────────────────────────────
CREATOR_REWARDS_MIN_FOLLOWERS = 10_000
CREATOR_REWARDS_MIN_VIEWS_30D = 100_000
CREATOR_REWARDS_MIN_VIDEO_LENGTH = 60  # seconds
TIKTOK_SHOP_MIN_FOLLOWERS = 5_000
LIVE_GIFTS_MIN_FOLLOWERS = 1_000

# ── Server ──────────────────────────────────────────────────────
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ── Niche Keywords ──────────────────────────────────────────────
NICHE_KEYWORDS = [
    "didgeridoo", "didjeridu", "yidaki", "aboriginal",
    "indigenous", "music", "instrument", "busking",
    "street music", "world music", "meditation",
    "drone", "circular breathing", "outback",
    "australian", "tribal", "rhythm", "percussion",
]

# ── Hashtag Pools ───────────────────────────────────────────────
CORE_HASHTAGS = [
    "#didgeridoo", "#didgeridooplayer", "#worldmusic",
    "#aboriginal", "#indigenous", "#streetmusic",
    "#busking", "#musician", "#australia",
    "#culturalmusic", "#meditation", "#drone",
]

VIRAL_HASHTAGS = [
    "#fyp", "#foryou", "#foryoupage", "#viral",
    "#trending", "#music", "#talent", "#mindblowing",
    "#satisfying", "#unique", "#wow",
]
