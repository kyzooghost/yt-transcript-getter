---
name: transcribe-mp3
description: Transcribe MP3 audio files to markdown using Python openai-whisper. Use when transcribing audio files in this project. Outputs to output/transcript-{video_id}.md format compatible with summarise-transcript skill.
---

# Transcribe MP3

Transcribe MP3 audio files to markdown transcripts using OpenAI Whisper (Python).

## Requirements

- `ffmpeg` installed (`brew install ffmpeg`)
- `uv` installed (Python package runner)

## Workflow

### 1. Identify Files

Find MP3 files to transcribe:
- If user specifies a file, use that
- Otherwise, glob for `output/*.mp3`

Extract video_id from filename. Common patterns:
- `output/audio-{video_id}.mp3`
- `output/{title} [{video_id}].mp3` (yt-dlp format - ID is in square brackets)

### 2. Convert to WAV

```bash
ffmpeg -y -i "<input.mp3>" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_{video_id}.wav
```

### 3. Transcribe with Python openai-whisper

**Primary method** - uses `uv run` with SSL workarounds for corporate environments:

```bash
REQUESTS_CA_BUNDLE="" PYTHONHTTPSVERIFY=0 uv run --with openai-whisper --with setuptools python -c "
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import whisper
model = whisper.load_model('small')
result = model.transcribe('/tmp/whisper_{video_id}.wav', language='en', verbose=False)
with open('output/transcript-{video_id}.md', 'w') as f:
    f.write('# Transcript: {video_id}\n\n')
    for seg in result['segments']:
        start = seg['start']
        h, m, s = int(start // 3600), int((start % 3600) // 60), int(start % 60)
        f.write(f'{h:02d}:{m:02d}:{s:02d} {seg[\"text\"].strip()}\n')
print(f'Done! {len(result[\"segments\"])} segments')
"
```

**Set bash timeout to 600000ms** - a 40-min recording takes ~4 minutes on Apple Silicon.

If model auto-download fails (blocked CDN), pre-download manually:
```bash
curl -L "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt" -o /tmp/whisper-small.pt
```
Then load with: `model = whisper.load_model('/tmp/whisper-small.pt')`

### 4. Output

Save to `output/transcript-{video_id}.md` with format:

```markdown
# Transcript: {video_id}

00:00:00 First line of text
00:00:05 Second line of text
...
```

### 5. Cleanup

Remove temporary WAV file from /tmp.

## Fallback: whisper-cli (brew)

If Python whisper is unavailable, use the brew-installed whisper-cli:

```bash
/opt/homebrew/Cellar/whisper-cpp/1.8.3/bin/whisper-cli -m <model_path> -f /tmp/whisper_{video_id}.wav -otxt -l en
```

**Note:** The binary is `whisper-cli` (NOT `whisper-cpp`). The ggml model format changes between versions - if you get "invalid model data (bad magic)", use Python whisper instead.

## Model Options

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| tiny | 39 MB | fastest | low (testing only) |
| base | 74 MB | fast | acceptable |
| small | 461 MB | ~4 min/40 min audio | good (recommended) |
| medium | 1.5 GB | ~10 min/40 min audio | better |

Use `small` as default. Use `medium` only for critical/unclear audio.

## Example

User: "Transcribe output/Raytar - Some title [2068768519722831872].mp3"

1. Extract ID: `2068768519722831872`
2. Convert: `ffmpeg -y -i "output/Raytar - Some title [2068768519722831872].mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_2068768519722831872.wav`
3. Transcribe with Python whisper (see above)
4. Output: `output/transcript-2068768519722831872.md`
