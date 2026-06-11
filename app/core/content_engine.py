import os
from groq import Groq
from app.core.config import GROQ_API_KEY, LLM_MODEL, PROMPTS_DIR


class GenerationError(Exception):
    pass


def _load_prompt(filename):
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(path):
        raise GenerationError(f"Prompt file not found: {path}")
    with open(path) as f:
        return f.read()


def _call_llm(system_prompt, user_message, max_tokens=2048):
    if not GROQ_API_KEY:
        raise GenerationError("GROQ_API_KEY is not set.")

    client = Groq(api_key=GROQ_API_KEY)
    last_error = None

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = str(e)
            if "429" in str(e) or "rate" in str(e).lower():
                import time
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            raise GenerationError(f"LLM call failed: {e}")

    raise GenerationError(f"LLM failed after 3 attempts: {last_error}")


def _truncate_transcript(transcript, max_chars=12000):
    if len(transcript) <= max_chars:
        return transcript
    front = int(max_chars * 0.8)
    back = max_chars - front
    return transcript[:front] + "\n\n[...middle section truncated...]\n\n" + transcript[-back:]


def generate_linkedin_post(transcript, title):
    system = _load_prompt("linkedin_post.txt")
    user = f"Video title: {title}\n\nTranscript:\n{_truncate_transcript(transcript)}"
    return _call_llm(system, user, max_tokens=600)


def generate_linkedin_article(transcript, title):
    system = _load_prompt("linkedin_article.txt")
    user = f"Video title: {title}\n\nTranscript:\n{_truncate_transcript(transcript, 14000)}"
    return _call_llm(system, user, max_tokens=2500)


def generate_twitter_thread(transcript, title):
    system = _load_prompt("twitter_thread.txt")
    user = f"Video title: {title}\n\nTranscript:\n{_truncate_transcript(transcript)}"
    return _call_llm(system, user, max_tokens=1200)


def generate_blog_post(transcript, title):
    system = _load_prompt("blog_post.txt")
    user = f"Video title: {title}\n\nTranscript:\n{_truncate_transcript(transcript, 14000)}"
    return _call_llm(system, user, max_tokens=3000)
