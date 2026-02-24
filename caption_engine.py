"""
DIDGERI-BOOM Caption Engine
Auto-generates captions from video audio using Whisper AI.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from config import WHISPER_MODEL


class CaptionEngine:
    """Generates captions/subtitles from video audio using Whisper."""

    def __init__(self, model_size: str = WHISPER_MODEL):
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                )
            except ImportError:
                print("[CAPTION] faster-whisper not installed. Captions disabled.")
                return None
        return self._model

    def extract_audio(self, video_path: Path, output_path: Optional[Path] = None) -> Path:
        """Extract audio track from video using FFmpeg."""
        if output_path is None:
            output_path = video_path.with_suffix(".wav")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # 16kHz for Whisper
            "-ac", "1",  # Mono
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    def transcribe(self, audio_path: Path) -> list[dict]:
        """Transcribe audio to text segments with timestamps."""
        model = self._load_model()
        if model is None:
            return self._get_instrumental_captions()

        try:
            segments, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
            )

            result = []
            for segment in segments:
                seg_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "words": [],
                }
                if segment.words:
                    for word in segment.words:
                        seg_data["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        })
                result.append(seg_data)

            # If very little speech detected, add instrumental captions
            total_text = " ".join(s["text"] for s in result).strip()
            if len(total_text) < 10:
                result = self._get_instrumental_captions()

            return result

        except Exception as e:
            print(f"[CAPTION] Transcription error: {e}")
            return self._get_instrumental_captions()

    def generate_srt(self, segments: list[dict], output_path: Path) -> Path:
        """Generate an SRT subtitle file from transcription segments."""
        lines = []
        for i, seg in enumerate(segments, 1):
            start_time = self._format_srt_time(seg["start"])
            end_time = self._format_srt_time(seg["end"])
            text = seg["text"]

            lines.append(f"{i}")
            lines.append(f"{start_time} --> {end_time}")
            lines.append(text)
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def generate_ass(self, segments: list[dict], output_path: Path) -> Path:
        """Generate an ASS subtitle file with TikTok-style animated captions."""
        header = (
            "[Script Info]\n"
            "Title: DIDGERI-BOOM Captions\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1080\n"
            "PlayResY: 1920\n"
            "WrapStyle: 0\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: TikTok,Arial Black,72,&H00FFFFFF,&H000000FF,"
            "&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,0,"
            "2,40,40,200,1\n"
            "Style: TikTokGlow,Arial Black,72,&H0000D4FF,&H000000FF,"
            "&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,"
            "2,40,40,200,1\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
            "MarginV, Effect, Text\n"
        )

        events = []
        for seg in segments:
            start = self._format_ass_time(seg["start"])
            end = self._format_ass_time(seg["end"])
            text = seg["text"].upper()

            # Glow background layer
            events.append(
                f"Dialogue: 0,{start},{end},TikTokGlow,,0,0,0,,{text}"
            )
            # Main text layer
            events.append(
                f"Dialogue: 1,{start},{end},TikTok,,0,0,0,,{text}"
            )

        content = header + "\n".join(events) + "\n"
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def generate_captions(self, video_path: Path) -> dict:
        """Full pipeline: video → audio → transcribe → subtitle files."""
        audio_path = self.extract_audio(video_path)

        try:
            segments = self.transcribe(audio_path)

            srt_path = video_path.with_suffix(".srt")
            ass_path = video_path.with_suffix(".ass")

            self.generate_srt(segments, srt_path)
            self.generate_ass(segments, ass_path)

            return {
                "segments": segments,
                "srt_path": str(srt_path),
                "ass_path": str(ass_path),
                "word_count": sum(len(s["text"].split()) for s in segments),
                "duration": segments[-1]["end"] if segments else 0,
            }
        finally:
            # Clean up temp audio
            if audio_path.exists():
                audio_path.unlink()

    # ── Helpers ──────────────────────────────────────────────────

    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _format_ass_time(self, seconds: float) -> str:
        """Format seconds to ASS timestamp: H:MM:SS.cc"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def _get_instrumental_captions(self) -> list[dict]:
        """Generate captions for instrumental/non-speech content."""
        return [
            {"start": 0.0, "end": 3.0, "text": "🎵 Didgeridoo Vibes 🎵", "words": []},
            {"start": 3.0, "end": 6.0, "text": "🔊 Feel the Drone 🔊", "words": []},
        ]
