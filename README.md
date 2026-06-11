# 🎬 YT Content Creator

> Turn any YouTube video into LinkedIn posts, articles, Twitter threads, and blog posts — free, instantly.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Whisper%20%2B%20Llama%203.3-F55036?style=flat-square)
![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

---

## ✨ Features

- 🎙️ **AI Transcription** — Transcribes any YouTube video using Groq Whisper large-v3-turbo
- 💼 **LinkedIn Post** — Punchy, engagement-optimised posts under 1300 characters
- 📝 **LinkedIn Article** — Long-form thought leadership articles (1000–1500 words)
- 🐦 **Twitter/X Thread** — Numbered tweet threads with hooks and insights
- 📖 **Blog Post** — SEO-structured Markdown blog posts (1200–1800 words)
- ⬇️ **Multiple Export Formats** — Download content as TXT, PDF, or DOCX
- 🗄️ **Smart Caching** — Transcripts and generated content saved to SQLite; re-processing the same URL skips download/transcription
- 📚 **History Page** — View, re-download, and delete all previously processed videos
- 🔒 **Secure API Handling** — API key stored in environment variables, never exposed in the UI
- ☁️ **One-click Railway Deploy** — Fully configured `railway.toml` and `nixpacks.toml`

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | Streamlit 1.58 | Web interface |
| Audio Download | yt-dlp 2026.3 | YouTube audio extraction |
| Transcription | Groq Whisper large-v3-turbo | Speech-to-text |
| Content Generation | Groq Llama 3.3 70B Versatile | LLM content writing |
| Database | SQLite (built-in) | Caching videos and content |
| PDF Export | ReportLab 4.5 | Styled PDF generation |
| DOCX Export | python-docx 1.2 | Word document generation |
| Large Audio | pydub 0.25 | Audio chunking for files > 24 MB |
| Config | python-dotenv 1.2 | Environment variable loading |
| Deployment | Railway + Nixpacks | Cloud hosting |
| Runtime | ffmpeg (via Nix) | Audio conversion |

---

## 📁 Project Structure

```
yt-content-creator-py/
│
├── app/                          # Application source code
│   ├── __init__.py
│   ├── main.py                   # Streamlit entry point — main page
│   │
│   ├── core/                     # Business logic
│   │   ├── __init__.py
│   │   ├── config.py             # Environment variables and path constants
│   │   ├── database.py           # SQLite helpers (CRUD operations)
│   │   ├── downloader.py         # yt-dlp wrapper for YouTube audio
│   │   ├── transcriber.py        # Groq Whisper transcription
│   │   └── content_engine.py     # Groq LLM content generation
│   │
│   ├── exporters/                # File export utilities
│   │   ├── __init__.py
│   │   └── exporter.py           # TXT, PDF, DOCX export functions
│   │
│   └── pages/                    # Additional Streamlit pages
│       ├── __init__.py
│       └── 02_history.py         # Past videos page
│
├── prompts/                      # System prompts for LLM
│   ├── linkedin_post.txt         # LinkedIn post generation prompt
│   ├── linkedin_article.txt      # LinkedIn article generation prompt
│   ├── twitter_thread.txt        # Twitter thread generation prompt
│   └── blog_post.txt             # Blog post generation prompt
│
├── data/                         # Runtime data (git-ignored)
│   ├── audio/                    # Temporary audio files (auto-deleted)
│   ├── transcripts/              # Reserved for future use
│   └── exports/                  # Reserved for future use
│
├── docs/                         # Project documentation
│   └── analysis.pdf              # Full project analysis report
│
├── .env                          # Local environment variables (git-ignored)
├── .gitignore                    # Git ignore rules
├── .railwayignore                # Railway deploy ignore rules
├── CLAUDE.md                     # AI assistant context file
├── README.md                     # This file
├── requirements.txt              # Python dependencies (pinned)
├── railway.toml                  # Railway deployment configuration
├── nixpacks.toml                 # Nixpacks build configuration
└── content_creator.db            # SQLite database (auto-created, git-ignored)
```

---

## 🚀 Getting Started (Local Setup)

### Prerequisites

- **Python 3.12** — [python.org/downloads](https://www.python.org/downloads/)
- **ffmpeg** — Required for audio conversion
  - Windows: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **Git** — [git-scm.com](https://git-scm.com/)
- **Groq API Key** — Free at [console.groq.com](https://console.groq.com)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/yt-content-creator-py.git
cd yt-content-creator-py
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Get your Groq API key**

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy your key (starts with `gsk_`)

**5. Create your `.env` file**
```bash
# Create .env in the project root
```
```env
GROQ_API_KEY=gsk_your_key_here
```

**6. Run the app**
```bash
# Windows
python -m streamlit run app/main.py

# macOS / Linux
PYTHONPATH=. streamlit run app/main.py
```

The app opens at **http://localhost:8501**

---

## ☁️ Deployment (Railway)

### Step-by-step Guide

**1. Push your code to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

**2. Create a Railway project**

1. Go to [railway.app](https://railway.app) and sign in
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repository

**3. Set environment variables**

In Railway → your service → **Variables**, add:

| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |
| `YOUTUBE_COOKIES` | *(Optional)* Netscape cookie format (see below) |

**4. Deploy**

Railway auto-detects `railway.toml` and `nixpacks.toml` and deploys automatically on every push to `main`.

**5. Get your public URL**

Railway → your service → **Settings** → **Domains** → Generate domain.

Your app is now live at `https://your-app.up.railway.app`.

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | **Yes** | — | Groq API key for Whisper + LLM. Get free at console.groq.com |
| `PORT` | Auto | — | Injected by Railway. Do not set manually. |
| `YOUTUBE_COOKIES` | No | — | Netscape-format YouTube cookies for bot bypass on cloud IPs |
| `APP_TITLE` | No | `YT Content Creator` | Browser tab title |
| `MAX_VIDEO_DURATION_MINUTES` | No | `60` | Maximum allowed video length in minutes |
| `WHISPER_MODEL` | No | `whisper-large-v3-turbo` | Override the Groq Whisper model |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Override the Groq LLM model |

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER FLOW                                │
└─────────────────────────────────────────────────────────────────┘

  1. Paste YouTube URL
          │
          ▼
  2. Normalize URL → https://www.youtube.com/watch?v={id}
          │
          ▼
  3. Check SQLite cache ──── HIT ────► Load transcript + skip to step 7
          │
         MISS
          │
          ▼
  4. yt-dlp downloads audio as MP3 (64kbps)
          │
          ▼
  5. Groq Whisper API transcribes audio → plain text
     (files > 24 MB are split into 10-min chunks)
          │
          ▼
  6. Save video + transcript to SQLite
     Delete audio file
          │
          ▼
  7. Show transcript (collapsible)
          │
          ▼
  8. For each selected format:
     Check cache → generate with Groq LLM → save to SQLite
          │
          ▼
  9. Render content + download as TXT / PDF / DOCX
```

---

## 📋 Content Formats

| Format | Model | Max Tokens | Typical Output |
|--------|-------|-----------|----------------|
| **LinkedIn Post** | Llama 3.3 70B | 600 | ~1300 characters, 1 punchy insight, 3 hashtags |
| **LinkedIn Article** | Llama 3.3 70B | 2500 | 1000–1500 words, structured with headings |
| **Twitter/X Thread** | Llama 3.3 70B | 1200 | 9 tweets, numbered, each ≤270 characters |
| **Blog Post** | Llama 3.3 70B | 3000 | 1200–1800 words, SEO-structured Markdown |

All formats use custom system prompts located in the `prompts/` folder — fully editable without touching any Python code.

---

## ⚠️ Known Limitations

- **YouTube bot detection** — Cloud server IPs (Railway, Render, etc.) are frequently flagged by YouTube. Set `YOUTUBE_COOKIES` with fresh browser cookies to bypass this.
- **Cookies export required for cloud** — Export cookies from Chrome using a browser extension (e.g. "Get cookies.txt LOCALLY") while logged into YouTube, then paste the content into `YOUTUBE_COOKIES` Railway variable.
- **60-minute video limit** — Configurable via `MAX_VIDEO_DURATION_MINUTES` env var. Longer videos produce larger audio files and may hit Groq's 25 MB limit.
- **Single-user SQLite** — The app uses SQLite which supports only one concurrent writer. Not suitable for multiple simultaneous users without migrating to PostgreSQL.
- **Groq free tier rate limits** — The free Groq tier has requests-per-minute limits. The app retries up to 3 times on rate limit errors with exponential backoff.
- **ffmpeg required** — Must be installed on the server/local machine for audio conversion. Handled automatically on Railway via `nixpacks.toml`.

---

## 🔧 Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `YouTube blocked this request as a bot` | Cloud IP flagged by YouTube | Set `YOUTUBE_COOKIES` in Railway Variables with fresh exported cookies |
| `GROQ_API_KEY is not set` | Missing API key | Add `GROQ_API_KEY=gsk_...` to `.env` locally or Railway Variables |
| `ffmpeg not found` / audio conversion fails | ffmpeg not installed | Install ffmpeg: `winget install ffmpeg` (Windows) or `brew install ffmpeg` (Mac) |
| `Could not extract YouTube ID` | Unsupported or malformed URL | Use a standard `youtube.com/watch?v=` or `youtu.be/` URL |
| `Transcription failed: 413` | Audio file > 25 MB | Reduce `MAX_VIDEO_DURATION_MINUTES` or use a shorter video |
| `LLM failed after 3 attempts` | Groq rate limit exhausted | Wait a minute and try again, or upgrade to Groq paid tier |
| `ModuleNotFoundError: app` | `PYTHONPATH` not set | Run as `PYTHONPATH=. streamlit run app/main.py` or set `PYTHONPATH` env var |
| `Video is X min. Max allowed: 60 min` | Video too long | Set `MAX_VIDEO_DURATION_MINUTES=120` in `.env` |
| PDF download crashes | Special characters in content | Fixed in current version; update to latest code |

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and test locally
4. Commit: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

**Guidelines:**
- Keep prompt files in `prompts/` — no hardcoded prompts in Python
- All config values via environment variables — no hardcoded keys or paths
- New content formats: add generator in `content_engine.py`, prompt in `prompts/`, entry in `format_map` in `main.py`
- Run `python -m py_compile app/**/*.py` before submitting

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 👤 Author

**Your Name**  
GitHub: [@Srinu2504](https://github.com/Srinu2504)

---

<div align="center">
  <sub>Built with ❤️ using Streamlit + Groq · Free to use · Deploy in minutes</sub>
</div>
