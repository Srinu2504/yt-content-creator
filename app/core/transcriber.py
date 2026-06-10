import os
from groq import Groq
from app.core.config import GROQ_API_KEY, WHISPER_MODEL


class TranscriptionError(Exception):
    pass


def transcribe_audio(audio_path):
    if not GROQ_API_KEY:
        raise TranscriptionError("GROQ_API_KEY is not set. Add it to your .env file.")

    if not os.path.exists(audio_path):
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    if file_size_mb > 24:
        return _transcribe_large_file(audio_path)

    client = Groq(api_key=GROQ_API_KEY)

    with open(audio_path, "rb") as f:
        try:
            result = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f),
                model=WHISPER_MODEL,
                response_format="text",
                temperature=0.0,
            )
            return str(result).strip()
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")


def _transcribe_large_file(audio_path):
    try:
        from pydub import AudioSegment
    except ImportError:
        raise TranscriptionError("pydub is required for large files: pip install pydub")

    audio = AudioSegment.from_mp3(audio_path)
    chunk_ms = 10 * 60 * 1000
    chunks = [audio[i:i + chunk_ms] for i in range(0, len(audio), chunk_ms)]

    transcripts = []
    base = os.path.splitext(audio_path)[0]

    for i, chunk in enumerate(chunks):
        chunk_path = f"{base}_chunk_{i}.mp3"
        chunk.export(chunk_path, format="mp3", bitrate="64k")
        try:
            text = transcribe_audio(chunk_path)
            transcripts.append(text)
        finally:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

    return " ".join(transcripts)
