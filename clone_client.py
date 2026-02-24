"""
DIDGERI-BOOM Client Cloner
Spins up a new client instance from the template in seconds.

Usage:
    python clone_client.py "ClientName" "niche" --color "#FF6A00"

Example:
    python clone_client.py "ChefBoom" "cooking" --color "#E74C3C"
    python clone_client.py "FitBoom" "fitness" --color "#27AE60"
    python clone_client.py "ComedyBoom" "comedy" --color "#9B59B6"
"""

import argparse
import shutil
import re
import json
from pathlib import Path
from datetime import datetime

# ── Niche Presets ─────────────────────────────────────────────
NICHE_PRESETS = {
    "cooking": {
        "keywords": [
            "cooking", "chef", "recipe", "food", "kitchen",
            "baking", "meal prep", "foodie", "culinary", "plating",
            "restaurant", "homecook", "gourmet", "flavor",
        ],
        "core_hashtags": [
            "#cooking", "#chef", "#recipe", "#foodtiktok",
            "#homecook", "#foodie", "#yummy", "#mealprep",
            "#kitchenhacks", "#delicious", "#easyrecipe",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#food", "#satisfying", "#asmr", "#tasty",
            "#mindblowing", "#hack",
        ],
        "caption_themes": [
            "Wait for the reveal 🤯🍳",
            "This recipe broke the internet 🔥",
            "POV: You finally learn the secret ingredient 👨‍🍳",
        ],
    },
    "fitness": {
        "keywords": [
            "fitness", "workout", "gym", "exercise", "training",
            "bodybuilding", "cardio", "strength", "muscle", "gains",
            "health", "wellness", "transformation", "motivation",
        ],
        "core_hashtags": [
            "#fitness", "#workout", "#gym", "#fitnessmotivation",
            "#training", "#bodybuilding", "#exercise", "#gains",
            "#fitfam", "#personaltrainer", "#healthylifestyle",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#motivation", "#satisfying", "#transformation",
            "#mindblowing", "#wow", "#hack",
        ],
        "caption_themes": [
            "This exercise changed everything 💪🔥",
            "Nobody teaches you this at the gym 😤",
            "30 days of this = insane results 📈",
        ],
    },
    "comedy": {
        "keywords": [
            "comedy", "funny", "humor", "skit", "joke",
            "prank", "standup", "comedian", "laugh", "meme",
            "relatable", "parody", "roast", "impression",
        ],
        "core_hashtags": [
            "#comedy", "#funny", "#humor", "#skit",
            "#comedian", "#joke", "#laugh", "#standup",
            "#relatable", "#memes", "#parody",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#funny", "#lol", "#dead", "#hilarious",
            "#relatable", "#fy",
        ],
        "caption_themes": [
            "POV: This is too accurate 😂💀",
            "Tag someone who does this 👇😭",
            "I can't be the only one 🤣",
        ],
    },
    "music": {
        "keywords": [
            "music", "musician", "singer", "guitar", "piano",
            "drums", "producer", "beat", "songwriting", "cover",
            "performance", "concert", "band", "vocals",
        ],
        "core_hashtags": [
            "#music", "#musician", "#singer", "#guitar",
            "#cover", "#songwriting", "#producer", "#livemusic",
            "#performer", "#talent", "#newmusic",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#music", "#talent", "#wow", "#amazing",
            "#goosebumps", "#mindblowing",
        ],
        "caption_themes": [
            "This cover hit different 🎵🔥",
            "Wait for the high note 🤯",
            "They weren't ready for this 😮‍💨",
        ],
    },
    "beauty": {
        "keywords": [
            "beauty", "makeup", "skincare", "cosmetics", "tutorial",
            "glam", "hairstyle", "nails", "aesthetic", "routine",
            "glow", "transformation", "grwm", "sephora",
        ],
        "core_hashtags": [
            "#beauty", "#makeup", "#skincare", "#grwm",
            "#beautytok", "#glam", "#tutorial", "#aesthetic",
            "#routine", "#transformation", "#glow",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#satisfying", "#hack", "#wow", "#aesthetic",
            "#asmr", "#slay",
        ],
        "caption_themes": [
            "This product changed my LIFE 😱✨",
            "GRWM for the glow up 💅🔥",
            "The before & after is INSANE 🤯",
        ],
    },
    "gaming": {
        "keywords": [
            "gaming", "gamer", "esports", "twitch", "gameplay",
            "console", "pc", "streamer", "clutch", "win",
            "fortnite", "valorant", "minecraft", "playstation",
        ],
        "core_hashtags": [
            "#gaming", "#gamer", "#esports", "#gameplay",
            "#streamer", "#clutch", "#gamingcommunity",
            "#pcgaming", "#console", "#letsplay", "#gamertok",
        ],
        "viral_hashtags": [
            "#fyp", "#foryou", "#viral", "#trending",
            "#gaming", "#insane", "#clutch", "#wow",
            "#satisfying", "#epic",
        ],
        "caption_themes": [
            "This clutch was ILLEGAL 🎮🔥",
            "1v4 and they all got deleted 💀",
            "POV: You hit the play of your life 😤",
        ],
    },
}

