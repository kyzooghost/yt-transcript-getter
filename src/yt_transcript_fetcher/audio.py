"""YouTube audio download functionality using yt-dlp."""

import subprocess
from pathlib import Path

import yt_dlp


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is available on PATH.

    Returns:
        True if ffmpeg is available, False otherwise.
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=False,
        )
        return True
    except FileNotFoundError:
        return False


def download_audio(url: str, video_id: str, output_dir: Path) -> tuple[bool, str | None]:
    """
    Download audio from YouTube URL as MP3.

    Args:
        url: The YouTube URL.
        video_id: The video ID (for output filename).
        output_dir: Directory to save the audio file.

    Returns:
        Tuple of (success, error_message).
    """
    output_template = str(output_dir / f"audio-{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, None
    except Exception as e:
        return False, str(e)
