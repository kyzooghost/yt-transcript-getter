#!/usr/bin/env python3
"""Extract MP3 audio from an HLS playlist and transcribe it with Whisper."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

WHISPER_PACKAGE = "openai-whisper==20250625"
SETUPTOOLS_PACKAGE = "setuptools==80.9.0"
DEFAULT_MODEL = "small"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "m3u8-audio"


def read_text_or_file(value: str) -> str:
    path = Path(value).expanduser()
    if path.exists():
        return path.read_text(encoding="utf-8")
    return value


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def find_m3u8_url(metadata_json: str) -> str:
    try:
        parsed = json.loads(read_text_or_file(metadata_json))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"metadata JSON could not be parsed: {exc}") from exc

    for candidate in iter_strings(parsed):
        if ".m3u8" in candidate and "localhost" not in candidate:
            return candidate
    raise SystemExit("metadata JSON did not contain a non-localhost .m3u8 URL")


def derive_slug(title: str | None, m3u8_url: str, explicit_slug: str | None) -> str:
    if explicit_slug:
        return slugify(explicit_slug)
    if title:
        return slugify(title)
    path = urlparse(m3u8_url).path
    useful_parts = [part for part in path.split("/") if part and part.lower() not in {"hls"}]
    return slugify("-".join(useful_parts[-3:]) or "m3u8-audio")


def redact_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme and not parsed.netloc:
        return url
    redacted = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        redacted += "?<redacted>"
    return redacted


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not found on PATH: {name}")


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def redact_command(cmd: list[str]) -> str:
    redacted = []
    for part in cmd:
        if ".m3u8" in part or urlparse(part).query:
            redacted.append(redact_url(part))
        else:
            redacted.append(part)
    return " ".join(redacted)


def ffprobe(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,bit_rate,size",
            "-of",
            "default=noprint_wrappers=1:nokey=0",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition("=")
        values[key] = value
    return values


def transcribe_with_whisper(wav_path: Path, transcript_path: Path, title: str, model: str) -> None:
    code = r'''
import ssl
import sys
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context
import whisper

wav_path = sys.argv[1]
transcript_path = Path(sys.argv[2])
title = sys.argv[3]
model_name = sys.argv[4]

model = whisper.load_model(model_name)
result = model.transcribe(wav_path, language="en", verbose=False)

with transcript_path.open("w", encoding="utf-8") as f:
    f.write(f"# Transcript: {title}\n\n")
    for seg in result["segments"]:
        start = seg["start"]
        h = int(start // 3600)
        m = int((start % 3600) // 60)
        s = int(start % 60)
        text = seg["text"].strip()
        if text:
            f.write(f"{h:02d}:{m:02d}:{s:02d} {text}\n")

print(f"Done! {len(result['segments'])} segments -> {transcript_path}")
'''
    run(
        [
            "uv",
            "run",
            "--with",
            WHISPER_PACKAGE,
            "--with",
            SETUPTOOLS_PACKAGE,
            "python",
            "-c",
            code,
            str(wav_path),
            str(transcript_path),
            title,
            model,
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a signed .m3u8 URL or metadata JSON to MP3 and a Whisper transcript."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--m3u8-url", help="Signed HLS .m3u8 URL")
    source.add_argument("--metadata-json", help="Metadata JSON string or path containing videoUrls")
    parser.add_argument("--title", help="Human title for transcript header and slug")
    parser.add_argument("--slug", help="Output slug. Defaults to a slug from title or URL")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Whisper model name")
    parser.add_argument("--dry-run", action="store_true", help="Resolve inputs and print output paths without network work")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    m3u8_url = args.m3u8_url or find_m3u8_url(args.metadata_json)
    if ".m3u8" not in m3u8_url:
        raise SystemExit("input URL does not look like an .m3u8 playlist")

    slug = derive_slug(args.title, m3u8_url, args.slug)
    title = args.title or slug
    output_dir = Path(args.output_dir)
    mp3_path = output_dir / f"{slug}.mp3"
    transcript_path = output_dir / f"transcript-{slug}.md"
    wav_path = Path("/tmp") / f"{slug}-whisper.wav"

    print(f"Playlist: {redact_url(m3u8_url)}")
    print(f"MP3: {mp3_path}")
    print(f"Transcript: {transcript_path}")

    if args.dry_run:
        return 0

    for tool in ("ffmpeg", "ffprobe", "uv"):
        require_tool(tool)

    output_dir.mkdir(parents=True, exist_ok=True)

    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            m3u8_url,
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(mp3_path),
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ]
    )

    transcribe_with_whisper(wav_path, transcript_path, title, args.model)

    media_info = ffprobe(mp3_path)
    print(f"Duration: {media_info.get('duration', 'unknown')} seconds")
    print(f"Bit rate: {media_info.get('bit_rate', 'unknown')}")
    print(f"Size: {media_info.get('size', 'unknown')} bytes")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"command failed with exit code {exc.returncode}: {redact_command(exc.cmd)}") from exc
