"""Tests for YouTube URL parsing and video ID extraction."""

import pytest

from yt_transcript_fetcher.youtube import extract_video_id


class TestExtractVideoId:
    """Tests for extract_video_id function."""

    @pytest.mark.parametrize(
        "url,expected_id",
        [
            # Standard youtu.be short URLs
            ("https://youtu.be/7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("http://youtu.be/7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("youtu.be/7wWRoqC0gnU", "7wWRoqC0gnU"),
            # Standard watch URLs
            ("https://www.youtube.com/watch?v=7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("https://youtube.com/watch?v=7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("http://www.youtube.com/watch?v=7wWRoqC0gnU", "7wWRoqC0gnU"),
            # Live URLs
            ("https://www.youtube.com/live/7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("https://youtube.com/live/7wWRoqC0gnU", "7wWRoqC0gnU"),
            # Embed URLs
            ("https://www.youtube.com/embed/7wWRoqC0gnU", "7wWRoqC0gnU"),
            # URLs with extra query params
            ("https://www.youtube.com/watch?v=7wWRoqC0gnU&t=120", "7wWRoqC0gnU"),
            ("https://www.youtube.com/watch?v=7wWRoqC0gnU&list=PLxyz", "7wWRoqC0gnU"),
            ("https://www.youtube.com/watch?list=PLxyz&v=7wWRoqC0gnU", "7wWRoqC0gnU"),
            ("https://youtu.be/7wWRoqC0gnU?t=60", "7wWRoqC0gnU"),
            ("https://youtu.be/7wWRoqC0gnU?si=abcdef123456", "7wWRoqC0gnU"),
            # URLs with whitespace (should be stripped)
            ("  https://youtu.be/7wWRoqC0gnU  ", "7wWRoqC0gnU"),
        ],
    )
    def test_extracts_video_id_from_valid_urls(self, url: str, expected_id: str):
        """Given a valid YouTube URL, when extracting video ID, then returns the correct ID."""
        # Act
        result = extract_video_id(url)

        # Assert
        assert result == expected_id

    @pytest.mark.parametrize(
        "url",
        [
            # Invalid URLs
            "",
            "not a url",
            "https://example.com/watch?v=7wWRoqC0gnU",
            "https://vimeo.com/123456789",
            # Invalid video IDs (too short)
            "https://youtu.be/short",
            # Missing video ID
            "https://www.youtube.com/watch?v=",
            "https://www.youtube.com/watch?list=PLxyz",
            "https://youtu.be/",
        ],
    )
    def test_returns_none_for_invalid_urls(self, url: str):
        """Given an invalid URL, when extracting video ID, then returns None."""
        # Act
        result = extract_video_id(url)

        # Assert
        assert result is None

    def test_handles_various_video_id_characters(self):
        """Given video IDs with various valid characters, when extracting, then succeeds."""
        # Arrange - Video IDs can contain letters, numbers, underscores, and hyphens
        test_cases = [
            ("https://youtu.be/abc123ABC-_", "abc123ABC-_"),
            ("https://youtu.be/ABCDEFGHIJK", "ABCDEFGHIJK"),
            ("https://youtu.be/12345678901", "12345678901"),
            ("https://youtu.be/___________", "___________"),
            ("https://youtu.be/-----------", "-----------"),
        ]

        for url, expected_id in test_cases:
            # Act
            result = extract_video_id(url)

            # Assert
            assert result == expected_id, f"Failed for URL: {url}"
