---
name: m3u8-to-summary
description: Convert a signed HLS .m3u8 URL, or metadata JSON containing videoUrls, into an MP3, timestamped Whisper transcript, and structured 20-minute meeting summary. Use when the user provides an m3u8 playlist, Cornerstone/CSOD-style video metadata, or asks to go from HLS broadcast/video link to summary.
---

# M3U8 to Summary

## Overview

Turn a signed HLS playlist into reviewable meeting notes. Use the helper script for media download and transcription, then summarize the generated transcript with the section format below.

## Workflow

1. Save any pasted metadata JSON to a temporary file if it is too large to pass safely as a shell argument.
2. Run `scripts/m3u8_to_transcript.py` from this skill.
3. Read the generated transcript.
4. Write `output/summary-<slug>.md` with 20-minute chunks.
5. Verify the MP3, transcript, and summary before reporting completion.

## Helper Script

Use:

```bash
python3 agents/skills/m3u8-to-summary/scripts/m3u8_to_transcript.py \
  --m3u8-url '<SIGNED_M3U8_URL>' \
  --title 'Consensys Core Devs Unpacked - July 2026'
```

For metadata JSON:

```bash
python3 agents/skills/m3u8-to-summary/scripts/m3u8_to_transcript.py \
  --metadata-json /tmp/video-metadata.json \
  --title 'Consensys Core Devs Unpacked - July 2026'
```

The script:
- Selects the first non-localhost URL containing `.m3u8` from metadata JSON.
- Writes `output/<slug>.mp3`.
- Converts MP3 to `/tmp/<slug>-whisper.wav`.
- Runs Whisper through pinned `uv` transient dependencies: `openai-whisper==20250625` and `setuptools==80.9.0`.
- Writes `output/transcript-<slug>.md`.
- Prints the MP3, transcript, duration, and size.

Prerequisites: `ffmpeg`, `ffprobe`, `uv`, and network access to the signed playlist and Whisper model cache/download. If `python` is missing, use `python3`.

## Summary Format

Create `output/summary-<slug>.md`:

```markdown
# Summary: <slug>

## Chunk 1 (00:00 - 20:00)
### Key Points by Speaker
### Important Technical Insights
### Decisions Made
### Action Items
### Unresolved Questions/Follow-ups

---

## Chunk 2 (20:00 - 40:00)
[repeat sections]
```

Chunk rules:
- Parse transcript lines matching `HH:MM:SS text`.
- Group into 20-minute windows: `00:00:00-00:19:59`, `00:20:00-00:39:59`, and so on.
- Include a short final chunk if the recording ends just after a boundary.
- Preserve transcript wording for uncertain names unless the correction is obvious from context.

Summarize as an expert software engineering meeting summarizer:
- Key points by speaker: suggestions, technical inputs, concerns, or updates.
- Important technical insights: tradeoffs, risks, architecture, protocol or implementation details.
- Decisions made: explicit decisions only. If none, say none.
- Action items: owner and deadline when stated. Do not invent owners.
- Unresolved questions/follow-ups: open questions, blockers, or topics requiring more discussion.

## Verification

Run fresh checks before reporting completion:

```bash
ffprobe -v error -show_entries format=duration,bit_rate,size -of default=noprint_wrappers=1:nokey=0 output/<slug>.mp3
wc -l output/transcript-<slug>.md output/summary-<slug>.md
rg '^## Chunk|^### Key Points by Speaker|^### Important Technical Insights|^### Decisions Made|^### Action Items|^### Unresolved Questions/Follow-ups' output/summary-<slug>.md
```

Report the output paths and verification evidence.

Do not paste signed playlist URLs back to the user unless they explicitly ask. Treat query strings as bearer-like credentials.
