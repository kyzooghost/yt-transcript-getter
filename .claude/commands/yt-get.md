# yt-get

Download YouTube transcripts and summarize them.

## Usage

```
/yt-get <YouTube URLs>
```

## Workflow

1. Run `make clean` to clear the output directory
2. Write the provided YouTube URLs to `urls.txt` (one URL per line)
3. Run `make get-list` to download transcripts
4. Use the `/summarise-transcript` skill to generate summaries

## Arguments

The command accepts YouTube URLs as arguments. These will be written to `urls.txt` before downloading.

Example:
```
/yt-get https://www.youtube.com/watch?v=abc123 https://www.youtube.com/watch?v=def456
```
