import streamlit as st
import os
from app.core.config import APP_TITLE, GROQ_API_KEY
from app.core.database import init_db, save_video, get_video_by_url, save_content, get_content_for_video
from app.core.downloader import download_audio, extract_youtube_id, DownloadError
from app.core.transcriber import transcribe_audio, TranscriptionError
from app.core.content_engine import (
    generate_linkedin_post, generate_linkedin_article,
    generate_twitter_thread, generate_blog_post, GenerationError
)
from app.exporters.exporter import export_txt, export_pdf, export_docx

init_db()

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + title
    st.markdown("### 🎬 YT Content Creator")
    st.caption("Turn any YouTube video into polished content — free.")
    st.divider()

    # Navigation
    st.page_link("main.py", label="➕  New Video")
    st.page_link("pages/02_history.py", label="📚  Past Videos")

    st.divider()

    # API key status — never shown, only status
    api_key = os.environ.get("GROQ_API_KEY", GROQ_API_KEY)
    if api_key:
        st.markdown("""
        <div class="api-badge">
            🔐 &nbsp;<strong>API Key secured</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("GROQ_API_KEY not set.\nAdd it in Railway Variables.")

    st.divider()
    st.caption("Groq Whisper large-v3-turbo\nLlama 3.3 70B · Free tier · No GPU")

# ── Main page ─────────────────────────────────────────────────────────────────
# Hero badge
st.markdown("""
<div class="hero-badge">
    ✦ AI-powered · 100% free · Groq API
</div>
""", unsafe_allow_html=True)

st.title("YouTube → Content, instantly")
st.caption("Transcribe any video · Generate LinkedIn posts, articles, Twitter threads & blog posts")

st.divider()

# URL input
url_input = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

# Format selector + button
formats_col, btn_col = st.columns([3, 1])
with formats_col:
    selected_formats = st.multiselect(
        "Formats",
        ["LinkedIn Post", "LinkedIn Article", "Twitter Thread", "Blog Post"],
        default=["LinkedIn Post", "Twitter Thread"],
        label_visibility="collapsed",
    )
with btn_col:
    run_btn = st.button("Generate ✨", type="primary", use_container_width=True)

st.divider()

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run_btn:
    if not url_input.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()
    if not os.environ.get("GROQ_API_KEY", GROQ_API_KEY):
        st.error("GROQ_API_KEY is not set. Add it in Railway → Variables.")
        st.stop()
    if not selected_formats:
        st.error("Select at least one content format.")
        st.stop()

    url = url_input.strip()
    cached = get_video_by_url(url)

    if cached:
        transcript = cached["transcript"] or ""
        if not transcript:
            st.warning("Cached video has no transcript. Re-processing...")
        else:
            st.info(f"Loaded from cache: **{cached['title']}**")
            video_id = cached["id"]
            title = cached["title"]

    if not cached or not (cached["transcript"] or ""):
        status = st.status("Starting pipeline...", expanded=True)
        try:
            yt_id = extract_youtube_id(url)

            def update_status(msg):
                status.write(msg)

            # Step 1 — Download
            status.update(label="⬇️ Downloading audio...")
            audio_path, info = download_audio(url, yt_id, progress_callback=update_status)
            status.write(f"✅ Downloaded: **{info['title']}** ({info['duration_sec']//60} min)")

            # Step 2 — Transcribe
            status.update(label="🎙️ Transcribing with Groq Whisper...")
            status.write("Sending audio to Groq Whisper API...")
            transcript = transcribe_audio(audio_path)
            status.write(f"✅ Transcribed: **{len(transcript.split())} words**")

            # Save to DB
            video_id = save_video(
                url, yt_id, info["title"], info["channel"],
                info["duration_sec"], transcript
            )
            title = info["title"]

            # Cleanup audio
            if os.path.exists(audio_path):
                os.remove(audio_path)

            status.update(label="✅ Transcription complete!", state="complete")

        except DownloadError as e:
            status.update(label="Download failed", state="error")
            st.error(str(e))
            st.stop()
        except TranscriptionError as e:
            status.update(label="Transcription failed", state="error")
            st.error(str(e))
            st.stop()

    # ── Show transcript ───────────────────────────────────────────────────────
    st.subheader("📝 Transcript")
    with st.expander("View full transcript", expanded=False):
        st.text_area(
            "Transcript text",
            transcript,
            height=300,
            label_visibility="collapsed"
        )
        st.caption(f"Words: {len(transcript.split())}  ·  Characters: {len(transcript)}")
        st.download_button(
            "⬇️ Download transcript (TXT)",
            transcript.encode("utf-8"),
            file_name=f"{title[:40]}_transcript.txt",
            mime="text/plain",
            key="transcript_dl"
        )

    st.divider()

    # ── Generate content ──────────────────────────────────────────────────────
    st.subheader(f"✨ Generated content for: {title}")

    format_map = {
        "LinkedIn Post":    ("linkedin_post",    generate_linkedin_post),
        "LinkedIn Article": ("linkedin_article", generate_linkedin_article),
        "Twitter Thread":   ("twitter_thread",   generate_twitter_thread),
        "Blog Post":        ("blog_post",         generate_blog_post),
    }

    icons = {
        "LinkedIn Post":    "💼",
        "LinkedIn Article": "📝",
        "Twitter Thread":   "🐦",
        "Blog Post":        "📖",
    }

    existing = get_content_for_video(video_id)

    for fmt in selected_formats:
        fmt_key, gen_fn = format_map[fmt]
        icon = icons[fmt]

        with st.expander(f"{icon}  {fmt}", expanded=True):
            if fmt_key in existing:
                content = existing[fmt_key]["content"]
                st.caption("✅ Loaded from cache")
            else:
                with st.spinner(f"Writing {fmt}..."):
                    try:
                        content = gen_fn(transcript, title)
                        save_content(video_id, fmt_key, content)
                    except GenerationError as e:
                        st.error(str(e))
                        continue

            st.markdown(content)
            st.caption(f"Words: {len(content.split())}  ·  Characters: {len(content)}")
            st.divider()

            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40]
            fname = f"{safe_title}_{fmt_key}"

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.download_button(
                    "⬇️ TXT", export_txt(content),
                    file_name=f"{fname}.txt", mime="text/plain",
                    use_container_width=True, key=f"txt_{fmt_key}"
                )
            with c2:
                try:
                    st.download_button(
                        "⬇️ PDF", export_pdf(content, f"{fmt} — {title}"),
                        file_name=f"{fname}.pdf", mime="application/pdf",
                        use_container_width=True, key=f"pdf_{fmt_key}"
                    )
                except Exception:
                    st.button("PDF N/A", disabled=True,
                              use_container_width=True, key=f"pdf_{fmt_key}")
            with c3:
                try:
                    st.download_button(
                        "⬇️ DOCX", export_docx(content, f"{fmt} — {title}"),
                        file_name=f"{fname}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True, key=f"docx_{fmt_key}"
                    )
                except Exception:
                    st.button("DOCX N/A", disabled=True,
                              use_container_width=True, key=f"docx_{fmt_key}")
            with c4:
                if st.button("📋 Copy", use_container_width=True, key=f"copy_{fmt_key}"):
                    st.session_state[f"show_copy_{fmt_key}"] = True
            if st.session_state.get(f"show_copy_{fmt_key}"):
                st.code(content, language=None)
                st.caption("Select all text above and copy manually (Ctrl+A, Ctrl+C)")
