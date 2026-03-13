"""YouTube audio download functionality using yt-dlp."""

import argparse
import subprocess
import sys
from pathlib import Path

import yt_dlp

from yt_transcript_fetcher.cli import parse_input_list
from yt_transcript_fetcher.youtube import extract_video_id


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


def process_batch(input_file: Path, no_verify_ssl: bool = False) -> int:
    """
    Process multiple YouTube URLs from a file.

    Args:
        input_file: Path to file containing URLs.
        no_verify_ssl: Whether to disable SSL verification.

    Returns:
        Exit code (0 if all succeed, 1 if any fail).
    """
    # Check ffmpeg first
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not in PATH.", file=sys.stderr)
        print("Install ffmpeg: https://ffmpeg.org/download.html", file=sys.stderr)
        return 1

    # Parse input file
    try:
        urls = parse_input_list(input_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not urls:
        print("Error: No URLs found in input file.", file=sys.stderr)
        return 1

    # Extract video IDs and deduplicate
    video_id_to_url: dict[str, str] = {}
    skipped_invalid = 0
    skipped_duplicates = 0

    for url in urls:
        video_id = extract_video_id(url)
        if not video_id:
            print(f"Warning: Skipping invalid URL: {url}", file=sys.stderr)
            skipped_invalid += 1
            continue

        if video_id in video_id_to_url:
            skipped_duplicates += 1
            continue

        video_id_to_url[video_id] = url

    if not video_id_to_url:
        print("Error: No valid URLs to process.", file=sys.stderr)
        return 1

    # Report deduplication
    total_urls = len(urls)
    unique_count = len(video_id_to_url)
    print(f"Found {total_urls} URLs, processing {unique_count} unique videos")
    if skipped_duplicates > 0:
        print(f"  Skipped {skipped_duplicates} duplicate(s)")
    if skipped_invalid > 0:
        print(f"  Skipped {skipped_invalid} invalid URL(s)")
    print()

    # Process each unique video
    success_count = 0
    failures: list[tuple[str, str]] = []

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    for video_id, url in video_id_to_url.items():
        print(f"Downloading: {video_id}")

        success, error = download_audio(url, video_id, output_dir)
        if success:
            success_count += 1
            print(f"  Saved to: output/audio-{video_id}.mp3")
        else:
            failures.append((video_id, error or "Unknown error"))
            print(f"  Failed: {error}", file=sys.stderr)

        print()

    # Summary
    print("=" * 50)
    print(f"Summary: {success_count}/{unique_count} audio files downloaded successfully")

    if failures:
        print(f"\nFailed ({len(failures)}):")
        for video_id, error in failures:
            print(f"  - {video_id}: {error}")
        return 1

    return 0


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="yt-audio",
        description="Download YouTube video audio as MP3 files.",
    )

    parser.add_argument(
        "--input-list",
        required=True,
        help="Path to file containing YouTube URLs (one per line)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification (use in corporate networks with proxy)",
    )

    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Optional list of arguments (for testing). Uses sys.argv if None.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parsed = parse_args(args)
    return process_batch(Path(parsed.input_list), parsed.no_verify_ssl)


if __name__ == "__main__":
    sys.exit(main())
