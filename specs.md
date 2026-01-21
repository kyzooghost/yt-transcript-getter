# Spec: YouTube Transcript Fetcher (Python)

## Goal
Build a small Python CLI tool that fetches the transcript for a given YouTube URL and writes it to a Markdown file.

- Input: a single YouTube link (any common format)
- Output: a Markdown transcript file matching the formatting of `@example-output.md`

Example input:
- https://youtu.be/7wWRoqC0gnU

Example output:
- `@example-output.md` (treat this as the source of truth for formatting)

## Scope
### Must-have features
1. **URL handling**
   - Accept YouTube URLs in common forms:
     - `https://youtu.be/<id>`
     - `https://www.youtube.com/watch?v=<id>`
     - `https://www.youtube.com/live/<id>`
     - URLs with extra query params (timestamps, playlists, etc.)
   - Robustly extract the video ID.

2. **Transcript retrieval**
   - Prefer `youtube-transcript-api`:
     - Repo: https://github.com/jdepoix/youtube-transcript-api
   - If transcript is not available in the default language, attempt to:
     - List available transcripts and pick the best match (see Language rules below)
     - If only auto-generated transcripts exist, use them as a fallback.
   - If retrieval fails, return a non-zero exit code and a helpful error message.

3. **Output format**
   - Output must match `@example-output.md` exactly in structure/style.
   - The tool should write to a user-specified file path OR default to `./transcript.md`.
   - Ensure deterministic output (stable ordering, stable formatting).

4. **CLI**
   - Provide an executable entrypoint (via `python -m ...` and/or console script).
   - Minimum CLI flags:
     - `--url <youtube_url>` (or positional URL)
     - `--out <path>` (optional, default `transcript.md`)
     - `--lang <code>` (optional; see language rules)
     - `--format <mode>` (optional, if needed to support example-output variants)
   - Print a short success message including output path on success.

5. **Project setup**
   - Use **uv** as the package manager.
   - Provide `pyproject.toml` with:
     - dependencies
     - a console script entrypoint
     - test dependencies
   - Provide `README.md` with:
     - install commands
     - usage examples
     - an example output snippet (small excerpt, not the entire file unless tiny)
     - notes on limitations (e.g., disabled transcripts)

6. **Unit tests**
   - Use `pytest`.
   - Test categories:
     - video ID parsing for multiple URL shapes
     - formatting renderer (given transcript segments → expected markdown)
     - error handling paths (no transcript, invalid URL, etc.)
   - Do **not** rely on live network calls in unit tests.
     - Mock `youtube_transcript_api` responses.
   - Keep tests fast and deterministic.

## Language selection rules
- Default behavior (no `--lang`):
  1. Prefer manually-created transcripts in English (`en`, `en-US`, `en-GB`).
  2. If not available, prefer auto-generated English.
  3. If no English, pick the first available transcript (manual preferred over generated).
- If `--lang` is provided:
  - Attempt exact match first; if not available, fallback to the default behavior but print a warning.

## Non-goals (explicitly out of scope unless trivial)
- Downloading audio/video
- Whisper / local ASR transcription (unless you propose it as an optional extension)
- Timestamp hyperlinking (unless `@example-output.md` shows it)
- Web UI

## Deliverables / repo layout (suggested)
- `src/yt_transcript_fetcher/`
  - `__init__.py`
  - `cli.py` (argparse/typer)
  - `youtube.py` (fetch + language selection)
  - `formatting.py` (markdown renderer)
- `tests/`
  - `test_url_parsing.py`
  - `test_formatting.py`
  - `test_fetch_logic.py` (mocked)
- `README.md`
- `pyproject.toml`
- `@example-output.md` (provided by me; do not modify)

## Acceptance criteria
- `uv run yt-transcript "<url>" --out transcript.md` produces a file matching `@example-output.md` for the example URL.
- `uv run pytest` passes.
- Running with an invalid URL exits non-zero with an actionable message.
- No tests require network access.
