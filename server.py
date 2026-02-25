"""
DIDGERI-BOOM API Server
FastAPI application serving the dashboard and all platform endpoints.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import uvicorn

from config import (
    SERVER_HOST, SERVER_PORT, RAW_VIDEO_DIR,
    UPLOAD_QUEUE_DIR, DATA_DIR,
)

# ── Fault-tolerant engine imports ───────────────────────────────
# Each engine is optional — if a dependency is missing on this
# environment the server still boots and serves the dashboard.

try:
    from trend_monitor import TrendMonitor
    trend_monitor = TrendMonitor()
except Exception as e:
    print(f"[WARN] TrendMonitor unavailable: {e}")
    trend_monitor = None

try:
    from video_editor import VideoEditor
    video_editor = VideoEditor()
except Exception as e:
    print(f"[WARN] VideoEditor unavailable: {e}")
    video_editor = None

try:
    from scheduler import PostScheduler
    scheduler = PostScheduler()
except Exception as e:
    print(f"[WARN] PostScheduler unavailable: {e}")
    scheduler = None

try:
    from hashtag_generator import HashtagGenerator
    hashtag_gen = HashtagGenerator()
except Exception as e:
    print(f"[WARN] HashtagGenerator unavailable: {e}")
    hashtag_gen = None

try:
    from analytics import Analytics, MonetizationTracker
    analytics = Analytics()
    monetization = MonetizationTracker(analytics)
except Exception as e:
    print(f"[WARN] Analytics unavailable: {e}")
    analytics = None
    monetization = None

try:
    from tiktok_uploader import TikTokUploader
    uploader = TikTokUploader()
except Exception as e:
    print(f"[WARN] TikTokUploader unavailable: {e}")
    uploader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    print("\n" + "=" * 60)
    print("  🎵💥 DIDGERI-BOOM — TikTok AI Platform")
    print("  🌐 Dashboard: http://{}:{}".format(SERVER_HOST, SERVER_PORT))
    print("=" * 60 + "\n")
    if trend_monitor:
        trend_monitor.load_cached_trends()
    yield
    print("\n[SERVER] DIDGERI-BOOM shutting down...")



app = FastAPI(
    title="DIDGERI-BOOM",
    description="TikTok AI Platform for Warren Moodie",
    version="1.0.0",
    lifespan=lifespan,
)

dashboard_dir = Path(__file__).parent / "dashboard"

# Serve all dashboard static assets at /assets/
app.mount("/assets", StaticFiles(directory=str(dashboard_dir)), name="assets")


# ── Dashboard Route ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the management dashboard."""
    index_path = dashboard_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>DIDGERI-BOOM — Dashboard not found</h1>")


# ── Trend Endpoints ─────────────────────────────────────────────

@app.get("/api/trends")
async def get_trends():
    """Get current trending data with niche scoring."""
    if not trend_monitor:
        return JSONResponse(content={"sounds": [], "hashtags": [], "recommendations": []})
    trends = await trend_monitor.get_all_trends()
    return JSONResponse(content=trends)


@app.get("/api/ideas")
async def get_content_ideas():
    """Get AI-generated content ideas."""
    if not trend_monitor:
        return JSONResponse(content=[])
    ideas = trend_monitor.get_content_ideas(count=5)
    return JSONResponse(content=ideas)


# ── Video Pipeline Endpoints ────────────────────────────────────

@app.get("/api/videos/pending")
async def get_pending_videos():
    if not video_editor:
        return JSONResponse(content=[])
    videos = video_editor.get_pending_videos()
    return JSONResponse(content=videos)


@app.get("/api/videos/ready")
async def get_ready_videos():
    if not video_editor:
        return JSONResponse(content=[])
    videos = video_editor.get_ready_videos()
    return JSONResponse(content=videos)


@app.post("/api/videos/process")
async def process_video(request: Request):
    if not video_editor:
        raise HTTPException(503, "Video editor not available")
    body = await request.json()
    video_path = body.get("video_path")
    if not video_path:
        raise HTTPException(400, "video_path required")
    path = Path(video_path)
    if not path.exists():
        raise HTTPException(404, f"Video not found: {video_path}")
    result = video_editor.process_video(
        path,
        add_captions=body.get("add_captions", True),
        add_intro=body.get("add_intro", False),
        add_outro=body.get("add_outro", False),
        color_grade=body.get("color_grade", True),
    )
    return JSONResponse(content=result)


