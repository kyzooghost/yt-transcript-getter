"""Command-line interface for YouTube Transcript Fetcher."""

import argparse
import sys
from pathlib import Path

from yt_transcript_fetcher.formatting import format_transcript_to_markdown
from yt_transcript_fetcher.youtube import extract_video_id, fetch_transcript


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="yt-transcript",
        description="Fetch YouTube video transcripts and save them as Markdown files.",
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube video URL",
    )
    parser.add_argument(
        "--url",
        dest="url_flag",
        help="YouTube video URL (alternative to positional argument)",
    )
    parser.add_argument(
        "--out",
        "-o",
        default="transcript.md",
        help="Output file path (default: transcript.md)",
    )
    parser.add_argument(
        "--lang",
        "-l",
        help="Preferred language code (e.g., 'en', 'es', 'fr')",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "md"],
        default="markdown",
        help="Output format (default: markdown)",
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

    # Get URL from either positional or flag argument
    url = parsed.url or parsed.url_flag

    if not url:
        print("Error: No YouTube URL provided.", file=sys.stderr)
        print("Usage: yt-transcript <url> [--out <path>] [--lang <code>]", file=sys.stderr)
        return 1

    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {url}", file=sys.stderr)
        print("Supported URL formats:", file=sys.stderr)
        print("  - https://youtu.be/<id>", file=sys.stderr)
        print("  - https://www.youtube.com/watch?v=<id>", file=sys.stderr)
        print("  - https://www.youtube.com/live/<id>", file=sys.stderr)
        return 1

    # Fetch transcript
    result, error = fetch_transcript(video_id, parsed.lang)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if result is None:
        print("Error: Failed to fetch transcript.", file=sys.stderr)
        return 1

    # Format transcript
    markdown_content = format_transcript_to_markdown(result.segments)

    # Write to file
    output_path = Path(parsed.out)
    try:
        output_path.write_text(markdown_content, encoding="utf-8")
    except OSError as e:
        print(f"Error: Could not write to file '{output_path}': {e}", file=sys.stderr)
        return 1

    # Success message
    transcript_type = "auto-generated" if result.is_generated else "manual"
    print(f"✓ Transcript saved to: {output_path}")
    print(f"  Language: {result.language} ({transcript_type})")
    print(f"  Segments: {len(result.segments)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
