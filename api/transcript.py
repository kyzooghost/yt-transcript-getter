"""Vercel serverless function for fetching YouTube transcripts with snippet splitting."""

import json
import re
import urllib3
from http.server import BaseHTTPRequestHandler
from typing import NamedTuple

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


class TranscriptSegment(NamedTuple):
    """A single segment of a transcript."""

    start: float
    duration: float
    text: str


def extract_video_id(url: str) -> str | None:
    """
    Extract the video ID from various YouTube URL formats.

    Supported formats:
    - https://youtu.be/<id>
    - https://www.youtube.com/watch?v=<id>
    - https://www.youtube.com/live/<id>
    - URLs with extra query params (timestamps, playlists, etc.)

    Returns None if no valid video ID is found.
    """
    url = url.strip()

    # Pattern for youtu.be short URLs
    short_url_pattern = r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})"

    # Pattern for youtube.com/watch?v= URLs
    watch_pattern = r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})"

    # Pattern for youtube.com/live/ URLs
    live_pattern = r"(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})"

    # Pattern for youtube.com/embed/ URLs
    embed_pattern = r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"

    # Pattern for youtube.com/v/ URLs
    v_pattern = r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})"

    for pattern in [short_url_pattern, watch_pattern, live_pattern, embed_pattern, v_pattern]:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


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


def _select_transcript(transcripts, preferred_lang: str | None = None):
    """
    Select the best transcript based on language preference rules.

    Language selection rules:
    - Default behavior (no preferred_lang):
      1. Prefer manually-created transcripts in English (en, en-US, en-GB).
      2. If not available, prefer auto-generated English.
      3. If no English, pick the first available transcript (manual preferred over generated).
    - If preferred_lang is provided:
      - Attempt exact match first; if not available, fallback to default behavior.

    Returns tuple of (transcript, language_code, is_generated, warning_message).
    """
    transcript_list = list(transcripts)
    warning = None

    # Build lists of available transcripts
    manual_transcripts = {}
    generated_transcripts = {}

    for t in transcript_list:
        if t.is_generated:
            generated_transcripts[t.language_code] = t
        else:
            manual_transcripts[t.language_code] = t

    # If a specific language is requested, try to find it
    if preferred_lang:
        # Try exact match in manual first
        if preferred_lang in manual_transcripts:
            t = manual_transcripts[preferred_lang]
            return t, t.language_code, t.is_generated, None

        # Try exact match in generated
        if preferred_lang in generated_transcripts:
            t = generated_transcripts[preferred_lang]
            return t, t.language_code, t.is_generated, None

        # Language not found, fall back to default with warning
        warning = f"Requested language '{preferred_lang}' not available. Falling back to default selection."

    # Default language selection
    english_codes = ["en", "en-US", "en-GB", "en-AU", "en-CA"]

    # 1. Prefer manual English
    for code in english_codes:
        if code in manual_transcripts:
            t = manual_transcripts[code]
            return t, t.language_code, t.is_generated, warning

    # 2. Prefer auto-generated English
    for code in english_codes:
        if code in generated_transcripts:
            t = generated_transcripts[code]
            return t, t.language_code, t.is_generated, warning

    # 3. Pick first available (manual preferred)
    if manual_transcripts:
        t = next(iter(manual_transcripts.values()))
        return t, t.language_code, t.is_generated, warning

    if generated_transcripts:
        t = next(iter(generated_transcripts.values()))
        return t, t.language_code, t.is_generated, warning

    return None, None, None, "No transcripts available."


