"""YouTube video ID extraction and transcript fetching logic."""

import re
import sys
import urllib3
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


class TranscriptResult(NamedTuple):
    """Result of fetching a transcript."""

    segments: list[TranscriptSegment]
    language: str
    is_generated: bool


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


def fetch_transcript(video_id: str, lang: str | None = None, no_verify_ssl: bool = False) -> tuple[TranscriptResult | None, str | None]:
    """
    Fetch the transcript for a YouTube video.

    Args:
        video_id: The YouTube video ID.
        lang: Optional language code to prefer.
        no_verify_ssl: Whether to disable SSL certificate verification.

    Returns:
        Tuple of (TranscriptResult or None, error_message or None).
        On success, error_message is None (though there may be a warning printed).
        On failure, TranscriptResult is None and error_message contains the error.
    """
    # Create custom session if SSL verification needs to be disabled
    http_client = None
    if no_verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        from requests import Session
        http_client = Session()
        http_client.verify = False

    try:
        ytt_api = YouTubeTranscriptApi(http_client=http_client)
        transcript_list = ytt_api.list(video_id)
    except TranscriptsDisabled:
        return None, f"Transcripts are disabled for video '{video_id}'."
    except VideoUnavailable:
        return None, f"Video '{video_id}' is unavailable."
    except NoTranscriptFound:
        return None, f"No transcript found for video '{video_id}'."
    except Exception as e:
        return None, f"Failed to fetch transcript: {e}"

    transcript, language, is_generated, warning = _select_transcript(transcript_list, lang)

    if warning:
        print(f"Warning: {warning}", file=sys.stderr)

    if transcript is None:
        return None, "No suitable transcript found."

    try:
        raw_segments = transcript.fetch()
    except Exception as e:
        return None, f"Failed to fetch transcript content: {e}"

    segments = [
        TranscriptSegment(
            start=seg.start,
            duration=seg.duration,
            text=seg.text,
        )
        for seg in raw_segments
    ]

    return TranscriptResult(segments=segments, language=language, is_generated=is_generated), None
