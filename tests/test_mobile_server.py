import mobile_server
from yt_transcript_fetcher.youtube import TranscriptResult


def test_mobile_server_uses_15_minute_snippets(monkeypatch):
    captured = {}

    def fake_split(segments, target_minutes, variance_minutes):
        captured["target_minutes"] = target_minutes
        captured["variance_minutes"] = variance_minutes
        return [{"id": 1, "start": 0, "end": 0, "text": ""}]

    fake_result = TranscriptResult(segments=[], language="en", is_generated=False)

    monkeypatch.setattr(mobile_server, "extract_video_id", lambda url: "abc123")
    monkeypatch.setattr(
        mobile_server,
        "fetch_transcript",
        lambda video_id: (fake_result, None),
    )
    monkeypatch.setattr(mobile_server, "split_into_snippets", fake_split)
    monkeypatch.setattr(
        mobile_server, "format_transcript_to_markdown", lambda segments: "full"
    )

    client = mobile_server.app.test_client()
    response = client.post("/api/transcript", json={"url": "https://youtu.be/abc123"})

    assert response.status_code == 200
    assert captured["target_minutes"] == 15
    assert captured["variance_minutes"] == 2
