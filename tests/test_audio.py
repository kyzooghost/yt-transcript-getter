"""Tests for audio download functionality."""

import subprocess
from unittest.mock import patch

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
