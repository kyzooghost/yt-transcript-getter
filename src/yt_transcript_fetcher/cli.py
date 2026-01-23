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
    parser.add_argument(
        "--input-list",
        help="Path to file containing YouTube URLs (one per line)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification (use in corporate networks with proxy)",
    )

    return parser.parse_args(args)


def process_single_url(url: str, output_path: Path, lang: str | None, no_verify_ssl: bool = False) -> tuple[bool, str | None]:
    """
    Process a single YouTube URL and save transcript.

    Args:
        url: The YouTube URL.
        output_path: Path to save the transcript.
        lang: Optional language preference.
        no_verify_ssl: Whether to disable SSL verification.

    Returns:
        Tuple of (success, error_message).
    """
    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        return False, f"Could not extract video ID from URL: {url}"

    # Fetch transcript
    result, error = fetch_transcript(video_id, lang, no_verify_ssl)
    if error:
        return False, error

    if result is None:
        return False, "Failed to fetch transcript."

    # Format transcript
    markdown_content = format_transcript_to_markdown(result.segments)

    # Write to file
    try:
        output_path.write_text(markdown_content, encoding="utf-8")
    except OSError as e:
        return False, f"Could not write to file '{output_path}': {e}"

    # Success message
    transcript_type = "auto-generated" if result.is_generated else "manual"
    print(f"✓ Transcript saved to: {output_path}")
    print(f"  Language: {result.language} ({transcript_type})")
    print(f"  Segments: {len(result.segments)}")

    return True, None


def parse_input_list(file_path: Path) -> list[str]:
    """
    Parse a file containing YouTube URLs (one per line).

    Args:
        file_path: Path to the input file.

    Returns:
        List of non-empty, stripped URLs.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"Could not read input file '{file_path}': {e}")

    urls = []
    for line in content.splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith("#"):
            urls.append(line)

    return urls


def process_batch(input_file: Path, lang: str | None, no_verify_ssl: bool = False) -> int:
    """
    Process multiple YouTube URLs from a file.

    Args:
        input_file: Path to file containing URLs.
        lang: Optional language preference.
        no_verify_ssl: Whether to disable SSL verification.

    Returns:
        Exit code (0 if all succeed, 1 if any fail).
    """
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

    for video_id, url in video_id_to_url.items():
        output_path = Path(f"transcript-{video_id}.md")
        print(f"Processing: {video_id}")

        success, error = process_single_url(url, output_path, lang, no_verify_ssl)
        if success:
            success_count += 1
        else:
            failures.append((video_id, error or "Unknown error"))
            print(f"  ✗ Failed: {error}", file=sys.stderr)

        print()

    # Summary
    print("=" * 50)
    print(f"Summary: {success_count}/{unique_count} transcripts fetched successfully")

    if failures:
        print(f"\nFailed ({len(failures)}):")
        for video_id, error in failures:
            print(f"  - {video_id}: {error}")
        return 1

    return 0


def main(args: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Optional list of arguments (for testing). Uses sys.argv if None.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parsed = parse_args(args)

    # Handle batch processing mode
    if parsed.input_list:
        return process_batch(Path(parsed.input_list), parsed.lang, parsed.no_verify_ssl)

    # Get URL from either positional or flag argument
    url = parsed.url or parsed.url_flag

    if not url:
        print("Error: No YouTube URL provided.", file=sys.stderr)
        print("Usage: yt-transcript <url> [--out <path>] [--lang <code>]", file=sys.stderr)
        print("       yt-transcript --input-list <file>", file=sys.stderr)
        return 1

    # Process single URL
    success, error = process_single_url(url, Path(parsed.out), parsed.lang, parsed.no_verify_ssl)
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
