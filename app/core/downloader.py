import os
import re
import tempfile
import yt_dlp
from app.core.config import AUDIO_DIR, MAX_VIDEO_DURATION_MINUTES


def _get_cookies_file():
    cookies_content = os.environ.get("YOUTUBE_COOKIES", "")
    if not cookies_content:
        return None
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name


class DownloadError(Exception):
    pass


def extract_youtube_id(url):
    patterns = [r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise DownloadError(f"Could not extract YouTube ID from: {url}")


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

    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
        "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
        "ignoreerrors": False,
        "format_sort": ["abr", "asr"],
    }
    cookies_file = _get_cookies_file()
    if cookies_file:
        opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            raise DownloadError(f"Download failed: {e}")

    if not os.path.exists(out_path):
        raise DownloadError("Audio file not found after download.")

    return out_path, info