# ── Color Presets ─────────────────────────────────────────────
COLOR_PRESETS = {
    "cooking":  {"primary": "#E74C3C", "name": "Flame Red"},
    "fitness":  {"primary": "#27AE60", "name": "Power Green"},
    "comedy":   {"primary": "#9B59B6", "name": "Laugh Purple"},
    "music":    {"primary": "#3498DB", "name": "Sound Blue"},
    "beauty":   {"primary": "#E91E8C", "name": "Glam Pink"},
    "gaming":   {"primary": "#00D4FF", "name": "Neon Cyan"},
}


def clone_client(client_name: str, niche: str, color: str = None, port: int = 8001):
    """Clone the DIDGERI-BOOM template for a new client."""

    template_dir = Path(__file__).parent
    projects_dir = template_dir.parent
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', client_name).upper()
    target_dir = projects_dir / f"{safe_name}_BOOM"

    if target_dir.exists():
        print(f"[ERROR] {target_dir} already exists! Delete it first or choose a different name.")
        return

    print(f"\n{'='*60}")
    print(f"  🔁 Cloning DIDGERI-BOOM → {safe_name}_BOOM")
    print(f"  📂 Target: {target_dir}")
    print(f"  🎯 Niche: {niche}")
    print(f"{'='*60}\n")

    # ── Step 1: Copy the template ────────────────────────────
    print("[1/5] Copying template files...")
    ignore = shutil.ignore_patterns(
        'data', '__pycache__', '*.pyc', '.env', 'clone_client.py',
    )
    shutil.copytree(template_dir, target_dir, ignore=ignore)

    # Create data directories
    for d in ['data/raw_videos', 'data/processed_videos', 'data/upload_queue']:
        (target_dir / d).mkdir(parents=True, exist_ok=True)

    print("   ✅ Files copied")

    # ── Step 2: Update config.py ─────────────────────────────
    print("[2/5] Customizing config.py...")
    config_path = target_dir / "config.py"
    config_text = config_path.read_text(encoding="utf-8")

    preset = NICHE_PRESETS.get(niche, NICHE_PRESETS.get("music", {}))

    # Replace niche keywords
    old_keywords = config_text[config_text.find("NICHE_KEYWORDS"):config_text.find("]", config_text.find("NICHE_KEYWORDS")) + 1]
    new_keywords = f'NICHE_KEYWORDS = {json.dumps(preset.get("keywords", []), indent=4)}'
    config_text = config_text.replace(old_keywords, new_keywords)

    # Replace core hashtags
    old_core = config_text[config_text.find("CORE_HASHTAGS"):config_text.find("]", config_text.find("CORE_HASHTAGS")) + 1]
    new_core = f'CORE_HASHTAGS = {json.dumps(preset.get("core_hashtags", []), indent=4)}'
    config_text = config_text.replace(old_core, new_core)

    # Replace viral hashtags
    old_viral = config_text[config_text.find("VIRAL_HASHTAGS"):config_text.find("]", config_text.find("VIRAL_HASHTAGS")) + 1]
    new_viral = f'VIRAL_HASHTAGS = {json.dumps(preset.get("viral_hashtags", []), indent=4)}'
    config_text = config_text.replace(old_viral, new_viral)

    # Update port
    config_text = config_text.replace(
        'SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))',
        f'SERVER_PORT = int(os.getenv("SERVER_PORT", "{port}"))',
    )

    config_path.write_text(config_text, encoding="utf-8")
    print(f"   ✅ Niche set to: {niche} ({len(preset.get('keywords', []))} keywords)")

    # ── Step 3: Reskin dashboard ─────────────────────────────
    print("[3/5] Reskinning dashboard...")
    primary = color or COLOR_PRESETS.get(niche, {}).get("primary", "#D4760A")

    # Generate color variants from primary
    css_path = target_dir / "dashboard" / "index.css"
    css_text = css_path.read_text(encoding="utf-8")

    # Replace brand colors
    css_text = css_text.replace("#D4760A", primary)
    css_text = css_text.replace("#FF9933", _lighten(primary))
    css_text = css_text.replace("#8B5E0B", _darken(primary))
    css_text = css_text.replace("#CC7722", _shift(primary, 10))

    # Replace amber references in rgba values
    css_text = css_text.replace(
        "rgba(212, 118, 10,",
        f"rgba({_hex_to_rgb(primary)},",
    )

    css_path.write_text(css_text, encoding="utf-8")

    # Update HTML title
    html_path = target_dir / "dashboard" / "index.html"
    html_text = html_path.read_text(encoding="utf-8")
    display_name = client_name.upper().replace("_", "-")
    html_text = html_text.replace("DIDGERI-BOOM", f"{display_name}-BOOM")
    html_text = html_text.replace("Warren Moodie", client_name)
    html_path.write_text(html_text, encoding="utf-8")

    print(f"   ✅ Recolored to {primary} ({COLOR_PRESETS.get(niche, {}).get('name', 'Custom')})")

    # ── Step 4: Create .env ──────────────────────────────────
    print("[4/5] Creating .env template...")
    env_path = target_dir / ".env"
    env_content = f"""# {display_name}-BOOM Configuration
# Generated: {datetime.now().isoformat()}
# Niche: {niche}

# TikTok API
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_ACCESS_TOKEN=
TIKTOK_REFRESH_TOKEN=

# Trend Monitoring
APIFY_API_TOKEN=

# Server
SERVER_HOST=127.0.0.1
SERVER_PORT={port}
MAX_DAILY_POSTS=3
TIMEZONE=Australia/Brisbane

# Whisper Model (tiny/base/small/medium)
WHISPER_MODEL=base
"""
    env_path.write_text(env_content, encoding="utf-8")
    print(f"   ✅ .env created (port {port})")

    # ── Step 5: Summary ──────────────────────────────────────
    print(f"\n[5/5] Done! 🎉")
    print(f"\n{'='*60}")
    print(f"  ✅ {display_name}-BOOM is ready!")
    print(f"  📂 Location: {target_dir}")
    print(f"  🎨 Color: {primary}")
    print(f"  🌐 Port: {port}")
    print(f"  ")
    print(f"  To launch:")
    print(f"    cd {target_dir}")
    print(f"    pip install -r requirements.txt")
    print(f"    python server.py")
    print(f"    → Dashboard at http://127.0.0.1:{port}")
    print(f"{'='*60}\n")


