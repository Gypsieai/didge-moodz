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
from trend_monitor import TrendMonitor
from video_editor import VideoEditor
from scheduler import PostScheduler
from hashtag_generator import HashtagGenerator
from analytics import Analytics, MonetizationTracker
from tiktok_uploader import TikTokUploader


# ── Initialize Engines ──────────────────────────────────────────
trend_monitor = TrendMonitor()
video_editor = VideoEditor()
scheduler = PostScheduler()
hashtag_gen = HashtagGenerator()
analytics = Analytics()
monetization = MonetizationTracker(analytics)
uploader = TikTokUploader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    print("\n" + "=" * 60)
    print("  🎵💥 DIDGERI-BOOM — TikTok AI Platform")
    print("  🌐 Dashboard: http://{}:{}".format(SERVER_HOST, SERVER_PORT))
    print("  📁 Raw Videos: {}".format(RAW_VIDEO_DIR))
    print("  📤 Upload Queue: {}".format(UPLOAD_QUEUE_DIR))
    print("=" * 60 + "\n")
    # Load cached data
    trend_monitor.load_cached_trends()
    yield
    print("\n[SERVER] DIDGERI-BOOM shutting down...")


app = FastAPI(
    title="DIDGERI-BOOM",
    description="TikTok AI Platform for Warren Moodie",
    version="1.0.0",
    lifespan=lifespan,
)

# Serve dashboard static files
dashboard_dir = Path(__file__).parent / "dashboard"
if dashboard_dir.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")


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
    trends = await trend_monitor.get_all_trends()
    return JSONResponse(content=trends)


@app.get("/api/ideas")
async def get_content_ideas():
    """Get AI-generated content ideas."""
    ideas = trend_monitor.get_content_ideas(count=5)
    return JSONResponse(content=ideas)


# ── Video Pipeline Endpoints ────────────────────────────────────

@app.get("/api/videos/pending")
async def get_pending_videos():
    """List raw videos waiting to be processed."""
    videos = video_editor.get_pending_videos()
    return JSONResponse(content=videos)


@app.get("/api/videos/ready")
async def get_ready_videos():
    """List processed videos ready for upload."""
    videos = video_editor.get_ready_videos()
    return JSONResponse(content=videos)


@app.post("/api/videos/process")
async def process_video(request: Request):
    """Process a raw video through the editing pipeline."""
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
    """Process all pending raw videos."""
    pending = video_editor.get_pending_videos()
    results = []
    for video in pending:
        result = video_editor.process_video(
            Path(video["path"]),
            add_captions=True,
            color_grade=True,
        )
        results.append(result)
    return JSONResponse(content={"processed": len(results), "results": results})


# ── Scheduling Endpoints ────────────────────────────────────────

@app.get("/api/schedule")
async def get_schedule():
    """Get the upload schedule queue."""
    queue = scheduler.get_queue()
    return JSONResponse(content=queue)


@app.get("/api/calendar")
async def get_calendar():
    """Get the weekly content calendar."""
    calendar = scheduler.get_weekly_calendar()
    return JSONResponse(content=calendar)


@app.post("/api/schedule")
async def schedule_post(request: Request):
    """Schedule a video for posting."""
    body = await request.json()
    video_path = body.get("video_path")
    caption = body.get("caption", "")
    hashtags = body.get("hashtags", [])
    preferred_time = body.get("preferred_time")

    if not video_path:
        raise HTTPException(400, "video_path required")

    # Auto-generate caption and hashtags if not provided
    if not caption:
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
    """Trigger a manual upload to TikTok."""
    body = await request.json()
    video_path = body.get("video_path")
    caption = body.get("caption", "")
    hashtags = body.get("hashtags", [])

    if not video_path:
        raise HTTPException(400, "video_path required")

    result = await uploader.upload_video(
        Path(video_path),
        title=caption,
        hashtags=hashtags,
    )
    return JSONResponse(content=result)


@app.get("/api/upload/stats")
async def get_upload_stats():
    """Get today's upload statistics."""
    stats = uploader.get_daily_stats()
    return JSONResponse(content=stats)


@app.get("/api/upload/history")
async def get_upload_history():
    """Get upload history."""
    history = uploader.get_upload_history()
    return JSONResponse(content=history)


# ── Analytics & Monetization ────────────────────────────────────

@app.get("/api/analytics")
async def get_analytics():
    """Get performance analytics."""
    data = analytics.get_dashboard_data()
    return JSONResponse(content=data)


@app.get("/api/monetization")
async def get_monetization():
    """Get monetization progress and estimates."""
    data = monetization.get_monetization_dashboard()
    return JSONResponse(content=data)


# ── Hashtag & Caption Generation ────────────────────────────────

@app.post("/api/generate/caption")
async def generate_caption(request: Request):
    """Generate an AI caption with hashtags."""
    body = await request.json()
    content_type = body.get("content_type", "general")
    trend_name = body.get("trend_name", "")
    trend_tags = body.get("trend_tags", [])

    result = hashtag_gen.generate_full_post(content_type, trend_name, trend_tags)
    return JSONResponse(content=result)


# ── OAuth Callback ──────────────────────────────────────────────

@app.get("/auth/tiktok")
async def tiktok_auth():
    """Redirect to TikTok OAuth."""
    url = uploader.get_auth_url()
    return RedirectResponse(url=url)


@app.get("/auth/callback")
async def auth_callback(code: str = ""):
    """Handle TikTok OAuth callback."""
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
            "trend_monitor": "online",
            "video_editor": "online",
            "scheduler": "online",
            "uploader": "online" if uploader.access_token else "no_api_key",
            "analytics": "online",
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
