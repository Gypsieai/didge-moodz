"""
DIDGERI-BOOM Video Editor
Automated video editing pipeline: raw → TikTok-ready vertical content.
"""

import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_CODEC, AUDIO_CODEC, VIDEO_BITRATE, AUDIO_BITRATE,
    RAW_VIDEO_DIR, PROCESSED_VIDEO_DIR, UPLOAD_QUEUE_DIR,
    SUPPORTED_INPUT_FORMATS, TEMPLATES_DIR,
)
from caption_engine import CaptionEngine


class VideoEditor:
    """Processes raw video into TikTok-optimized vertical content."""

    def __init__(self):
        self.caption_engine = CaptionEngine()
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Check that FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True,
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            print(f"[VIDEO] FFmpeg ready: {version_line}")
        except FileNotFoundError:
            print("[VIDEO] ⚠️ FFmpeg not found! Install from https://ffmpeg.org")

    # ── Main Pipeline ────────────────────────────────────────────

    def process_video(
        self,
        input_path: Path,
        add_captions: bool = True,
        add_intro: bool = False,
        add_outro: bool = False,
        color_grade: bool = True,
    ) -> dict:
        """
        Full processing pipeline:
        1. Probe input → 2. Crop/pad to vertical → 3. Add captions
        4. Color grade → 5. Add intro/outro → 6. Export final
        """
        input_path = Path(input_path)
        if input_path.suffix.lower() not in SUPPORTED_INPUT_FORMATS:
            return {"error": f"Unsupported format: {input_path.suffix}"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = input_path.stem
        work_dir = PROCESSED_VIDEO_DIR / f"{stem}_{timestamp}"
        work_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "input": str(input_path),
            "stem": stem,
            "started_at": datetime.now().isoformat(),
            "steps": [],
        }

        try:
            # Step 1: Probe input
            probe = self._probe_video(input_path)
            result["probe"] = probe
            result["steps"].append("probed")

            # Step 2: Convert to vertical format
            vertical_path = work_dir / f"{stem}_vertical.mp4"
            self._make_vertical(input_path, vertical_path, probe)
            result["steps"].append("vertical")
            current = vertical_path

            # Step 3: Color grading
            if color_grade:
                graded_path = work_dir / f"{stem}_graded.mp4"
                self._apply_color_grade(current, graded_path)
                result["steps"].append("color_graded")
                current = graded_path

            # Step 4: Add captions
            caption_data = None
            if add_captions:
                caption_data = self.caption_engine.generate_captions(current)
                captioned_path = work_dir / f"{stem}_captioned.mp4"
                self._burn_captions(current, captioned_path, caption_data["ass_path"])
                result["steps"].append("captioned")
                result["caption_data"] = {
                    "word_count": caption_data["word_count"],
                    "duration": caption_data["duration"],
                }
                current = captioned_path

            # Step 5: Add intro/outro
            if add_intro or add_outro:
                final_parts = []
                if add_intro and (TEMPLATES_DIR / "intro.mp4").exists():
                    final_parts.append(TEMPLATES_DIR / "intro.mp4")
                final_parts.append(current)
                if add_outro and (TEMPLATES_DIR / "outro.mp4").exists():
                    final_parts.append(TEMPLATES_DIR / "outro.mp4")

                if len(final_parts) > 1:
                    concat_path = work_dir / f"{stem}_concat.mp4"
                    self._concat_videos(final_parts, concat_path)
                    result["steps"].append("intro_outro")
                    current = concat_path

            # Step 6: Final export (optimized for TikTok)
            final_path = UPLOAD_QUEUE_DIR / f"{stem}_{timestamp}_READY.mp4"
            self._final_encode(current, final_path)
            result["steps"].append("exported")

            # Get final file info
            final_probe = self._probe_video(final_path)
            result["output"] = str(final_path)
            result["output_size_mb"] = round(final_path.stat().st_size / (1024 * 1024), 2)
            result["output_duration"] = final_probe.get("duration", 0)
            result["output_resolution"] = f"{final_probe.get('width', '?')}x{final_probe.get('height', '?')}"
            result["completed_at"] = datetime.now().isoformat()
            result["status"] = "ready"

            # Save processing report
            report_path = work_dir / "processing_report.json"
            report_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

            return result

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "failed"
            return result

    # ── FFmpeg Operations ────────────────────────────────────────

    def _probe_video(self, path: Path) -> dict:
        """Get video metadata using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}

        # Extract key info
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
            {},
        )
        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": float(data.get("format", {}).get("duration", 0)),
            "fps": self._parse_fps(video_stream.get("r_frame_rate", "30/1")),
            "codec": video_stream.get("codec_name", "unknown"),
            "size_mb": round(
                int(data.get("format", {}).get("size", 0)) / (1024 * 1024), 2
            ),
        }

    def _make_vertical(self, input_path: Path, output_path: Path, probe: dict):
        """Convert video to 9:16 vertical format (1080x1920)."""
        w = probe.get("width", 1920)
        h = probe.get("height", 1080)
        aspect = w / h if h > 0 else 1.78

        if aspect > 0.5625:
            # Landscape → crop to vertical (center crop)
            vf = (
                f"crop=ih*(9/16):ih,"
                f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
            )
        elif aspect < 0.5:
            # Ultra-tall → scale and pad
            vf = (
                f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
            )
        else:
            # Already roughly vertical → scale to fit
            vf = (
                f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
            )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", vf,
            "-c:v", VIDEO_CODEC,
            "-b:v", VIDEO_BITRATE,
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-r", str(VIDEO_FPS),
            "-movflags", "+faststart",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _apply_color_grade(self, input_path: Path, output_path: Path):
        """Apply cinematic color grading — warm tones for outback/earthy feel."""
        vf = (
            # Warm color grading: slight orange tint, boosted contrast
            "eq=contrast=1.1:brightness=0.02:saturation=1.2,"
            # Slight vignette for cinematic feel
            "vignette=PI/5,"
            # Subtle sharpening
            "unsharp=3:3:0.5"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", vf,
            "-c:v", VIDEO_CODEC,
            "-b:v", VIDEO_BITRATE,
            "-c:a", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _burn_captions(self, input_path: Path, output_path: Path, ass_path: str):
        """Burn ASS subtitles into the video."""
        # Escape path for FFmpeg filter (Windows backslashes)
        escaped_path = ass_path.replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", f"ass={escaped_path}",
            "-c:v", VIDEO_CODEC,
            "-b:v", VIDEO_BITRATE,
            "-c:a", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    def _concat_videos(self, parts: list[Path], output_path: Path):
        """Concatenate multiple video segments (intro + main + outro)."""
        list_file = output_path.parent / "concat_list.txt"
        lines = [f"file '{p}'" for p in parts]
        list_file.write_text("\n".join(lines), encoding="utf-8")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        list_file.unlink(missing_ok=True)

    def _final_encode(self, input_path: Path, output_path: Path):
        """Final encoding pass optimized for TikTok upload."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c:v", VIDEO_CODEC,
            "-preset", "medium",
            "-crf", "23",
            "-b:v", VIDEO_BITRATE,
            "-maxrate", "5M",
            "-bufsize", "10M",
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-ar", "44100",
            "-r", str(VIDEO_FPS),
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    # ── Utilities ────────────────────────────────────────────────

    def _parse_fps(self, fps_str: str) -> float:
        """Parse FFmpeg frame rate string like '30/1' or '29.97'."""
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                return round(float(num) / float(den), 2)
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 30.0

    def get_pending_videos(self) -> list[dict]:
        """List raw videos waiting to be processed."""
        videos = []
        for f in RAW_VIDEO_DIR.iterdir():
            if f.suffix.lower() in SUPPORTED_INPUT_FORMATS:
                probe = self._probe_video(f)
                videos.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_mb": probe.get("size_mb", 0),
                    "duration": probe.get("duration", 0),
                    "resolution": f"{probe.get('width', '?')}x{probe.get('height', '?')}",
                })
        return videos

    def get_ready_videos(self) -> list[dict]:
        """List processed videos ready for upload."""
        videos = []
        for f in UPLOAD_QUEUE_DIR.iterdir():
            if f.suffix.lower() == ".mp4" and "_READY" in f.name:
                probe = self._probe_video(f)
                videos.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_mb": probe.get("size_mb", 0),
                    "duration": probe.get("duration", 0),
                    "resolution": f"{probe.get('width', '?')}x{probe.get('height', '?')}",
                    "status": "ready",
                })
        return videos
