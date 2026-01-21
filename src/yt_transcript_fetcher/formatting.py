"""Markdown formatting for transcripts."""

from yt_transcript_fetcher.youtube import TranscriptSegment


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS format.

    Args:
        seconds: Time in seconds (can be float).

    Returns:
        Formatted timestamp string (e.g., "00:01:23").
    """
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_transcript_to_markdown(segments: list[TranscriptSegment]) -> str:
    """
    Format transcript segments into Markdown format.

    The output format matches example-output.md:
    - Each line starts with a timestamp (HH:MM:SS)
    - Followed by a space and the transcript text
    - Text may wrap across multiple lines in the source but is joined

    Args:
        segments: List of TranscriptSegment objects.

    Returns:
        Formatted Markdown string.
    """
    lines = []

    for segment in segments:
        timestamp = seconds_to_timestamp(segment.start)
        # Clean up the text: replace newlines with spaces, strip whitespace
        text = segment.text.replace("\n", " ").strip()
        lines.append(f"{timestamp} {text}")

    return "\n".join(lines)
