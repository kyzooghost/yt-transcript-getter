"""Tests for transcript formatting."""

import pytest

from yt_transcript_fetcher.formatting import format_transcript_to_markdown, seconds_to_timestamp
from yt_transcript_fetcher.youtube import TranscriptSegment


class TestSecondsToTimestamp:
    """Tests for seconds_to_timestamp function."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, "00:00:00"),
            (1, "00:00:01"),
            (59, "00:00:59"),
            (60, "00:01:00"),
            (61, "00:01:01"),
            (3599, "00:59:59"),
            (3600, "01:00:00"),
            (3661, "01:01:01"),
            (7322, "02:02:02"),
            (86399, "23:59:59"),
        ],
    )
    def test_converts_seconds_to_timestamp(self, seconds: int, expected: str):
        """Given seconds, when converting to timestamp, then returns HH:MM:SS format."""
        # Act
        result = seconds_to_timestamp(seconds)

        # Assert
        assert result == expected

    def test_handles_float_seconds(self):
        """Given float seconds, when converting, then truncates to integer."""
        # Arrange
        test_cases = [
            (0.5, "00:00:00"),
            (1.9, "00:00:01"),
            (61.999, "00:01:01"),
        ]

        for seconds, expected in test_cases:
            # Act
            result = seconds_to_timestamp(seconds)

            # Assert
            assert result == expected


class TestFormatTranscriptToMarkdown:
    """Tests for format_transcript_to_markdown function."""

    def test_formats_single_segment(self):
        """Given a single segment, when formatting, then produces correct output."""
        # Arrange
        segments = [TranscriptSegment(start=0, duration=2, text="Hello world")]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        assert result == "00:00:00 Hello world"

    def test_formats_multiple_segments(self):
        """Given multiple segments, when formatting, then produces newline-separated output."""
        # Arrange
        segments = [
            TranscriptSegment(start=0, duration=2, text="First line"),
            TranscriptSegment(start=2, duration=2, text="Second line"),
            TranscriptSegment(start=4, duration=2, text="Third line"),
        ]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        expected = "00:00:00 First line\n00:00:02 Second line\n00:00:04 Third line"
        assert result == expected

    def test_handles_empty_segments(self):
        """Given no segments, when formatting, then returns empty string."""
        # Arrange
        segments = []

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        assert result == ""

    def test_handles_newlines_in_text(self):
        """Given text with newlines, when formatting, then replaces with spaces."""
        # Arrange
        segments = [TranscriptSegment(start=0, duration=2, text="Hello\nworld\ntest")]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        assert result == "00:00:00 Hello world test"

    def test_handles_whitespace_in_text(self):
        """Given text with extra whitespace, when formatting, then trims properly."""
        # Arrange
        segments = [TranscriptSegment(start=0, duration=2, text="  Hello world  ")]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        assert result == "00:00:00 Hello world"

    def test_formats_realistic_transcript(self):
        """Given realistic transcript data, when formatting, then matches expected output."""
        # Arrange - Based on example-output.md
        segments = [
            TranscriptSegment(start=0, duration=2, text="Cursor 1.0 just dropped. What does that"),
            TranscriptSegment(start=2, duration=2, text="mean for us VI coders, AI developers,"),
            TranscriptSegment(start=4, duration=3, text="chat orientated programmers, whatever"),
        ]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        expected_lines = [
            "00:00:00 Cursor 1.0 just dropped. What does that",
            "00:00:02 mean for us VI coders, AI developers,",
            "00:00:04 chat orientated programmers, whatever",
        ]
        assert result == "\n".join(expected_lines)

    def test_handles_long_timestamps(self):
        """Given timestamps over an hour, when formatting, then formats correctly."""
        # Arrange
        segments = [
            TranscriptSegment(start=3661, duration=2, text="One hour one minute one second"),
            TranscriptSegment(start=7322, duration=2, text="Two hours two minutes two seconds"),
        ]

        # Act
        result = format_transcript_to_markdown(segments)

        # Assert
        expected = "01:01:01 One hour one minute one second\n02:02:02 Two hours two minutes two seconds"
        assert result == expected
