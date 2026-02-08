from pathlib import Path


def test_index_copy_mentions_15_minute_snippets():
    index_html = Path("public/index.html").read_text(encoding="utf-8")

    assert "15-minute" in index_html
    assert "approximately 15 minutes" in index_html
