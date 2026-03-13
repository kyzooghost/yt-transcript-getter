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

Transcription requires local whisper model. If unavailable, stops at MP3.

## Workflow

### 1. Setup

```bash
make clean
```

Write provided URLs to `urls.txt` (one per line).

### 2. Download Audio

```bash
make get-list-audio
```

Output: `output/audio-{video_id}.mp3` for each URL.

### 3. Check for Whisper Model

```bash
ls ~/.whisper-cpp/ggml-medium.bin
```

**If model NOT found:** Stop here and inform user:

> Audio files downloaded to `output/audio-*.mp3`
>
> Local whisper model not found at `~/.whisper-cpp/ggml-medium.bin`.
>
> To transcribe, either:
> 1. Install whisper-cpp model locally, or
> 2. Upload MP3 files to https://elevenlabs.io/mp3-to-text for online transcription
>
> After getting transcripts, save them as `output/transcript-{video_id}.md` and run `/summarise-transcript`.

**If model found:** Continue to step 4.

### 4. Transcribe Each Audio File

For each `output/audio-{video_id}.mp3`:

```bash
ffmpeg -i "output/audio-{video_id}.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_{video_id}.wav
whisper-cpp -m ~/.whisper-cpp/ggml-medium.bin -f /tmp/whisper_{video_id}.wav -otxt -l en
```

Save `/tmp/whisper_{video_id}.wav.txt` as `output/transcript-{video_id}.md`.

### 5. Summarize

Invoke `/summarise-transcript` to process all transcripts.

## Example

```
/yt-get-audio https://www.youtube.com/watch?v=abc123
```

With whisper model:
- `output/audio-abc123.mp3`
- `output/transcript-abc123.md`
- `output/summary-abc123.md`

Without whisper model:
- `output/audio-abc123.mp3` (then use elevenlabs.io for transcription)