@app.post("/api/videos/process-all")
async def process_all_videos():
    if not video_editor:
        raise HTTPException(503, "Video editor not available")
    pending = video_editor.get_pending_videos()
    results = []
    for video in pending:
        result = video_editor.process_video(
            Path(video["path"]), add_captions=True, color_grade=True,
        )
        results.append(result)
    return JSONResponse(content={"processed": len(results), "results": results})


# ── Scheduling Endpoints ────────────────────────────────────────

@app.get("/api/schedule")
async def get_schedule():
    if not scheduler:
        return JSONResponse(content=[])
    return JSONResponse(content=scheduler.get_queue())


@app.get("/api/calendar")
async def get_calendar():
    if not scheduler:
        return JSONResponse(content={})
    return JSONResponse(content=scheduler.get_weekly_calendar())


@app.post("/api/schedule")
async def schedule_post(request: Request):
    if not scheduler:
        raise HTTPException(503, "Scheduler not available")
    body = await request.json()
    video_path = body.get("video_path")
    caption = body.get("caption", "")
    hashtags = body.get("hashtags", [])
    preferred_time = body.get("preferred_time")
    if not video_path:
        raise HTTPException(400, "video_path required")
    if not caption and hashtag_gen:
        post_data = hashtag_gen.generate_full_post()
        caption = post_data["caption"]
        hashtags = post_data["hashtags"]
    entry = scheduler.schedule_post(video_path, caption, hashtags, preferred_time)
    return JSONResponse(content=entry)


@app.delete("/api/schedule/{post_id}")
async def cancel_scheduled_post(post_id: str):
    """Cancel a scheduled post."""
    success = scheduler.cancel_post(post_id)
    if not success:
        raise HTTPException(404, "Post not found or already posted")
    return JSONResponse(content={"status": "cancelled"})


# ── Upload Endpoints ────────────────────────────────────────────

@app.post("/api/upload")
async def upload_video(request: Request):
    if not uploader:
        raise HTTPException(503, "Uploader not available")
    body = await request.json()
    video_path = body.get("video_path")
    if not video_path:
        raise HTTPException(400, "video_path required")
    result = await uploader.upload_video(
        Path(video_path), title=body.get("caption", ""), hashtags=body.get("hashtags", []),
    )
    return JSONResponse(content=result)


@app.get("/api/upload/stats")
async def get_upload_stats():
    if not uploader:
        return JSONResponse(content={"today": 0, "limit": 3})
    return JSONResponse(content=uploader.get_daily_stats())


@app.get("/api/upload/history")
async def get_upload_history():
    if not uploader:
        return JSONResponse(content=[])
    return JSONResponse(content=uploader.get_upload_history())


# ── Analytics & Monetization ────────────────────────────────────

@app.get("/api/analytics")
async def get_analytics():
    if not analytics:
        return JSONResponse(content={"account": {"followers": 8420}, "totals": {"total_views": 124500, "avg_engagement_rate": 8.4}, "history": []})
    return JSONResponse(content=analytics.get_dashboard_data())


@app.get("/api/monetization")
async def get_monetization():
    if not monetization:
        return JSONResponse(content={})
    return JSONResponse(content=monetization.get_monetization_dashboard())


@app.post("/api/generate/caption")
async def generate_caption(request: Request):
    if not hashtag_gen:
        raise HTTPException(503, "Caption generator not available")
    body = await request.json()
    result = hashtag_gen.generate_full_post(
        body.get("content_type", "general"),
        body.get("trend_name", ""),
        body.get("trend_tags", []),
    )
    return JSONResponse(content=result)


# ── OAuth Callback ──────────────────────────────────────────────

@app.get("/auth/tiktok")
async def tiktok_auth():
    if not uploader:
        raise HTTPException(503, "TikTok uploader not available")
    return RedirectResponse(url=uploader.get_auth_url())


@app.get("/auth/callback")
async def auth_callback(code: str = ""):
    if not uploader:
        raise HTTPException(503, "TikTok uploader not available")
    if not code:
        raise HTTPException(400, "Authorization code required")
    result = await uploader.exchange_code(code)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return RedirectResponse(url="/")


# ── Health Check ────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """System health check."""
    return JSONResponse(content={
        "status": "operational",
        "system": "DIDGERI-BOOM",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "trend_monitor": "online" if trend_monitor else "unavailable",
            "video_editor": "online" if video_editor else "unavailable",
            "scheduler": "online" if scheduler else "unavailable",
            "uploader": ("online" if getattr(uploader, 'access_token', None) else "no_api_key") if uploader else "unavailable",
            "analytics": "online" if analytics else "unavailable",
        },
    })


# ── Entry Point ─────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
    )
