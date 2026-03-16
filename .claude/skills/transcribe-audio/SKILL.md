---
name: transcribe-audio
version: 1.0.0
description: |
  Transcribe YouTube videos, podcasts, and audio files for the research sweep pipeline.
  Downloads captions (free) or extracts audio and transcribes via OpenRouter API. Use this
  skill when the user wants to transcribe a video or podcast, says things like "transcribe
  this video", "get the transcript", "what did they say in this podcast", "transcribe this
  episode", or provides a YouTube/podcast URL and wants a transcript or content analysis.
---

# Transcribe Audio

Transcribe YouTube videos, podcasts, and audio files. Tries free YouTube captions first,
falls back to audio download + OpenRouter transcription.

## Prerequisites

- **yt-dlp**: `pip install yt-dlp`
- **ffmpeg**: `brew install ffmpeg` (needed for audio extraction and normalization)
- **OPENROUTER_API_KEY**: Environment variable (only needed when captions unavailable)

## Instructions

### Single video/podcast transcript

Use `transcriber.py pipeline` for the full chain:

```bash
python3 transcriber.py pipeline "https://youtube.com/watch?v=VIDEO_ID"
```

This will:
1. Try YouTube auto-captions first (free, fast)
2. If no captions: download audio, normalize to 16kHz mono WAV, chunk into 10-min segments
3. Transcribe each chunk via OpenRouter (`openai/gpt-audio-mini` by default, ~$0.58/hr)
4. Return JSON with title, URL, author, date, duration, transcript, and method used

### Search for videos first

```bash
python3 transcriber.py search "AI engineering podcast 2026" --max-results 5
```

Returns JSON array with title, URL, author, date, duration, views, description.

### Just get captions (free, no API cost)

```bash
python3 transcriber.py captions "https://youtube.com/watch?v=VIDEO_ID"
```

### Transcribe a local audio file

```bash
python3 transcriber.py transcribe /path/to/audio.wav --model openai/gpt-audio-mini
```

### Individual steps (for debugging or custom workflows)

```bash
# Download audio only
python3 transcriber.py download "https://youtube.com/watch?v=VIDEO_ID"

# Normalize to 16kHz mono
python3 transcriber.py normalize /tmp/transcriber/VIDEO_ID.wav

# Split into 10-minute chunks
python3 transcriber.py chunk /tmp/transcriber/VIDEO_ID_16k.wav --segment 600

# Transcribe one chunk
python3 transcriber.py transcribe /tmp/transcriber/chunks/VIDEO_ID_16k_000.wav
```

## Integration with Research Sweep

When scanning Tier 7 (YouTube & Podcasts) as part of a full sweep:

1. **Fetch feed** to get recent video URLs:
   ```bash
   python3 feed_parser.py fetch --tier 7 --since 7d
   ```

2. **For each video URL**, get transcript:
   ```bash
   python3 transcriber.py pipeline "$VIDEO_URL"
   ```

3. **Score using transcript content** — the transcript field gives the scoring agent
   actual content to evaluate, not just titles and descriptions.

4. Items go through the normal `sweep.py pipeline` for scoring, dedup, and formatting.

### Batch processing in sweep

When processing multiple Tier 7 items, launch parallel Agent subprocesses:
- Use `captions` first for YouTube videos (fast, free)
- Only fall back to `pipeline` (with audio download) for items without captions
- Skip videos longer than 3 hours to avoid excessive API costs

## Model Options

| Model | Cost (input) | Best for |
|-------|-------------|----------|
| `openai/gpt-audio-mini` | $0.60/M tokens | Default. Good accuracy, cheap for bulk transcription |
| `openai/gpt-audio` | $32/M tokens | Best accuracy, use for high-value content only |
| `google/gemini-2.5-flash` | varies | Alternative, good for long audio |

Override the model: `--model google/gemini-2.5-flash`

## Output Schema

All subcommands output JSON to stdout. The `pipeline` command returns:

```json
{
  "title": "Episode Title",
  "url": "https://youtube.com/watch?v=...",
  "author": "Channel Name",
  "date": "20260315",
  "duration": 3600,
  "transcript": "Full transcript text...",
  "method": "captions",
  "source_tier": "7"
}
```

The `method` field indicates how the transcript was obtained:
- `"captions"` — YouTube auto-captions (free)
- `"openrouter"` — Audio download + API transcription (paid)

## Error Handling

- No yt-dlp: Clear error with install instructions
- No ffmpeg: Clear error with install instructions
- No OPENROUTER_API_KEY: Only fails when captions unavailable
- No captions + no API key: Exits with error message
- Network errors: Reported in JSON output `error` field
