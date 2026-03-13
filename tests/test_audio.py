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


def test_process_batch_deduplicates_urls(tmp_path: Path):
    """process_batch deduplicates URLs by video ID."""
    from yt_transcript_fetcher.audio import process_batch

    # Create input file with duplicate URLs
    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "https://www.youtube.com/watch?v=abc12345678\n"
        "https://youtu.be/abc12345678\n"  # duplicate
        "https://www.youtube.com/watch?v=xyz98765432\n"
    )

    with patch("yt_transcript_fetcher.audio.download_audio") as mock_download:
        mock_download.return_value = (True, None)
        with patch("yt_transcript_fetcher.audio.check_ffmpeg", return_value=True):
            process_batch(input_file)

        # Should only call download twice (deduplicated)
        assert mock_download.call_count == 2


def test_process_batch_skips_invalid_urls(tmp_path: Path):
    """process_batch skips invalid URLs."""
    from yt_transcript_fetcher.audio import process_batch

    input_file = tmp_path / "urls.txt"
    input_file.write_text(
        "https://www.youtube.com/watch?v=abc12345678\n"
        "not-a-valid-url\n"
        "https://example.com/video\n"
    )

    with patch("yt_transcript_fetcher.audio.download_audio") as mock_download:
        mock_download.return_value = (True, None)
        with patch("yt_transcript_fetcher.audio.check_ffmpeg", return_value=True):
            process_batch(input_file)

        # Should only call download once (only one valid URL)
        assert mock_download.call_count == 1


def test_parse_args_input_list():
    """parse_args correctly parses --input-list argument."""
    from yt_transcript_fetcher.audio import parse_args

    args = parse_args(["--input-list", "urls.txt"])
    assert args.input_list == "urls.txt"
    assert args.no_verify_ssl is False


def test_parse_args_no_verify_ssl():
    """parse_args correctly parses --no-verify-ssl flag."""
    from yt_transcript_fetcher.audio import parse_args

    args = parse_args(["--input-list", "urls.txt", "--no-verify-ssl"])
    assert args.input_list == "urls.txt"
    assert args.no_verify_ssl is True
