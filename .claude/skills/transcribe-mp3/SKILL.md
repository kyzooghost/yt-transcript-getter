---
name: transcribe-mp3
description: Transcribe MP3 audio files to markdown using whisper-cpp. Use when transcribing audio files in this project. Outputs to output/transcript-{video_id}.md format compatible with summarise-transcript skill.
---

# Transcribe MP3

Transcribe MP3 audio files to markdown transcripts using whisper-cpp.

## Requirements

- `whisper-cpp` installed (`brew install whisper-cpp`)
- `ffmpeg` installed (`brew install ffmpeg`)
- Medium model at `~/.whisper-cpp/ggml-medium.bin`

## Workflow

### 1. Identify Files

Find MP3 files to transcribe:
- If user specifies a file, use that
- Otherwise, glob for `output/audio-*.mp3`

Extract video_id from filename: `output/audio-{video_id}.mp3`

### 2. Transcribe Each File

For each MP3 file:

```bash
# Convert to WAV (whisper-cpp requires 16kHz mono WAV)
ffmpeg -i "output/audio-{video_id}.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_{video_id}.wav

# Run transcription
whisper-cpp -m ~/.whisper-cpp/ggml-medium.bin -f /tmp/whisper_{video_id}.wav -otxt -l en

# Output is at /tmp/whisper_{video_id}.wav.txt
```

### 3. Format and Save

Read the whisper output and format as markdown transcript:

```markdown
# Transcript: {video_id}

{transcript_content}
```

Save to `output/transcript-{video_id}.md`

### 4. Cleanup

Remove temporary WAV files from /tmp.

## Options

| Flag | Description |
|------|-------------|
| `-l <lang>` | Language code (default: `en`) |
| `-t <threads>` | Number of threads (default: 4) |

## Example

User: "Transcribe output/audio-lbfoNxoHl2o.mp3"

```bash
ffmpeg -i "output/audio-lbfoNxoHl2o.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_lbfoNxoHl2o.wav
whisper-cpp -m ~/.whisper-cpp/ggml-medium.bin -f /tmp/whisper_lbfoNxoHl2o.wav -otxt -l en
```

Then read `/tmp/whisper_lbfoNxoHl2o.wav.txt`, format as markdown, save to `output/transcript-lbfoNxoHl2o.md`.
