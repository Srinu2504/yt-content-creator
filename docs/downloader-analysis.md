# YT Content Creator — `app/core/downloader.py` Analysis

Generated: 2026-06-09

---

## 1. Current format string for yt-dlp

In `download_audio()`, the format option is:

```
bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best
```

`get_video_info()` does **not** set a format. It only fetches metadata with `skip_download: True`.

---

## 2. Fallback format handling

### Implicit fallback (format chain)

The `/` separators define a priority chain. yt-dlp tries each selector left-to-right until one matches:

| Priority | Selector                    | Meaning                                      |
|----------|-----------------------------|----------------------------------------------|
| 1        | `bestaudio[ext=m4a]`        | Best audio stream in M4A container           |
| 2        | `bestaudio[ext=webm]`       | Best audio stream in WebM container          |
| 3        | `bestaudio`                 | Best audio-only stream (any container)       |
| 4        | `best`                      | Best overall stream (video+audio if needed)  |

### Additional format tuning

```python
"format_sort": ["abr", "asr"],
"prefer_free_formats": True,
```

- **format_sort** — When multiple streams match, prefer higher audio bitrate (`abr`), then sample rate (`asr`).
- **prefer_free_formats** — Favor non-proprietary containers when quality is tied.

### What is NOT implemented

- No Python retry loop with alternate format strings
- No explicit catch/retry for `"Requested format is not available"`
- No cached-file bypass for format errors (only skips download if `{video_id}.mp3` already exists)

If all selectors fail, yt-dlp raises an exception, which is wrapped as `DownloadError`.

---

## 3. How cookies are loaded and passed to yt-dlp

### `_get_cookies_file()` flow

1. Read `YOUTUBE_COOKIES` from `os.environ` (not directly from `.env` in this module).
2. `.strip()` whitespace; return `None` if empty.
3. Write content to a temporary file:
   - Mode: `w`
   - Suffix: `.txt`
   - Encoding: `utf-8`
   - `delete=False` (manual cleanup later)
4. On write failure, log and return `None`.

Expected content format: **Netscape cookies file** (what browser extensions export).

### Where cookies are attached

Both `get_video_info()` and `download_audio()` call `_get_cookies_file()` independently:

```python
cookies_file = _get_cookies_file()
if cookies_file:
    opts["cookiefile"] = cookies_file
```

### Cleanup

Both functions delete the temp file in a `finally` block:

```python
finally:
    if cookies_file and os.path.exists(cookies_file):
        os.remove(cookies_file)
```

### Important note

A full `download_audio()` run creates and deletes cookies **twice** — once in `get_video_info()` (called first) and again in `download_audio()` itself.

---

## 4. Where `"Requested format is not available"` can be triggered

### Primary location — `download_audio()`

```python
with yt_dlp.YoutubeDL(opts) as ydl:
    try:
        ydl.download([url])
    except Exception as e:
        raise DownloadError(f"Download failed: {e}")
```

yt-dlp raises this when **none** of the format selectors match available streams.

**Common causes:**
- Video has no accessible audio-only formats
- Formats are geo-blocked or age-restricted
- YouTube changed available formats for the video
- Bot detection blocked format listing (partial failure)

**User sees:** `Download failed: Requested format is not available`

### Secondary location — `get_video_info()`

```python
info = ydl.extract_info(url, download=False)
```

Less common with `skip_download: True`, but possible if format resolution fails during metadata extraction.

**User sees:** `Could not fetch video info: Requested format is not available`

### Post-download check

```python
if not os.path.exists(out_path):
    raise DownloadError("Audio file not found after download.")
```

This is a different error — file missing after download, not the yt-dlp format error.

---

## 5. Where `"Sign in to confirm you're not a bot"` can be triggered

YouTube returns this when it treats the request as automated/bot traffic.

### Location 1 — `get_video_info()` (most likely first failure)

```python
info = ydl.extract_info(url, download=False)
```

**User sees:** `Could not fetch video info: Sign in to confirm you're not a bot`

Since `download_audio()` calls `get_video_info()` first, the pipeline often fails here before any download starts.

### Location 2 — `download_audio()`

```python
ydl.download([url])
```

**User sees:** `Download failed: Sign in to confirm you're not a bot`

### Mitigation

Set `YOUTUBE_COOKIES` environment variable with valid exported browser cookies. Especially important on:
- Cloud hosts (Railway, Render, etc.)
- Datacenter IP addresses
- High-volume or repeated requests

---

## 6. Full current function source

### `get_video_info()`

```python
def get_video_info(url):
    cookies_file = _get_cookies_file()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title", "Unknown"),
                "channel": info.get("uploader", "Unknown"),
                "duration_sec": info.get("duration", 0),
            }
        except Exception as e:
            raise DownloadError(f"Could not fetch video info: {e}")
        finally:
            if cookies_file and os.path.exists(cookies_file):
                os.remove(cookies_file)
```

### `download_audio()`

```python
def download_audio(url, video_id, progress_callback=None):
    info = get_video_info(url)
    duration_min = info["duration_sec"] / 60
    if duration_min > MAX_VIDEO_DURATION_MINUTES:
        raise DownloadError(
            f"Video is {duration_min:.0f} min. Max allowed: {MAX_VIDEO_DURATION_MINUTES} min."
        )

    out_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")
    if os.path.exists(out_path):
        return out_path, info

    def _progress_hook(d):
        if progress_callback and d["status"] == "downloading":
            pct = d.get("_percent_str", "...").strip()
            progress_callback(f"Downloading audio: {pct}")

    cookies_file = _get_cookies_file()

    opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "64",
        }],
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
        "format_sort": ["abr", "asr"],
        "prefer_free_formats": True,
    }

    if cookies_file:
        opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            raise DownloadError(f"Download failed: {e}")
        finally:
            if cookies_file and os.path.exists(cookies_file):
                os.remove(cookies_file)

    if not os.path.exists(out_path):
        raise DownloadError("Audio file not found after download.")

    return out_path, info
```

### `_get_cookies_file()` (reference)

```python
def _get_cookies_file():
    cookies_content = os.environ.get("YOUTUBE_COOKIES", "").strip()
    if not cookies_content:
        return None
    try:
        tmp = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        )
        tmp.write(cookies_content)
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"Cookie file creation failed: {e}")
        return None
```

---

## Error flow summary

```
download_audio(url)
    │
    ├─► get_video_info(url)
    │       └─► ydl.extract_info()
    │               ├─ Bot error → DownloadError("Could not fetch video info: ...")
    │               └─ Format error (rare) → DownloadError("Could not fetch video info: ...")
    │
    ├─► Duration check → DownloadError if too long
    │
    ├─► Cached .mp3 exists? → return early
    │
    └─► ydl.download()
            ├─ Bot error → DownloadError("Download failed: ...")
            ├─ Format error → DownloadError("Download failed: Requested format is not available")
            └─ Missing output file → DownloadError("Audio file not found after download.")
```

---

## Environment variables

| Variable            | Used by              | Purpose                          |
|---------------------|----------------------|----------------------------------|
| `YOUTUBE_COOKIES`   | `_get_cookies_file()`| Netscape-format cookies for YouTube |
| `MAX_VIDEO_DURATION_MINUTES` | `config.py` → `download_audio()` | Max allowed video length |

---

*File: `app/core/downloader.py`*
