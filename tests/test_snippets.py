"""Tests for snippet splitting and error suggestion logic."""

import pytest

from yt_transcript_fetcher.formatting import (
    find_sentence_boundary,
    get_error_suggestion,
    split_into_snippets,
)
from yt_transcript_fetcher.youtube import TranscriptSegment


def _make_segments(count: int, interval: float = 10.0, sentence_every: int = 20) -> list[TranscriptSegment]:
    """Helper to create mock transcript segments.

    Args:
        count: Number of segments to create.
        interval: Duration of each segment in seconds.
        sentence_every: End text with a period every N segments.
    """
    segments = []
    for i in range(count):
        text = f"This is segment {i}." if (i + 1) % sentence_every == 0 else f"This is segment {i}"
        segments.append(TranscriptSegment(start=i * interval, duration=interval, text=text))
    return segments


class TestFindSentenceBoundary:
    """Tests for find_sentence_boundary function."""

    def test_finds_closest_sentence_boundary(self):
        """Given segments with sentence endings, returns the one nearest to target."""
        # Arrange - 100 segments, 10s each, sentence at segment 19 (190s) and 39 (390s)
        segments = _make_segments(100, interval=10.0, sentence_every=20)

        # Act - target at 200s from start 0, window 120s
        result = find_sentence_boundary(segments, start_offset_time=0, target_duration=200, window=120)

        # Assert - segment 19 ends with period at 190s, closest to target 200s
        assert result == 20  # split after index 19

    def test_falls_back_to_closest_segment_when_no_sentence_boundary(self):
        """Given no sentence endings in window, returns closest segment to target."""
        # Arrange - no sentences at all
        segments = [TranscriptSegment(start=i * 10, duration=10, text=f"Word {i}") for i in range(50)]

        # Act
        result = find_sentence_boundary(segments, start_offset_time=0, target_duration=200, window=120)

        # Assert - closest to 200s is segment at index 20 (start=200)
        assert result == 20

    def test_always_advances_at_least_one_segment(self):
        """Given target at start, returns at least index 1 to avoid infinite loop."""
        # Arrange
        segments = [TranscriptSegment(start=i * 10, duration=10, text=f"Word {i}") for i in range(5)]

        # Act - target at 0s
        result = find_sentence_boundary(segments, start_offset_time=0, target_duration=0, window=0)

        # Assert
        assert result >= 1


class TestSplitIntoSnippets:
    """Tests for split_into_snippets function."""

    def test_returns_empty_for_empty_segments(self):
        """Given no segments, returns empty list."""
        # Act
        result = split_into_snippets([])

        # Assert
        assert result == []

    def test_short_transcript_produces_single_snippet(self):
        """Given a transcript shorter than target, returns one snippet."""
        # Arrange - 5 minutes of segments (30 segments * 10s)
        segments = _make_segments(30, interval=10.0)

        # Act
        result = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

        # Assert
        assert len(result) == 1
        assert result[0]["index"] == 1

    def test_long_transcript_splits_into_multiple_snippets(self):
        """Given a 65-minute transcript, splits into multiple ~20-minute snippets."""
        # Arrange - 390 segments * 10s = 65 minutes
        segments = _make_segments(390, interval=10.0, sentence_every=20)

        # Act
        result = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

        # Assert
        assert len(result) >= 3
        for snippet in result:
            assert "index" in snippet
            assert "start_time" in snippet
            assert "end_time" in snippet
            assert "markdown" in snippet
            assert "duration_minutes" in snippet

    def test_snippets_are_sequential_and_non_overlapping(self):
        """Given a long transcript, snippets cover the full duration without gaps."""
        # Arrange
        segments = _make_segments(390, interval=10.0, sentence_every=20)

        # Act
        result = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

        # Assert - indices are sequential starting from 1
        for i, snippet in enumerate(result):
            assert snippet["index"] == i + 1

    def test_snippet_durations_are_near_target(self):
        """Given target of 20 minutes, each snippet duration is roughly 18-22 minutes."""
        # Arrange
        segments = _make_segments(390, interval=10.0, sentence_every=20)

        # Act
        result = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

        # Assert - all but last snippet should be near target
        for snippet in result[:-1]:
            assert 15 <= snippet["duration_minutes"] <= 25

    def test_respects_custom_target_minutes(self):
        """Given target of 10 minutes, produces more snippets than 20-minute target."""
        # Arrange - 120 minutes of content for clear difference
        segments = _make_segments(720, interval=10.0, sentence_every=20)

        # Act
        result_10 = split_into_snippets(segments, target_minutes=10, variance_minutes=2)
        result_20 = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

        # Assert
        assert len(result_10) > len(result_20)

    def test_snippets_contain_valid_markdown(self):
        """Given segments, each snippet's markdown contains timestamps."""
        # Arrange
        segments = _make_segments(60, interval=10.0)

        # Act
        result = split_into_snippets(segments, target_minutes=5, variance_minutes=1)

        # Assert
        for snippet in result:
            assert len(snippet["markdown"]) > 0
            assert "00:" in snippet["markdown"]


class TestGetErrorSuggestion:
    """Tests for get_error_suggestion function."""

    @pytest.mark.parametrize(
        "error_message,expected_substring",
        [
            ("Transcripts are disabled", "captions disabled"),
            ("Video is unavailable", "private, deleted, or region-restricted"),
            ("No transcript found", "not have any available transcripts"),
            ("Invalid YouTube URL", "valid YouTube video link"),
            ("Something unexpected happened", "check the URL and try again"),
        ],
    )
    def test_returns_relevant_suggestion(self, error_message: str, expected_substring: str):
        """Given an error message, returns a suggestion containing the expected text."""
        # Act
        result = get_error_suggestion(error_message)

        # Assert
        assert expected_substring in result
