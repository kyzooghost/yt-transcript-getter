---
name: get-x-broadcast-audio
description: Use when needing to download audio from a Twitter/X broadcast or Periscope replay. Requires the user to provide an m3u8 playlist URL captured from browser DevTools (contains authentication token).
---

# Get X Broadcast Audio

Download a Twitter/X broadcast replay as an audio file using ffmpeg.

## Prerequisites

- `ffmpeg` installed (`brew install ffmpeg`)

## Workflow

### 1. Get m3u8 URL from User

Ask the user for the **m3u8 playlist URL** from the broadcast. This URL must be captured from browser DevTools:

1. Open the broadcast in browser (e.g. `https://x.com/i/broadcasts/<broadcast_id>`)
2. Open DevTools > Network tab
3. Filter by `m3u8`
4. Play the replay
5. Copy the full playlist URL (contains auth token in the path)

The URL looks like:
```
https://prod-fastly-<region>.video.pscp.tv/Transcoding/v1/hls/<stream_key>/transcode/<region>/periscope-replay-direct-prod-<region>-public/<jwt_token>/playlist_<id>.m3u8?type=replay
```

**The URL contains a JWT auth token that expires.** It cannot be reused after expiry.

### 2. Download Audio

Use ffmpeg to extract audio directly from the m3u8 stream. Run in background since broadcasts can be 30-60+ minutes:

```bash
mkdir -p output
ffmpeg -i "<m3u8_url>" -vn -c:a aac -b:a 64k output/broadcast.m4a
```

Run via Bash with `run_in_background: true`. Then poll progress using `tail -3 <output_file>` until the task completes. Report progress to the user (current time position vs total duration). Do not consider this step done until ffmpeg exits successfully.

### 3. Output

- `output/broadcast.m4a` - audio only, suitable for transcription upload (e.g. Whisper, ChatGPT)

## Common Issues

- **Relative chunk paths**: The m3u8 file alone is not enough - ffmpeg needs the full URL to resolve relative `.ts` chunk paths against the CDN base URL
- **Token expiry**: The JWT in the URL expires (typically within hours). Capture and use promptly
- **Non-monotonic DTS warnings**: Normal for live replay streams, does not affect output quality
