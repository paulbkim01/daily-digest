#!/usr/bin/env python3
"""transcriber.py — Audio/video transcription for the research sweep pipeline.

Downloads YouTube captions or audio, transcribes via OpenRouter API, and
outputs structured JSON for scoring. Uses yt-dlp CLI (no Python import needed).

Subcommands:
    captions   Download YouTube auto-captions (free, no API cost)
    download   Download audio from URL via yt-dlp
    normalize  Convert audio to mono 16kHz WAV for transcription
    chunk      Split long audio into segments for API limits
    transcribe Transcribe an audio file via OpenRouter API
    search     Search YouTube for videos matching a query
    pipeline   Full chain: captions → fallback to download+transcribe
"""
from __future__ import annotations

import argparse
import base64
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_MODEL = "openai/gpt-audio-mini"
DEFAULT_SEGMENT_SECONDS = 600  # 10 minutes
DEFAULT_OUTPUT_DIR = "/tmp/transcriber"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

AUDIO_FORMAT_MAP = {
    "mp3": "mp3", "wav": "wav", "flac": "flac",
    "m4a": "m4a", "aac": "aac", "ogg": "ogg",
}


# ── Dependency checks ────────────────────────────────────────────────────────

def _require_ytdlp():
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: yt-dlp not installed. Run: uv tool install yt-dlp", file=sys.stderr)
        sys.exit(1)


def _require_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: ffmpeg not installed. Run: brew install ffmpeg", file=sys.stderr)
        sys.exit(1)


def _require_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return key


# ── VTT/SRT parsing ─────────────────────────────────────────────────────────

def parse_vtt(path: str) -> str:
    """Parse VTT/SRT subtitles to plain text, deduplicating repeated lines."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    text_parts: list[str] = []
    seen: set[str] = set()
    in_note = False

    for line in lines:
        line = line.strip()
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("NOTE"):
            in_note = True
            continue
        if in_note:
            if line == "":
                in_note = False
            continue
        if "-->" in line:
            continue
        if not line or line.isdigit():
            continue
        # Strip HTML/VTT formatting tags
        clean = re.sub(r"<[^>]+>", "", line)
        if clean and clean not in seen:
            seen.add(clean)
            text_parts.append(clean)

    return " ".join(text_parts)


def _find_subtitle_file(directory: str) -> str | None:
    """Find a .vtt or .srt subtitle file in a directory."""
    for ext in ("*.en.vtt", "*.en-orig.vtt", "*.vtt", "*.en.srt", "*.srt"):
        matches = glob.glob(os.path.join(directory, ext))
        if matches:
            return matches[0]
    return None


# ── yt-dlp CLI wrappers ─────────────────────────────────────────────────────

def _ytdlp_json(url: str, extra_args: list[str] | None = None) -> dict:
    """Run yt-dlp with --dump-json and return parsed metadata."""
    cmd = ["yt-dlp", "--no-warnings", "--dump-json", "--no-download"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _get_captions(url: str) -> tuple[dict, str | None]:
    """Try to get YouTube captions via yt-dlp CLI. Returns (metadata, transcript_text)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp", "--no-warnings",
            "--write-sub", "--write-auto-sub",
            "--sub-lang", "en", "--sub-format", "vtt",
            "--skip-download", "--print-json",
            "-o", outtmpl,
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)

        sub_file = _find_subtitle_file(tmpdir)
        transcript = parse_vtt(sub_file) if sub_file else None

        meta = {
            "title": info.get("title"),
            "url": info.get("webpage_url", url),
            "author": info.get("uploader"),
            "date": info.get("upload_date"),
            "duration": info.get("duration"),
        }
        return meta, transcript


def _download_audio(url: str, output_dir: str) -> dict:
    """Download audio from a URL via yt-dlp CLI. Returns metadata with file path."""
    outtmpl = os.path.join(output_dir, "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp", "--no-warnings",
        "-x", "--audio-format", "wav",
        "--no-playlist", "--print-json",
        "-o", outtmpl,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)

    video_id = info.get("id", "unknown")
    wav_path = os.path.join(output_dir, f"{video_id}.wav")

    # yt-dlp may name the file differently after postprocessing
    if not os.path.exists(wav_path):
        wavs = glob.glob(os.path.join(output_dir, "*.wav"))
        wav_path = wavs[0] if wavs else wav_path

    return {
        "path": wav_path,
        "title": info.get("title"),
        "url": info.get("webpage_url", url),
        "author": info.get("uploader"),
        "date": info.get("upload_date"),
        "duration": info.get("duration"),
    }


