---
name: yt-get-audio
description: Download YouTube videos as audio, transcribe with whisper, and summarize. Use when the user wants to process YouTube videos that don't have transcripts available, or prefers audio-based transcription. Triggers on "/yt-get-audio <URLs>" or requests like "download and transcribe YouTube audio".
---

# yt-get-audio

Download YouTube audio, optionally transcribe and summarize.

## Usage

```
/yt-get-audio <YouTube URLs>
```

## Pipeline

```
URLs -> urls.txt -> MP3 -> [Transcript -> Summary]
```

Transcription uses whisper-cpp (primary) or Python openai-whisper (fallback). If neither available, stops at MP3.

## Workflow

### 1. Setup

```bash
make clean
```

Write provided URLs to `urls.txt` (one per line).

### 2. Download Audio

For YouTube URLs:

```bash
make get-list-audio
```

For non-YouTube URLs (e.g. x.com, twitter.com):

```bash
yt-dlp --cookies-from-browser chrome -x --audio-format mp3 -o "output/audio-%(id)s.%(ext)s" "<URL>"
```

Output: `output/audio-{video_id}.mp3` for each URL.

### 3. Transcribe (with fallback)

Try transcription methods in order:

#### Method A: whisper-cpp with ggml-medium model (primary)

Check if a valid model exists:

```bash
ls ~/.whisper-cpp/ggml-medium.bin
file ~/.whisper-cpp/ggml-medium.bin  # must NOT be "HTML document"
```

The model file must be ~1.5GB and a valid ggml binary (not an HTML page from a failed download).

If valid, transcribe each `output/audio-{video_id}.mp3`:

```bash
ffmpeg -i "output/audio-{video_id}.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_{video_id}.wav
whisper-cli -m ~/.whisper-cpp/ggml-medium.bin -f /tmp/whisper_{video_id}.wav -otxt -l en
```

Save `/tmp/whisper_{video_id}.wav.txt` as `output/transcript-{video_id}.md`.

#### Method B: Python openai-whisper via uv (fallback)

If whisper-cpp model is missing or corrupt, use the Python openai-whisper package with the cached `small` model at `~/.cache/whisper/small.pt`:

```bash
uv run --with openai-whisper --with torch python3 -c "
import whisper
model = whisper.load_model('small')
result = model.transcribe('output/audio-{video_id}.mp3', language='en', verbose=False)
with open('output/transcript-{video_id}.md', 'w') as f:
    f.write(result['text'])
"
```

Repeat for each audio file.

#### Neither method available

If both methods fail, stop and inform user:

> Audio files downloaded to `output/audio-*.mp3`
>
> No whisper transcription available:
> - whisper-cpp model not found/corrupt at `~/.whisper-cpp/ggml-medium.bin`
> - Python openai-whisper fallback failed
>
> To transcribe, either:
> 1. Download the ggml-medium.bin model (~1.5GB) from huggingface.co/ggerganov/whisper.cpp
> 2. Use https://elevenlabs.io/mp3-to-text to transcribe online
>
> After getting transcripts, save them as `output/transcript-{video_id}.md` and run `/summarise-transcript`.

### 4. Summarize

Invoke `/summarise-transcript` to process all transcripts.

## Example

```
/yt-get-audio https://www.youtube.com/watch?v=abc123
```

With whisper available:
- `output/audio-abc123.mp3`
- `output/transcript-abc123.md`
- `output/summary-abc123.md`

Without whisper:
- `output/audio-abc123.mp3` (then use elevenlabs.io for transcription)