def fetch_transcript(video_id: str, lang: str | None = None):
    """
    Fetch the transcript for a YouTube video.

    Args:
        video_id: The YouTube video ID.
        lang: Optional language code to prefer.

    Returns:
        Tuple of (segments, language, is_generated, error_message).
        On success, error_message is None.
        On failure, segments is None and error_message contains the error.
    """
    # Disable SSL warnings for serverless environment
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
    except TranscriptsDisabled:
        return None, None, None, f"Transcripts are disabled for video '{video_id}'."
    except VideoUnavailable:
        return None, None, None, f"Video '{video_id}' is unavailable."
    except NoTranscriptFound:
        return None, None, None, f"No transcript found for video '{video_id}'."
    except Exception as e:
        return None, None, None, f"Failed to fetch transcript: {e}"

    transcript, language, is_generated, warning = _select_transcript(transcript_list, lang)

    if transcript is None:
        return None, None, None, "No suitable transcript found."

    try:
        raw_segments = transcript.fetch()
    except Exception as e:
        return None, None, None, f"Failed to fetch transcript content: {e}"

    segments = [
        TranscriptSegment(
            start=seg.start,
            duration=seg.duration,
            text=seg.text,
        )
        for seg in raw_segments
    ]

    return segments, language, is_generated, None


def find_sentence_boundary(segments: list[TranscriptSegment], start_offset_time: float, target_duration: float, window: float = 120.0) -> int:
    """
    Find the best sentence boundary near a target time.

    Args:
        segments: List of transcript segments to search within
        start_offset_time: Start time of the current snippet
        target_duration: Target duration in seconds from start_offset_time (e.g., 1200 for 20 minutes)
        window: Search window in seconds (±2 minutes = 120 seconds)

    Returns:
        Index of the segment to split at (next snippet starts at this index)
    """
    target_time = start_offset_time + target_duration
    min_time = target_time - window
    max_time = target_time + window

    # Find segments within the window
    candidates = []
    for i, segment in enumerate(segments):
        if min_time <= segment.start <= max_time:
            # Check if text ends with sentence boundary
            text = segment.text.strip()
            if text and text[-1] in ".!?":
                # Calculate distance from target
                distance = abs(segment.start - target_time)
                candidates.append((distance, i))

    if candidates:
        # Return the closest sentence boundary to target
        candidates.sort()
        return candidates[0][1] + 1  # Split after this segment

    # No sentence boundary found, split at closest segment to target
    closest_idx = 0
    min_distance = float("inf")
    for i, segment in enumerate(segments):
        distance = abs(segment.start - target_time)
        if distance < min_distance:
            min_distance = distance
            closest_idx = i

    return closest_idx if closest_idx > 0 else 1  # Ensure we always advance at least 1 segment


def split_into_snippets(segments: list[TranscriptSegment], target_minutes: int = 20, variance_minutes: int = 2):
    """
    Split transcript segments into snippets of approximately target_minutes duration.

    Attempts to split at sentence boundaries within ±variance_minutes of target.

    Args:
        segments: List of transcript segments
        target_minutes: Target duration for each snippet in minutes
        variance_minutes: Allowed variance in minutes (±)

    Returns:
        List of snippet dictionaries with metadata
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

        # If we're near the end, just include everything remaining
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

        # Find the best split point
        split_idx = find_sentence_boundary(segments, current_start_time, target_seconds, variance_seconds)

        # Extract snippet
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


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            url = data.get("url", "").strip()
            if not url:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {"success": False, "error": "URL is required.", "suggestion": "Please provide a YouTube URL."}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            # Extract video ID
            video_id = extract_video_id(url)
            if not video_id:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {
                    "success": False,
                    "error": f"Invalid YouTube URL: {url}",
                    "suggestion": "Please provide a valid YouTube video URL (e.g., youtube.com/watch?v=... or youtu.be/...)",
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            # Fetch transcript
            segments, language, is_generated, error = fetch_transcript(video_id)
            if error:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {"success": False, "error": error, "suggestion": get_error_suggestion(error)}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            # Split into snippets
            snippets = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

            # Format full transcript
            full_transcript = format_transcript_to_markdown(segments)

            # Success response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response = {
                "success": True,
                "video_id": video_id,
                "language": language,
                "is_generated": is_generated,
                "snippets": snippets,
                "full_transcript": full_transcript,
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            response = {"success": False, "error": f"Internal server error: {str(e)}", "suggestion": "Please try again later."}
            self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
