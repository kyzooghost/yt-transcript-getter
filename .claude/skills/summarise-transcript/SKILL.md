---
name: summarise-transcript
description: Summarizes YouTube video transcripts in 20-minute chunks with structured output. Use when asked to summarize YT transcripts, meeting recordings, or video content. Looks for `transcript-*.md` files and produces summaries with key points by speaker, technical insights, decisions, action items, and follow-ups. Outputs to `summary-<video-id>.md`.
---

# Summarise Transcript

Summarize YouTube video transcripts into structured 20-minute chunks for easy review.

## Workflow

### 1. Find Transcript Files

Search for `transcript-*.md` files in the working directory using Glob.

- If user specifies a file path, use only that file
- Otherwise, find ALL `transcript-*.md` files in the directory
- Extract video ID from each filename: `transcript-<video-id>.md` -> `<video-id>`

### 2. Process Multiple Transcripts in Parallel

When multiple transcript files are found:

1. Use the **Task tool** with `subagent_type: "general-purpose"` for EACH transcript file
2. Launch all agents **in parallel** (single message with multiple Task tool calls)
3. Each agent processes one transcript independently and outputs to its own `summary-<video-id>.md`

**Task prompt template for each agent:**
```
Summarize the YouTube transcript at <FILE_PATH>

Instructions:
1. Read the transcript file
2. Parse timestamps (format: HH:MM:SS text) and group into 20-minute chunks:
   - Chunk 1: 00:00:00 - 00:19:59
   - Chunk 2: 00:20:00 - 00:39:59
   - Continue for remaining content

3. For EACH chunk, generate a structured summary with these sections:
   - Key points by speaker
   - Important technical insights
   - Decisions made
   - Action items
   - Unresolved questions/follow-ups

4. Write output to <OUTPUT_PATH>

Use this format:
# Summary: <video-id>

## Chunk 1 (00:00 - 20:00)
### Key Points by Speaker
### Important Technical Insights
### Decisions Made
### Action Items
### Unresolved Questions/Follow-ups

---

## Chunk 2 (20:00 - 40:00)
[repeat structure]
```

### 3. Per-Transcript Processing (done by each agent)

**Parse and Chunk:**
- Read the transcript content
- Parse timestamps from each line (format: `HH:MM:SS text`)
- Group lines into 20-minute chunks based on timestamp

**Timestamp parsing:**
```
Pattern: ^(\d{2}):(\d{2}):(\d{2})\s+(.*)$
Seconds = hours*3600 + minutes*60 + seconds
```

**Summarize Each Chunk:**
Apply the summarization prompt:

> You are an expert summariser of software engineering meetings. Analyse and generate a structured summary that includes:
> - **Key points by speaker** - Summarise suggestions, technical inputs and/or concerns raised by each speaker
> - **Important technical insights** - Highlight significant technical and strategic insights, challenges, trade-offs and/or discoveries
> - **Decisions made** - Note any design, process or timeline decisions agreed upon
> - **Action items** - List specific tasks assigned, including who is responsible and deadlines
> - **Unresolved questions/follow-ups** - List open questions, blockers, or areas requiring further discussion

### 4. Output Format

Create `summary-<video-id>.md` in the same directory as the transcript.

## Example Usage

**Single transcript:**
User: "Summarize transcript-Ta5g-OxjPO4.md"
-> Process that one file, output to summary-Ta5g-OxjPO4.md

**All transcripts in directory:**
User: "Summarize all YT transcripts"
-> Glob for transcript-*.md, spawn parallel general-purpose agents for each
