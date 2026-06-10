import streamlit as st
import os
from app.core.config import APP_TITLE, GROQ_API_KEY
from app.core.database import (init_db, save_video, get_video_by_url,
                                save_content, get_content_for_video)
from app.core.downloader import download_audio, extract_youtube_id, DownloadError
from app.core.transcriber import transcribe_audio, TranscriptionError
from app.core.content_engine import (
    generate_linkedin_post, generate_linkedin_article,
    generate_twitter_thread, generate_blog_post, GenerationError)
from app.exporters.exporter import export_txt, export_pdf, export_docx

init_db()

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("🎬 YT Content Creator")
    st.caption("Turn any YouTube video into polished content — free.")
    st.divider()
    if GROQ_API_KEY:
        st.success("API Key loaded ✅", icon="🔐")
    else:
        st.error("GROQ_API_KEY not set in environment")
    st.divider()
    st.page_link("main.py", label="New Video", icon="➕")
    st.page_link("pages/02_history.py", label="Past Videos", icon="📚")
    st.divider()
    st.caption("Groq Whisper + Llama 3.3 70B\nFree tier · No GPU needed")

st.title("🎬 Turn any YouTube video into content")
st.caption("Paste a URL → get LinkedIn post, article, Twitter thread, and blog post.")

url_input = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

formats_col, btn_col = st.columns([3, 1])
with formats_col:
    selected_formats = st.multiselect(
        "Generate",
        ["LinkedIn Post", "LinkedIn Article", "Twitter Thread", "Blog Post"],
        default=["LinkedIn Post", "Twitter Thread"],
        label_visibility="collapsed",
    )
with btn_col:
    run_btn = st.button("Generate ✨", type="primary", use_container_width=True)

st.divider()

if run_btn:
    if not url_input.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()
    if not os.environ.get("GROQ_API_KEY"):
        st.error("Add your Groq API key in the sidebar.")
        st.stop()
    if not selected_formats:
        st.error("Select at least one content format.")
        st.stop()

    url = url_input.strip()
    cached = get_video_by_url(url)

    if cached:
        st.info(f"Found cached transcript for: **{cached['title']}**")
        transcript = cached["transcript"]
        video_id = cached["id"]
        title = cached["title"]
    else:
        status = st.status("Starting...", expanded=True)
        try:
            yt_id = extract_youtube_id(url)

            def update_status(msg):
                status.write(msg)

            status.update(label="Downloading audio...")
            audio_path, info = download_audio(url, yt_id, update_status)
            status.write(f"✅ Downloaded: **{info['title']}** ({info['duration_sec']//60} min)")

            status.update(label="Transcribing with Groq Whisper...")
            status.write("Sending to Groq Whisper API...")
            transcript = transcribe_audio(audio_path)
            status.write(f"✅ Transcribed: {len(transcript.split())} words")

            video_id = save_video(url, yt_id, info["title"], info["channel"],
                                  info["duration_sec"], transcript)
            title = info["title"]

            if os.path.exists(audio_path):
                os.remove(audio_path)

            status.update(label="✅ Transcription complete!", state="complete")

            st.subheader("📝 Transcript")
            with st.expander("View full transcript", expanded=False):
                st.text_area("Transcript", transcript, height=300,
                             label_visibility="collapsed")
                st.caption(f"Words: {len(transcript.split())} · Characters: {len(transcript)}")
                st.download_button(
                    "⬇ Download Transcript (TXT)",
                    transcript.encode("utf-8"),
                    file_name=f"{title}_transcript.txt",
                    mime="text/plain",
                    key="transcript_download"
                )

            st.divider()

        except DownloadError as e:
            st.error(f"Download failed: {e}")
            st.stop()
        except TranscriptionError as e:
            st.error(f"Transcription failed: {e}")
            st.stop()

    st.subheader(f"Generating content for: {title}")

    format_map = {
        "LinkedIn Post":    ("linkedin_post",    generate_linkedin_post),
        "LinkedIn Article": ("linkedin_article", generate_linkedin_article),
        "Twitter Thread":   ("twitter_thread",   generate_twitter_thread),
        "Blog Post":        ("blog_post",         generate_blog_post),
    }

    existing = get_content_for_video(video_id)

    for fmt in selected_formats:
        fmt_key, gen_fn = format_map[fmt]
        icon = {"LinkedIn Post": "💼", "LinkedIn Article": "📝",
                "Twitter Thread": "🐦", "Blog Post": "📖"}[fmt]

        with st.expander(f"{icon} {fmt}", expanded=True):
            if fmt_key in existing:
                content = existing[fmt_key]["content"]
                st.caption("Loaded from cache")
            else:
                with st.spinner(f"Writing {fmt}..."):
                    try:
                        content = gen_fn(transcript, title)
                        save_content(video_id, fmt_key, content)
                    except GenerationError as e:
                        st.error(str(e))
                        continue

            st.markdown(content)
            st.divider()

            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40]
            fname = f"{safe_title}_{fmt_key}"
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.download_button("⬇ TXT", export_txt(content),
                    file_name=f"{fname}.txt", mime="text/plain",
                    use_container_width=True, key=f"txt_{fmt_key}")
            with c2:
                st.download_button("⬇ PDF",
                    export_pdf(content, f"{fmt} — {title}"),
                    file_name=f"{fname}.pdf", mime="application/pdf",
                    use_container_width=True, key=f"pdf_{fmt_key}")
            with c3:
                st.download_button("⬇ DOCX",
                    export_docx(content, f"{fmt} — {title}"),
                    file_name=f"{fname}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True, key=f"docx_{fmt_key}")
            with c4:
                if st.button("📋 Copy", use_container_width=True, key=f"copy_{fmt_key}"):
                    st.code(content, language=None)
