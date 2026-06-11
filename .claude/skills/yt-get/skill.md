# yt-get

Download YouTube transcripts and summarize them.

## Usage

```
/yt-get [--clean] <YouTube URLs>
```

## Workflow

1. If `--clean` flag is present, run `make clean` to clear the output directory. Otherwise, keep existing files.
2. Write the provided YouTube URLs to `urls.txt` (one URL per line)
3. Run `make get-list` to download transcripts
4. Use the `/summarise-transcript` skill to generate summaries

## Arguments

The command accepts YouTube URLs as arguments. These will be written to `urls.txt` before downloading.

- `--clean` - Clear the output directory before downloading. Without this flag, new transcripts are added alongside existing files.

Examples:
```
/yt-get https://www.youtube.com/watch?v=abc123 https://www.youtube.com/watch?v=def456
/yt-get --clean https://www.youtube.com/watch?v=abc123
```
