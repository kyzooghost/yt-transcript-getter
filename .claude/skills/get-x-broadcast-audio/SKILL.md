---
name: get-x-broadcast-audio
description: "Download audio from a Twitter/X broadcast, transcribe it, and summarize. Use when given a tweet URL containing a broadcast/space replay. Primary method: yt-dlp with Chrome cookies. Fallback: manual m3u8 from DevTools."
---

# Get X Broadcast Audio

Download a Twitter/X broadcast replay, transcribe it, and summarize - end to end.

## Usage

```
/get-x-broadcast-audio <tweet-or-broadcast-URL>
```

Example:
```
/get-x-broadcast-audio https://x.com/Raytar/status/2068769808720543781
```

## Prerequisites

- `yt-dlp` installed (`brew install yt-dlp`)
- `ffmpeg` installed (`brew install ffmpeg`)
- Chrome browser (for cookie-based auth)

## Workflow

### 1. Download Audio with yt-dlp (Primary Method)

This is the preferred approach - no manual DevTools capture needed:

```bash
mkdir -p output
yt-dlp --cookies-from-browser chrome -x --audio-format mp3 "<TWEET_URL>" -o "output/%(title).50s [%(id)s].%(ext)s"
```

**Note:** The user will see a macOS keychain prompt asking to allow access to "Chrome Safe Storage". They must click **Allow**.

The output filename will contain the tweet ID in brackets, e.g.:
`output/Username - Tweet text... [2068768519722831872].mp3`

Extract the tweet/broadcast ID from the filename for use in later steps.

### 2. Transcribe with Whisper

Convert the MP3 to 16kHz mono WAV, then transcribe:

```bash
ffmpeg -y -i "output/<filename>.mp3" -ar 16000 -ac 1 -c:a pcm_s16le /tmp/whisper_input.wav
```

Then transcribe using Python openai-whisper (handles model download from Azure CDN which is not blocked):

```bash
REQUESTS_CA_BUNDLE="" PYTHONHTTPSVERIFY=0 uv run --with openai-whisper --with setuptools python -c "
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import whisper
model = whisper.load_model('small')
result = model.transcribe('/tmp/whisper_input.wav', language='en', verbose=False)
with open('output/transcript-<ID>.md', 'w') as f:
    f.write('# Transcript: <ID>\n\n')
    for seg in result['segments']:
        start = seg['start']
        h, m, s = int(start // 3600), int((start % 3600) // 60), int(start % 60)
        f.write(f'{h:02d}:{m:02d}:{s:02d} {seg[\"text\"].strip()}\n')
print(f'Done! {len(result[\"segments\"])} segments')
"
```

If model is already cached at `/tmp/whisper-small.pt`, load it directly:
```python
model = whisper.load_model('/tmp/whisper-small.pt')
```

If no cached model and Azure CDN download fails, pre-download manually:
```bash
curl -L "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt" -o /tmp/whisper-small.pt
```

**Timeout:** Set bash timeout to 600000ms (10 min) - a 40-min recording takes ~4 min to transcribe.

### 3. Summarize

Once the transcript is at `output/transcript-<ID>.md`, invoke `/summarise-transcript` to generate the structured summary at `output/summary-<ID>.md`.

### 4. Output Files

- `output/<title> [<ID>].mp3` - downloaded audio
- `output/transcript-<ID>.md` - timestamped transcript
- `output/summary-<ID>.md` - structured summary (20-min chunks)

## Fallback: Manual m3u8 Method

If yt-dlp fails (e.g. auth issues, rate limiting), fall back to manual capture:

1. Open the broadcast in browser (`https://x.com/i/broadcasts/<broadcast_id>`)
2. Open DevTools > Network tab, filter by `m3u8`
3. Play the replay
4. Copy the full playlist URL (contains auth token)
5. Download with ffmpeg:

```bash
ffmpeg -i "<m3u8_url>" -vn -c:a aac -b:a 64k output/broadcast-<ID>.m4a
```

Then convert the m4a to mp3 and proceed with transcription as above.

## Common Issues

- **Keychain prompt**: macOS will ask for keychain access when yt-dlp reads Chrome cookies - user must Allow
- **HuggingFace blocked**: Corporate firewalls may block huggingface.co. Use the Azure CDN URL above for model download
- **SSL errors in Python**: Use `ssl._create_unverified_context` and `PYTHONHTTPSVERIFY=0` for corporate proxy environments
- **whisper-cpp model format**: If using whisper-cli (brew), the ggml model format may be outdated. Prefer Python openai-whisper
- **Large files**: 40-min broadcasts produce ~20MB MP3 and ~75MB WAV. Transcription takes ~4 min on Apple Silicon
