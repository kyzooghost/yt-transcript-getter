# YouTube Transcript Fetcher

A vibe-coded Python CLI tool that fetches transcripts from YouTube videos and saves them as Markdown files.

## Features

- Supports multiple YouTube URL formats:
  - `https://youtu.be/<id>`
  - `https://www.youtube.com/watch?v=<id>`
  - `https://www.youtube.com/live/<id>`
  - URLs with extra query parameters (timestamps, playlists, etc.)
- Smart language selection (prefers manual English, falls back to auto-generated)
- Clean Markdown output with timestamps
- Configurable output path and language preference

## Installation

This project uses [uv](https://docs.astral.sh/uv/) as the package manager.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone <repository-url>
cd youtube-transcript

# Install dependencies
uv sync

# Install with dev dependencies (for testing)
uv sync --all-extras
```

## Usage

### Basic usage

```bash
# Fetch transcript from a YouTube video
uv run yt-transcript "https://youtu.be/7wWRoqC0gnU"

# Or use the full URL format
uv run yt-transcript "https://www.youtube.com/watch?v=7wWRoqC0gnU"
```

### Specify output file

```bash
uv run yt-transcript "https://youtu.be/7wWRoqC0gnU" --out my-transcript.md
```

### Specify preferred language

```bash
uv run yt-transcript "https://youtu.be/7wWRoqC0gnU" --lang es
```

### Using --url flag

```bash
uv run yt-transcript --url "https://youtu.be/7wWRoqC0gnU" --out transcript.md
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `url` (positional) | YouTube video URL | - |
| `--url` | YouTube video URL (alternative to positional) | - |
| `--out`, `-o` | Output file path | `transcript.md` |
| `--lang`, `-l` | Preferred language code (e.g., 'en', 'es', 'fr') | Auto-detect |
| `--format`, `-f` | Output format (`markdown` or `md`) | `markdown` |

## Example Output

```
00:00:00 Cursor 1.0 just dropped. What does that
00:00:02 mean for us VI coders, AI developers,
00:00:04 chat orientated programmers, whatever
00:00:07 you want to call yourself these days.
```

## Language Selection

The tool follows these rules for selecting which transcript to use:

1. **Default behavior** (no `--lang` flag):
   - Prefer manually-created transcripts in English (`en`, `en-US`, `en-GB`)
   - If not available, prefer auto-generated English
   - If no English, pick the first available transcript (manual preferred over generated)

2. **With `--lang` flag**:
   - Attempt exact match first
   - If not available, fall back to default behavior with a warning

## Development

### Running tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=yt_transcript_fetcher

# Run specific test file
uv run pytest tests/test_url_parsing.py -v
```

### Project structure

```
youtube-transcript/
├── src/
│   └── yt_transcript_fetcher/
│       ├── __init__.py
│       ├── cli.py           # CLI entry point
│       ├── youtube.py       # URL parsing & transcript fetching
│       └── formatting.py    # Markdown formatting
├── tests/
│   ├── test_url_parsing.py
│   ├── test_formatting.py
│   └── test_fetch_logic.py
├── pyproject.toml
└── README.md
```

## Limitations

- Requires the video to have transcripts enabled (either manual or auto-generated)
- Videos with disabled transcripts will return an error
- Private or age-restricted videos may not be accessible
- Some videos may only have auto-generated transcripts in specific languages

## License

MIT
