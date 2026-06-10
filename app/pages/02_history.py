import streamlit as st
from app.core.database import init_db, get_all_videos, get_content_for_video, delete_video
from app.exporters.exporter import export_txt, export_pdf, export_docx

init_db()

st.set_page_config(page_title="Past Videos", page_icon="📚", layout="wide")
st.title("📚 Past Videos")
st.caption("All previously transcribed videos.")

videos = get_all_videos()

if not videos:
    st.info("No videos yet. Go to the home page and paste a YouTube URL to get started.")
    st.stop()

st.caption(f"{len(videos)} video(s) processed")
st.divider()

for video in videos:
    vid = dict(video)
    with st.expander(f"**{vid['title']}** — {vid['channel']} · {vid['duration_sec']//60} min"):
        st.caption(f"URL: {vid['youtube_url']}")
        st.caption(f"Transcribed: {vid['created_at'][:10]}")

        if vid["transcript"]:
            with st.expander("Show transcript"):
                st.text_area("Transcript", vid["transcript"], height=200,
                             label_visibility="collapsed")

        existing = get_content_for_video(vid["id"])

        if existing:
            fmt_labels = {
                "linkedin_post": "💼 LinkedIn Post",
                "linkedin_article": "📝 LinkedIn Article",
                "twitter_thread": "🐦 Twitter Thread",
                "blog_post": "📖 Blog Post",
            }
            tabs = st.tabs([fmt_labels.get(k, k) for k in existing.keys()])
            for tab, (fmt_key, item) in zip(tabs, existing.items()):
                with tab:
                    st.markdown(item["content"])
                    st.divider()
                    safe_title = "".join(c for c in vid['title']
                                        if c.isalnum() or c in " _-")[:40]
                    fname = f"{safe_title}_{fmt_key}"
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.download_button("⬇ TXT",
                            export_txt(item["content"]),
                            file_name=f"{fname}.txt",
                            mime="text/plain",
                            key=f"h_txt_{vid['id']}_{fmt_key}",
                            use_container_width=True)
                    with c2:
                        st.download_button("⬇ PDF",
                            export_pdf(item["content"],
                                       fmt_labels.get(fmt_key, fmt_key)),
                            file_name=f"{fname}.pdf",
                            mime="application/pdf",
                            key=f"h_pdf_{vid['id']}_{fmt_key}",
                            use_container_width=True)
                    with c3:
                        st.download_button("⬇ DOCX",
                            export_docx(item["content"],
                                        fmt_labels.get(fmt_key, fmt_key)),
                            file_name=f"{fname}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"h_docx_{vid['id']}_{fmt_key}",
                            use_container_width=True)
        else:
            st.info("No content generated yet for this video.")

        st.divider()
        if st.button("🗑 Delete", key=f"del_{vid['id']}", type="secondary"):
            delete_video(vid["id"])
            st.success("Deleted.")
            st.rerun()
