#!/usr/bin/env python3
"""Test script for the web app snippet splitting logic."""

import sys
sys.path.insert(0, "api")

from transcript import (
    extract_video_id,
    TranscriptSegment,
    split_into_snippets,
    seconds_to_timestamp,
)


def test_extract_video_id():
    """Test video ID extraction from various URL formats."""
    test_cases = [
        ("https://youtu.be/7wWRoqC0gnU", "7wWRoqC0gnU"),
        ("https://youtube.com/watch?v=7wWRoqC0gnU", "7wWRoqC0gnU"),
        ("https://www.youtube.com/watch?v=7wWRoqC0gnU&t=123", "7wWRoqC0gnU"),
        ("https://youtube.com/live/7wWRoqC0gnU", "7wWRoqC0gnU"),
        ("https://youtube.com/embed/7wWRoqC0gnU", "7wWRoqC0gnU"),
        ("invalid-url", None),
    ]

    print("Testing video ID extraction:")
    for url, expected in test_cases:
        result = extract_video_id(url)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {url} -> {result}")

    print()


def test_snippet_splitting():
    """Test snippet splitting logic."""
    # Create mock transcript segments
    # Simulate a 65-minute video
    segments = []
    for i in range(390):  # 390 segments * 10 seconds = 65 minutes
        start = i * 10
        text = f"This is segment {i}."
        # Add sentence boundaries at strategic points
        if i % 20 == 19:  # Every 20th segment ends with period
            text = f"This is segment {i}."
        segments.append(TranscriptSegment(start=start, duration=10.0, text=text))

    print("Testing snippet splitting:")
    print(f"  Total segments: {len(segments)}")
    print(f"  Total duration: {segments[-1].start + segments[-1].duration} seconds")
    print()

    snippets = split_into_snippets(segments, target_minutes=20, variance_minutes=2)

    print(f"  Number of snippets: {len(snippets)}")
    print()

    for snippet in snippets:
        print(f"  Snippet {snippet['index']}:")
        print(f"    Time range: {snippet['start_time']} - {snippet['end_time']}")
        print(f"    Duration: {snippet['duration_minutes']} minutes")
        print(f"    Markdown length: {len(snippet['markdown'])} chars")
        print()


def test_timestamp_conversion():
    """Test timestamp conversion."""
    test_cases = [
        (0, "00:00:00"),
        (65, "00:01:05"),
        (3661, "01:01:01"),
        (7322, "02:02:02"),
    ]

    print("Testing timestamp conversion:")
    for seconds, expected in test_cases:
        result = seconds_to_timestamp(seconds)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {seconds}s -> {result} (expected: {expected})")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Web App - Test Suite")
    print("=" * 60)
    print()

    test_extract_video_id()
    test_timestamp_conversion()
    test_snippet_splitting()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