# ── Color Utilities ──────────────────────────────────────────
def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}"

def _lighten(hex_color: str, factor: float = 0.3) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02X}{g:02X}{b:02X}"

def _darken(hex_color: str, factor: float = 0.4) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return f"#{r:02X}{g:02X}{b:02X}"

def _shift(hex_color: str, degrees: int = 10) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    # Simple hue shift approximation
    r = min(255, max(0, r + degrees))
    g = min(255, max(0, g - degrees // 2))
    return f"#{r:02X}{g:02X}{b:02X}"


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔁 Clone DIDGERI-BOOM for a new client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clone_client.py "ChefMarco" cooking
  python clone_client.py "FitJess" fitness --color "#27AE60" --port 8002
  python clone_client.py "ComedyKing" comedy --port 8003

Available niches: cooking, fitness, comedy, music, beauty, gaming
        """,
    )
    parser.add_argument("name", help="Client name (e.g., 'ChefMarco')")
    parser.add_argument("niche", help="Content niche (cooking/fitness/comedy/music/beauty/gaming)")
    parser.add_argument("--color", help="Primary brand color hex (e.g., '#E74C3C')", default=None)
    parser.add_argument("--port", help="Server port (default: 8001)", type=int, default=8001)

    args = parser.parse_args()
    clone_client(args.name, args.niche, args.color, args.port)
