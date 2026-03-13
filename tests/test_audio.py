"""Tests for audio download functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_check_ffmpeg_when_available():
    """check_ffmpeg returns True when ffmpeg is installed."""
    from yt_transcript_fetcher.audio import check_ffmpeg

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        assert check_ffmpeg() is True
        mock_run.assert_called_once()


def test_check_ffmpeg_when_missing():
    """check_ffmpeg returns False when ffmpeg is not installed."""
    from yt_transcript_fetcher.audio import check_ffmpeg

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        assert check_ffmpeg() is False


def test_download_audio_success(tmp_path: Path):
    """download_audio returns success tuple on successful download."""
    from yt_transcript_fetcher.audio import download_audio

    with patch("yt_transcript_fetcher.audio.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.download.return_value = 0

        success, error = download_audio(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
            tmp_path,
        )

        assert success is True
        assert error is None
        mock_ydl.download.assert_called_once()


def test_download_audio_failure(tmp_path: Path):
    """download_audio returns error tuple on failed download."""
    from yt_transcript_fetcher.audio import download_audio

    with patch("yt_transcript_fetcher.audio.yt_dlp.YoutubeDL") as mock_ydl_class:
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.download.side_effect = Exception("Video unavailable")

        success, error = download_audio(
            "https://www.youtube.com/watch?v=invalid123",
            "invalid123",
            tmp_path,
        )

        assert success is False
        assert "Video unavailable" in error
