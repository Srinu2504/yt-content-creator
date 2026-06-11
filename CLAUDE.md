# Project: YT Content Creator

## Stack
- Python + Streamlit (UI)
- Groq Whisper large-v3-turbo (transcription)
- Groq Llama 3.3 70B (content generation)
- yt-dlp (YouTube audio download)
- SQLite (database)
- Railway (deployment)
- reportlab + python-docx (exports)

## Key files
- app/main.py — Streamlit UI entry point
- app/core/downloader.py — yt-dlp wrapper
- app/core/transcriber.py — Groq Whisper
- app/core/content_engine.py — Groq LLM
- app/core/database.py — SQLite helpers
- app/exporters/exporter.py — TXT, PDF, DOCX

## Rules
- Run with: python -m streamlit run app/main.py
- Always activate venv first: venv\Scripts\activate
- PYTHONPATH must include project root
- Never hardcode API keys
- All environment variables go in .env locally, Railway Variables in production