def _ytdlp_search(query: str, max_results: int = 10) -> list[dict]:
    """Search YouTube via yt-dlp CLI. Returns list of video metadata."""
    cmd = [
        "yt-dlp", "--no-warnings",
        "--dump-json", "--no-download",
        "--flat-playlist",
        f"ytsearch{max_results}:{query}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            entry = json.loads(line)
            videos.append({
                "title": entry.get("title"),
                "url": entry.get("url") or entry.get("webpage_url"),
                "author": entry.get("uploader") or entry.get("channel"),
                "date": entry.get("upload_date"),
                "duration": entry.get("duration"),
                "views": entry.get("view_count"),
                "description": (entry.get("description") or "")[:500],
            })
    return videos


# ── Audio processing helpers ─────────────────────────────────────────────────

def _normalize_audio(input_path: str, output_path: str) -> str:
    """Convert audio to mono 16kHz WAV for optimal speech recognition."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path],
        check=True, capture_output=True,
    )
    return output_path


def _chunk_audio(input_path: str, output_dir: str, segment_seconds: int = DEFAULT_SEGMENT_SECONDS) -> list[str]:
    """Split audio into fixed-length segments. Returns list of chunk paths."""
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", input_path],
        capture_output=True, text=True,
    )
    duration = float(json.loads(probe.stdout)["format"]["duration"])

    if duration <= segment_seconds:
        return [input_path]

    chunk_dir = os.path.join(output_dir, "chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    pattern = os.path.join(chunk_dir, f"{base}_%03d.wav")

    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-f", "segment",
         "-segment_time", str(segment_seconds), "-c", "copy", pattern],
        check=True, capture_output=True,
    )

    return sorted(glob.glob(os.path.join(chunk_dir, f"{base}_*.wav")))


def _transcribe_chunk(audio_path: str, model: str, api_key: str) -> str:
    """Transcribe a single audio chunk via OpenRouter API."""
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(audio_path)[1].lstrip(".").lower()
    audio_format = AUDIO_FORMAT_MAP.get(ext, "wav")

    payload = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Transcribe this audio accurately. Include speaker changes where detectable.",
                },
                {
                    "type": "input_audio",
                    "input_audio": {"data": audio_b64, "format": audio_format},
                },
            ],
        }],
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    return result["choices"][0]["message"]["content"]


# ── Subcommand handlers ──────────────────────────────────────────────────────

def cmd_captions(args):
    """Download YouTube captions (free, no API cost)."""
    _require_ytdlp()

    try:
        meta, transcript = _get_captions(args.url)
    except subprocess.CalledProcessError as e:
        json.dump({"transcript": None, "method": "captions", "error": e.stderr or str(e)}, sys.stdout, indent=2)
        return
    except Exception as e:
        json.dump({"transcript": None, "method": "captions", "error": str(e)}, sys.stdout, indent=2)
        return

    result = {**meta, "transcript": transcript, "method": "captions"}
    if not transcript:
        result["error"] = "No English captions available"
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)


def cmd_download(args):
    """Download audio from a URL via yt-dlp."""
    _require_ytdlp()
    _require_ffmpeg()

    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    meta = _download_audio(args.url, output_dir)
    json.dump(meta, sys.stdout, indent=2, ensure_ascii=False)


def cmd_normalize(args):
    """Convert audio to mono 16kHz WAV."""
    _require_ffmpeg()

    output_path = args.output or args.input.replace(".wav", "_16k.wav")
    _normalize_audio(args.input, output_path)

    size = os.path.getsize(output_path)
    json.dump({"path": output_path, "size_bytes": size}, sys.stdout, indent=2)


def cmd_chunk(args):
    """Split audio into segments for API limits."""
    _require_ffmpeg()

    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    chunks = _chunk_audio(args.input, output_dir, args.segment)
    json.dump({"chunks": chunks, "count": len(chunks)}, sys.stdout, indent=2)


def cmd_transcribe(args):
    """Transcribe an audio file via OpenRouter API."""
    api_key = _require_api_key()
    model = args.model or DEFAULT_MODEL

    transcript = _transcribe_chunk(args.input, model, api_key)
    json.dump({"transcript": transcript, "model": model}, sys.stdout, indent=2, ensure_ascii=False)


def cmd_search(args):
    """Search YouTube for videos matching a query."""
    _require_ytdlp()

    videos = _ytdlp_search(args.query, args.max_results)
    json.dump(videos, sys.stdout, indent=2, ensure_ascii=False)


def cmd_pipeline(args):
    """Full chain: try captions first, fall back to download+transcribe."""
    _require_ytdlp()

    url = args.url
    meta = None
    transcript = None
    method = None

    # Step 1: Try YouTube captions (free)
    try:
        meta, transcript = _get_captions(url)
        if transcript:
            method = "captions"
            print(f"Got captions for: {meta.get('title', url)}", file=sys.stderr)
    except Exception as e:
        print(f"Captions failed: {e}", file=sys.stderr)

    # Step 2: Fall back to audio download + OpenRouter transcription
    if not transcript:
        api_key = _require_api_key()
        _require_ffmpeg()
        model = args.model or DEFAULT_MODEL

        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Downloading audio from: {url}", file=sys.stderr)
            dl_meta = _download_audio(url, tmpdir)
            if meta is None:
                meta = dl_meta
            wav_path = dl_meta["path"]

            norm_path = os.path.join(tmpdir, "normalized.wav")
            _normalize_audio(wav_path, norm_path)

            chunks = _chunk_audio(norm_path, tmpdir, DEFAULT_SEGMENT_SECONDS)
            print(f"Transcribing {len(chunks)} chunk(s) via {model}...", file=sys.stderr)

            parts = []
            for i, chunk_path in enumerate(chunks):
                print(f"  Chunk {i + 1}/{len(chunks)}...", file=sys.stderr)
                text = _transcribe_chunk(chunk_path, model, api_key)
                parts.append(text)

            transcript = "\n\n".join(parts)
            method = "openrouter"

    result = {
        "title": meta.get("title") if meta else None,
        "url": meta.get("url", url) if meta else url,
        "author": meta.get("author") if meta else None,
        "date": meta.get("date") if meta else None,
        "duration": meta.get("duration") if meta else None,
        "transcript": transcript,
        "method": method,
        "source_tier": "7",
    }
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Audio/video transcription for the research sweep pipeline"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # captions
    p = sub.add_parser("captions", help="Download YouTube captions (free)")
    p.add_argument("url", help="YouTube video URL")
    p.set_defaults(func=cmd_captions)

    # download
    p = sub.add_parser("download", help="Download audio via yt-dlp")
    p.add_argument("url", help="Video/audio URL")
    p.add_argument("--output-dir", help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    p.set_defaults(func=cmd_download)

    # normalize
    p = sub.add_parser("normalize", help="Convert audio to mono 16kHz WAV")
    p.add_argument("input", help="Input audio file path")
    p.add_argument("--output", help="Output path (default: input_16k.wav)")
    p.set_defaults(func=cmd_normalize)

    # chunk
    p = sub.add_parser("chunk", help="Split audio into segments")
    p.add_argument("input", help="Input audio file path")
    p.add_argument("--segment", type=int, default=DEFAULT_SEGMENT_SECONDS,
                   help=f"Segment length in seconds (default: {DEFAULT_SEGMENT_SECONDS})")
    p.add_argument("--output-dir", help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    p.set_defaults(func=cmd_chunk)

    # transcribe
    p = sub.add_parser("transcribe", help="Transcribe audio via OpenRouter API")
    p.add_argument("input", help="Input audio file path")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p.set_defaults(func=cmd_transcribe)

    # search
    p = sub.add_parser("search", help="Search YouTube for videos")
    p.add_argument("query", help="Search query")
    p.add_argument("--max-results", type=int, default=10, help="Max results (default: 10)")
    p.set_defaults(func=cmd_search)

    # pipeline
    p = sub.add_parser("pipeline", help="Full chain: captions -> download+transcribe")
    p.add_argument("url", help="Video/audio URL")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
