"""Markdown formatting and snippet splitting for transcripts."""

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


def find_sentence_boundary(
    segments: list[TranscriptSegment],
    start_offset_time: float,
    target_duration: float,
    window: float = 120.0,
) -> int:
    """
    Find the best sentence boundary near a target time.

    Searches within +/- window seconds of the target split point for a segment
    ending with sentence-terminal punctuation (.!?), returning the closest match.

    Returns:
        Index of the segment to split at (next snippet starts at this index).
    """
    target_time = start_offset_time + target_duration
    min_time = target_time - window
    max_time = target_time + window

    candidates = []
    for i, segment in enumerate(segments):
        if min_time <= segment.start <= max_time:
            text = segment.text.strip()
            if text and text[-1] in ".!?":
                distance = abs(segment.start - target_time)
                candidates.append((distance, i))

    if candidates:
        candidates.sort()
        return candidates[0][1] + 1

    # No sentence boundary found, split at closest segment to target
    closest_idx = 0
    min_distance = float("inf")
    for i, segment in enumerate(segments):
        distance = abs(segment.start - target_time)
        if distance < min_distance:
            min_distance = distance
            closest_idx = i

    return closest_idx if closest_idx > 0 else 1


def split_into_snippets(
    segments: list[TranscriptSegment],
    target_minutes: int = 20,
    variance_minutes: int = 2,
) -> list[dict]:
    """
    Split transcript segments into snippets of approximately target_minutes duration.

    Attempts to split at sentence boundaries within +/- variance_minutes of target.

    Returns:
        List of snippet dicts with keys: index, start_time, end_time, markdown, duration_minutes.
    """
    if not segments:
        return []

    target_seconds = target_minutes * 60
    variance_seconds = variance_minutes * 60
    total_duration = segments[-1].start + segments[-1].duration

    snippets = []
    current_start_idx = 0
    snippet_index = 1

    while current_start_idx < len(segments):
        current_start_time = segments[current_start_idx].start
        target_end_time = current_start_time + target_seconds

        # If near the end, include everything remaining
        if target_end_time + variance_seconds >= total_duration:
            snippet_segments = segments[current_start_idx:]
            snippet_markdown = format_transcript_to_markdown(snippet_segments)
            snippet_duration = (segments[-1].start + segments[-1].duration) - current_start_time

            snippets.append(
                {
                    "index": snippet_index,
                    "start_time": seconds_to_timestamp(current_start_time),
                    "end_time": seconds_to_timestamp(segments[-1].start + segments[-1].duration),
                    "markdown": snippet_markdown,
                    "duration_minutes": round(snippet_duration / 60, 2),
                }
            )
            break

        split_idx = find_sentence_boundary(segments, current_start_time, target_seconds, variance_seconds)

        snippet_segments = segments[current_start_idx:split_idx]
        if not snippet_segments:
            break

        snippet_markdown = format_transcript_to_markdown(snippet_segments)
        snippet_end_time = snippet_segments[-1].start + snippet_segments[-1].duration
        snippet_duration = snippet_end_time - current_start_time

        snippets.append(
            {
                "index": snippet_index,
                "start_time": seconds_to_timestamp(current_start_time),
                "end_time": seconds_to_timestamp(snippet_end_time),
                "markdown": snippet_markdown,
                "duration_minutes": round(snippet_duration / 60, 2),
            }
        )

        snippet_index += 1
        current_start_idx = split_idx

    return snippets


def get_error_suggestion(error_message: str) -> str:
    """Generate a helpful suggestion based on the error message."""
    if "disabled" in error_message.lower():
        return "The video may have captions disabled by the creator."
    elif "unavailable" in error_message.lower():
        return "The video may be private, deleted, or region-restricted."
    elif "not found" in error_message.lower() or "no transcript" in error_message.lower():
        return "The video may not have any available transcripts/captions."
    elif "invalid" in error_message.lower():
        return "Please check that the URL is a valid YouTube video link."
    else:
        return "Please check the URL and try again."
