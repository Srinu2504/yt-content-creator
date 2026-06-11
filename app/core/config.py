import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
APP_TITLE = os.getenv("APP_TITLE", "YT Content Creator")
try:
    MAX_VIDEO_DURATION_MINUTES = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "60"))
except (ValueError, TypeError):
    MAX_VIDEO_DURATION_MINUTES = 60
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
DB_PATH = os.path.join(BASE_DIR, "content_creator.db")

for d in [AUDIO_DIR, TRANSCRIPTS_DIR, EXPORTS_DIR]:
    os.makedirs(d, exist_ok=True)
