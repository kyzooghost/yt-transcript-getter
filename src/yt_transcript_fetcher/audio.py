"""YouTube audio download functionality using yt-dlp."""

import subprocess


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
