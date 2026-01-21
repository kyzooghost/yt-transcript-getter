"""Tests for transcript fetching logic with mocked API calls."""

from unittest.mock import MagicMock, patch

import pytest

from yt_transcript_fetcher.youtube import (
    TranscriptResult,
    TranscriptSegment,
    _select_transcript,
    fetch_transcript,
)


class MockTranscript:
    """Mock transcript object for testing."""

    def __init__(self, language_code: str, is_generated: bool, segments: list | None = None):
        self.language_code = language_code
        self.is_generated = is_generated
        self._segments = segments or [
            MagicMock(start=0, duration=2, text="Test transcript"),
        ]

    def fetch(self):
        return self._segments


class TestSelectTranscript:
    """Tests for _select_transcript function."""

    def test_prefers_manual_english_over_generated(self):
        """Given both manual and generated English, when selecting, then prefers manual."""
        # Arrange
        transcripts = [
            MockTranscript("en", is_generated=True),
            MockTranscript("en", is_generated=False),
        ]

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts)

        # Assert
        assert lang == "en"
        assert is_generated is False
        assert warning is None

    def test_falls_back_to_generated_english(self):
        """Given only generated English, when selecting, then uses generated."""
        # Arrange
        transcripts = [
            MockTranscript("en", is_generated=True),
            MockTranscript("es", is_generated=False),
        ]

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts)

        # Assert
        assert lang == "en"
        assert is_generated is True

    def test_prefers_manual_non_english_when_no_english(self):
        """Given no English, when selecting, then prefers manual transcript."""
        # Arrange
        transcripts = [
            MockTranscript("es", is_generated=True),
            MockTranscript("fr", is_generated=False),
        ]

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts)

        # Assert
        assert lang == "fr"
        assert is_generated is False

    def test_handles_requested_language(self):
        """Given a requested language, when selecting, then returns it if available."""
        # Arrange
        transcripts = [
            MockTranscript("en", is_generated=False),
            MockTranscript("es", is_generated=False),
        ]

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts, preferred_lang="es")

        # Assert
        assert lang == "es"
        assert warning is None

    def test_falls_back_with_warning_when_requested_not_available(self):
        """Given unavailable requested language, when selecting, then falls back with warning."""
        # Arrange
        transcripts = [
            MockTranscript("en", is_generated=False),
        ]

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts, preferred_lang="es")

        # Assert
        assert lang == "en"
        assert warning is not None
        assert "es" in warning
        assert "not available" in warning

    def test_handles_english_variants(self):
        """Given English variants, when selecting, then accepts them."""
        # Arrange
        variants = ["en-US", "en-GB", "en-AU", "en-CA"]

        for variant in variants:
            transcripts = [
                MockTranscript(variant, is_generated=False),
                MockTranscript("es", is_generated=False),
            ]

            # Act
            result, lang, is_generated, warning = _select_transcript(transcripts)

            # Assert
            assert lang == variant, f"Failed for variant: {variant}"

    def test_returns_none_for_empty_list(self):
        """Given no transcripts, when selecting, then returns None with error."""
        # Arrange
        transcripts = []

        # Act
        result, lang, is_generated, warning = _select_transcript(transcripts)

        # Assert
        assert result is None
        assert lang is None
        assert warning is not None


class TestFetchTranscript:
    """Tests for fetch_transcript function with mocked API."""

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_fetches_transcript_successfully(self, mock_api_class):
        """Given a valid video ID, when fetching, then returns transcript."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        mock_transcript = MockTranscript(
            "en",
            is_generated=False,
            segments=[
                MagicMock(start=0, duration=2, text="Hello"),
                MagicMock(start=2, duration=2, text="World"),
            ],
        )
        mock_api.list.return_value = [mock_transcript]

        # Act
        result, error = fetch_transcript("test_video_id")

        # Assert
        assert error is None
        assert result is not None
        assert isinstance(result, TranscriptResult)
        assert len(result.segments) == 2
        assert result.language == "en"
        assert result.is_generated is False

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_handles_transcripts_disabled(self, mock_api_class):
        """Given disabled transcripts, when fetching, then returns error."""
        # Arrange
        from youtube_transcript_api._errors import TranscriptsDisabled

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = TranscriptsDisabled("test_video_id")

        # Act
        result, error = fetch_transcript("test_video_id")

        # Assert
        assert result is None
        assert error is not None
        assert "disabled" in error.lower()

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_handles_video_unavailable(self, mock_api_class):
        """Given unavailable video, when fetching, then returns error."""
        # Arrange
        from youtube_transcript_api._errors import VideoUnavailable

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = VideoUnavailable("test_video_id")

        # Act
        result, error = fetch_transcript("test_video_id")

        # Assert
        assert result is None
        assert error is not None
        assert "unavailable" in error.lower()

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_handles_no_transcript_found(self, mock_api_class):
        """Given no transcript, when fetching, then returns error."""
        # Arrange
        from youtube_transcript_api._errors import NoTranscriptFound

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.list.side_effect = NoTranscriptFound(
            "test_video_id", [], None
        )

        # Act
        result, error = fetch_transcript("test_video_id")

        # Assert
        assert result is None
        assert error is not None
        assert "no transcript found" in error.lower()

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_passes_language_preference(self, mock_api_class):
        """Given language preference, when fetching, then uses it."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        mock_en = MockTranscript("en", is_generated=False)
        mock_es = MockTranscript("es", is_generated=False)
        mock_api.list.return_value = [mock_en, mock_es]

        # Act
        result, error = fetch_transcript("test_video_id", lang="es")

        # Assert
        assert error is None
        assert result is not None
        assert result.language == "es"

    @patch("yt_transcript_fetcher.youtube.YouTubeTranscriptApi")
    def test_segments_have_correct_types(self, mock_api_class):
        """Given transcript data, when fetching, then segments have correct types."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        
        mock_transcript = MockTranscript(
            "en",
            is_generated=False,
            segments=[MagicMock(start=1.5, duration=2.5, text="Test")],
        )
        mock_api.list.return_value = [mock_transcript]

        # Act
        result, error = fetch_transcript("test_video_id")

        # Assert
        assert error is None
        segment = result.segments[0]
        assert isinstance(segment, TranscriptSegment)
        assert segment.start == 1.5
        assert segment.duration == 2.5
        assert segment.text == "Test"
