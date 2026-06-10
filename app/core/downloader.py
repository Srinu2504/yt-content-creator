import os
import re
import tempfile
import yt_dlp
from app.core.config import AUDIO_DIR, MAX_VIDEO_DURATION_MINUTES


class DownloadError(Exception):
    pass


def extract_youtube_id(url):
    patterns = [r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise DownloadError(f"Could not extract YouTube ID from: {url}")


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


def _get_base_opts():
    """Base yt-dlp options applied to every request."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "extractor_retries": 3,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    cookies_file = _get_cookies_file()
    if cookies_file:
        opts["cookiefile"] = cookies_file
    return opts, cookies_file


def get_video_info(url):
    opts, cookies_file = _get_base_opts()
    opts["skip_download"] = True
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
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


def download_audio(url, video_id, progress_callback=None):
    info = get_video_info(url)

    duration_min = info["duration_sec"] / 60
    if duration_min > MAX_VIDEO_DURATION_MINUTES:
        raise DownloadError(
            f"Video is {duration_min:.0f} min. "
            f"Max allowed: {MAX_VIDEO_DURATION_MINUTES} min."
        )

    out_path = os.path.join(AUDIO_DIR, f"{video_id}.mp3")
    if os.path.exists(out_path):
        return out_path, info

    def _progress_hook(d):
        if progress_callback and d["status"] == "downloading":
            pct = d.get("_percent_str", "...").strip()
            progress_callback(f"Downloading audio: {pct}")

    # Try multiple format strings in order
    format_attempts = [
        "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "bestaudio/best",
        "worstaudio/bestaudio/best",
        "best",
    ]

    last_error = None

    for fmt in format_attempts:
        opts, cookies_file = _get_base_opts()
        opts.update({
            "format": fmt,
            "outtmpl": os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }],
            "progress_hooks": [_progress_hook],
            "prefer_free_formats": True,
        })

        try:
            if progress_callback:
                progress_callback(f"Trying format: {fmt}")
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            if os.path.exists(out_path):
                return out_path, info

        except Exception as e:
            last_error = str(e)
            if "Sign in" in str(e) or "bot" in str(e).lower():
                raise DownloadError(
                    f"YouTube blocked the request. "
                    f"Please upload fresh cookies.txt in the sidebar."
                )
            continue
        finally:
            if cookies_file and os.path.exists(cookies_file):
                os.remove(cookies_file)

    raise DownloadError(
        f"Could not download audio after trying all formats. "
        f"Last error: {last_error}"
    )
