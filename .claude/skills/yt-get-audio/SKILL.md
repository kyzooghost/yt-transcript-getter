---
name: yt-get-audio
description: Download YouTube videos as audio, transcribe with whisper, and summarize. Use when the user wants to process YouTube videos that don't have transcripts available, or prefers audio-based transcription. Triggers on "/yt-get-audio <URLs>" or requests like "download and transcribe YouTube audio".
---

# yt-get-audio

Download YouTube audio, transcribe with whisper-cpp, and generate structured summaries.

## Usage

```
/yt-get-audio <YouTube URLs>
```

## Pipeline

```
URLs -> urls.txt -> MP3 -> Transcript -> Summary
```

1. Download audio as MP3 (128kbps)
2. Transcribe with whisper-cpp
3. Summarize with structured output

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

### 3. Transcribe Each Audio File

For each `output/audio-{video_id}.mp3`, run the transcription:

```bash
# Convert to WAV
ffmpeg -i "output/audio-{video_id}.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_{video_id}.wav

# Transcribe
whisper-cpp -m ~/.whisper-cpp/ggml-medium.bin -f /tmp/whisper_{video_id}.wav -otxt -l en
```

Read `/tmp/whisper_{video_id}.wav.txt` and save as `output/transcript-{video_id}.md`:

```markdown
# Transcript: {video_id}

{transcript_content}
```

Process sequentially (transcription is CPU-intensive).

### 4. Summarize

Invoke `/summarise-transcript` to process all transcripts.

Output: `output/summary-{video_id}.md` for each transcript.

## Example

```
/yt-get-audio https://www.youtube.com/watch?v=abc123
```

Produces:
- `output/audio-abc123.mp3`
- `output/transcript-abc123.md`
- `output/summary-abc123.md`

## Requirements

- `ffmpeg` installed
- `whisper-cpp` installed with medium model at `~/.whisper-cpp/ggml-medium.bin`
