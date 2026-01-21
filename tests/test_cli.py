"""Tests for CLI functionality including batch processing."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_transcript_fetcher.cli import (
    main,
    parse_args,
    parse_input_list,
    process_batch,
    process_single_url,
)
from yt_transcript_fetcher.youtube import TranscriptResult, TranscriptSegment


class TestParseArgs:
    """Tests for argument parsing."""

    def test_parses_positional_url(self):
        """Given a positional URL, when parsing, then captures it."""
        # Arrange & Act
        args = parse_args(["https://youtu.be/abc123def45"])

        # Assert
        assert args.url == "https://youtu.be/abc123def45"

    def test_parses_url_flag(self):
        """Given --url flag, when parsing, then captures it."""
        # Arrange & Act
        args = parse_args(["--url", "https://youtu.be/abc123def45"])

        # Assert
        assert args.url_flag == "https://youtu.be/abc123def45"

    def test_parses_input_list_flag(self):
        """Given --input-list flag, when parsing, then captures it."""
        # Arrange & Act
        args = parse_args(["--input-list", "urls.txt"])

        # Assert
        assert args.input_list == "urls.txt"

    def test_parses_lang_flag(self):
        """Given --lang flag, when parsing, then captures it."""
        # Arrange & Act
        args = parse_args(["https://youtu.be/abc123def45", "--lang", "es"])

        # Assert
        assert args.lang == "es"


class TestParseInputList:
    """Tests for input list file parsing."""

    def test_parses_urls_from_file(self):
        """Given a file with URLs, when parsing, then returns list of URLs."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.write("https://youtu.be/xyz789ghi01\n")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            urls = parse_input_list(file_path)

            # Assert
            assert urls == [
                "https://youtu.be/abc123def45",
                "https://youtu.be/xyz789ghi01",
            ]
        finally:
            file_path.unlink()

    def test_skips_empty_lines(self):
        """Given a file with empty lines, when parsing, then skips them."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.write("\n")
            f.write("  \n")
            f.write("https://youtu.be/xyz789ghi01\n")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            urls = parse_input_list(file_path)

            # Assert
            assert len(urls) == 2
        finally:
            file_path.unlink()

    def test_skips_comment_lines(self):
        """Given a file with comments, when parsing, then skips them."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("https://youtu.be/abc123def45\n")
            f.write("# Another comment\n")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            urls = parse_input_list(file_path)

            # Assert
            assert urls == ["https://youtu.be/abc123def45"]
        finally:
            file_path.unlink()

    def test_strips_whitespace(self):
        """Given URLs with whitespace, when parsing, then strips it."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  https://youtu.be/abc123def45  \n")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            urls = parse_input_list(file_path)

            # Assert
            assert urls == ["https://youtu.be/abc123def45"]
        finally:
            file_path.unlink()

    def test_raises_for_nonexistent_file(self):
        """Given a nonexistent file, when parsing, then raises ValueError."""
        # Arrange
        file_path = Path("/nonexistent/path/urls.txt")

        # Act & Assert
        with pytest.raises(ValueError, match="Could not read input file"):
            parse_input_list(file_path)


class TestProcessBatch:
    """Tests for batch processing functionality."""

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_processes_multiple_urls(self, mock_fetch):
        """Given multiple URLs, when processing batch, then processes each."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Test")],
            language="en",
            is_generated=False,
        )
        mock_fetch.return_value = (mock_result, None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.write("https://youtu.be/xyz789ghi01\n")
            f.flush()
            file_path = Path(f.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                exit_code = process_batch(file_path, None)

                # Assert
                assert exit_code == 0
                assert mock_fetch.call_count == 2
                assert Path("transcript-abc123def45.md").exists()
                assert Path("transcript-xyz789ghi01.md").exists()
            finally:
                os.chdir(original_cwd)
                file_path.unlink()

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_skips_duplicate_urls(self, mock_fetch):
        """Given duplicate URLs, when processing batch, then processes each video ID once."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Test")],
            language="en",
            is_generated=False,
        )
        mock_fetch.return_value = (mock_result, None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.write("https://www.youtube.com/watch?v=abc123def45\n")  # Same video ID
            f.write("https://youtu.be/abc123def45\n")  # Duplicate
            f.flush()
            file_path = Path(f.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                exit_code = process_batch(file_path, None)

                # Assert
                assert exit_code == 0
                assert mock_fetch.call_count == 1  # Only one unique video ID
            finally:
                os.chdir(original_cwd)
                file_path.unlink()

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_continues_on_failure(self, mock_fetch):
        """Given a failing URL, when processing batch, then continues with others."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Test")],
            language="en",
            is_generated=False,
        )
        # First call fails, second succeeds
        mock_fetch.side_effect = [
            (None, "Transcript not available"),
            (mock_result, None),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.write("https://youtu.be/xyz789ghi01\n")
            f.flush()
            file_path = Path(f.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                exit_code = process_batch(file_path, None)

                # Assert
                assert exit_code == 1  # Returns 1 because one failed
                assert mock_fetch.call_count == 2  # Both were attempted
                assert not Path("transcript-abc123def45.md").exists()  # Failed
                assert Path("transcript-xyz789ghi01.md").exists()  # Succeeded
            finally:
                os.chdir(original_cwd)
                file_path.unlink()

    def test_returns_error_for_empty_file(self):
        """Given an empty file, when processing batch, then returns error."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            exit_code = process_batch(file_path, None)

            # Assert
            assert exit_code == 1
        finally:
            file_path.unlink()

    def test_returns_error_for_all_invalid_urls(self):
        """Given only invalid URLs, when processing batch, then returns error."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("not-a-url\n")
            f.write("also-not-a-url\n")
            f.flush()
            file_path = Path(f.name)

        try:
            # Act
            exit_code = process_batch(file_path, None)

            # Assert
            assert exit_code == 1
        finally:
            file_path.unlink()


class TestProcessSingleUrl:
    """Tests for single URL processing."""

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_creates_transcript_file(self, mock_fetch):
        """Given a valid URL, when processing, then creates transcript file."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Hello world")],
            language="en",
            is_generated=False,
        )
        mock_fetch.return_value = (mock_result, None)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-transcript.md"

            # Act
            success, error = process_single_url(
                "https://youtu.be/abc123def45", output_path, None
            )

            # Assert
            assert success is True
            assert error is None
            assert output_path.exists()
            content = output_path.read_text()
            assert "00:00:00 Hello world" in content

    def test_returns_error_for_invalid_url(self):
        """Given an invalid URL, when processing, then returns error."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-transcript.md"

            # Act
            success, error = process_single_url("invalid-url", output_path, None)

            # Assert
            assert success is False
            assert "Could not extract video ID" in error

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_returns_error_when_fetch_fails(self, mock_fetch):
        """Given fetch failure, when processing, then returns error."""
        # Arrange
        mock_fetch.return_value = (None, "Transcripts disabled")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-transcript.md"

            # Act
            success, error = process_single_url(
                "https://youtu.be/abc123def45", output_path, None
            )

            # Assert
            assert success is False
            assert error == "Transcripts disabled"


class TestMain:
    """Tests for main CLI entry point."""

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_single_url_mode(self, mock_fetch):
        """Given a single URL, when running main, then processes it."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Test")],
            language="en",
            is_generated=False,
        )
        mock_fetch.return_value = (mock_result, None)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "transcript.md"

            # Act
            exit_code = main(
                ["https://youtu.be/abc123def45", "--out", str(output_path)]
            )

            # Assert
            assert exit_code == 0
            assert output_path.exists()

    @patch("yt_transcript_fetcher.cli.fetch_transcript")
    def test_batch_mode(self, mock_fetch):
        """Given --input-list, when running main, then processes batch."""
        # Arrange
        mock_result = TranscriptResult(
            segments=[TranscriptSegment(start=0, duration=2, text="Test")],
            language="en",
            is_generated=False,
        )
        mock_fetch.return_value = (mock_result, None)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("https://youtu.be/abc123def45\n")
            f.flush()
            file_path = Path(f.name)

        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Act
                exit_code = main(["--input-list", str(file_path)])

                # Assert
                assert exit_code == 0
                assert Path("transcript-abc123def45.md").exists()
            finally:
                os.chdir(original_cwd)
                file_path.unlink()

    def test_no_url_returns_error(self):
        """Given no URL or input list, when running main, then returns error."""
        # Act
        exit_code = main([])

        # Assert
        assert exit_code == 1

    def test_invalid_url_returns_error(self):
        """Given an invalid URL, when running main, then returns error."""
        # Act
        exit_code = main(["invalid-url"])

        # Assert
        assert exit_code == 1
