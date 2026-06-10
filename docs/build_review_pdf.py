"""Build docs/analysis.pdf from project review findings."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).parent / "analysis.pdf"


def P(text, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def main():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], fontSize=18, spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=8.5, leading=11, spaceAfter=4)
    mono = ParagraphStyle("M", parent=styles["Code"], fontSize=7, leading=9)

    story = [
        P("<b>YT Content Creator — Project Review</b>", title),
        P("Generated: 2026-06-09", body),
        Spacer(1, 0.3 * cm),
        P("<b>Executive Summary</b>", h2),
        P("Syntax errors: <b>None</b> (all files pass py_compile)<br/>"
          "Import errors: <b>None</b> when PYTHONPATH=project root<br/>"
          "Critical issues: <b>2</b> | High: <b>4</b> | Medium: <b>8</b> | Low: <b>6</b><br/>"
          "Missing from requirements.txt: <b>pydub</b><br/>"
          "ffmpeg in nixpacks.toml: <b>Yes</b><br/>"
          "PYTHONPATH in start cmd: <b>Correct (/app)</b>", body),
    ]

    sections = [
        ("1. app/core/config.py", [
            "L8 — ValueError if MAX_VIDEO_DURATION_MINUTES env is non-numeric",
            "L8-10 — Defaults OK; overridable via env",
            "Missing — YOUTUBE_COOKIES not in config (used in downloader via os.environ)",
        ]),
        ("2. app/core/database.py", [
            "L37-45 — save_video() new UUID on INSERT OR REPLACE orphans generated_content",
            "L75-82 — get_content_for_video() keeps OLDEST duplicate format, not newest",
            "L28 — No ON DELETE CASCADE on FK (delete_video handles manually)",
        ]),
        ("3. app/core/downloader.py", [
            "L46-55 — Hardcoded timeout, retries, User-Agent",
            "L74,86 — duration null causes TypeError on division",
            "L84 — get_video_info() + download each create cookie temp files",
            "L137-141 — Error mentions sidebar cookies upload but UI has none",
            "L117-120 — Requires ffmpeg (nixpacks OK)",
        ]),
        ("4. app/core/transcriber.py", [
            "L3,11 — GROQ_API_KEY bound at import from config",
            "L19-20,44 — Hardcoded 24MB / 10min chunk limits",
            "L39-41 — pydub MISSING from requirements.txt",
            "L43 — pydub requires ffmpeg",
        ]),
        ("5. app/core/content_engine.py", [
            "L3,19 — Import-time GROQ_API_KEY",
            "L31,38-43 — Hardcoded temperature, truncation, max_tokens",
            "Prompt files — All 4 exist in prompts/",
        ]),
        ("6. app/exporters/exporter.py", [
            "L14 — Unused import TA_JUSTIFY",
            "L52 — Unused import Pt",
            "L37-44 — Incomplete XML escape in PDF headings",
        ]),
        ("7. app/pages/02_history.py", [
            "L22 — duration_sec None causes TypeError on // 60",
            "L22-27 — Nested expanders may warn in Streamlit",
            "L57-71 — No try/except on PDF/DOCX export (unlike main.py)",
        ]),
        ("8. app/main.py", [
            "L3-11 — All core imports correct",
            "L38-55 — api-badge/hero-badge CSS removed; cosmetic",
            "L147-149 — XSS risk: transcript in unsafe_allow_html",
            "L234-235 — Copy button does not copy to clipboard",
            "L100,151 — None transcript crashes on .split()",
        ]),
        ("9. requirements.txt", [
            "MISSING: pydub (used for large audio files)",
            "Has: streamlit, yt-dlp, groq, python-dotenv, reportlab, python-docx",
            "Note: Full pip-freeze style (58 pkgs), not minimal pins",
        ]),
        ("10. railway.toml", [
            "L5 — PYTHONPATH=/app correct",
            "L5 — streamlit run app/main.py correct",
            "L6 — healthcheckPath=/ may fail with Streamlit startup",
        ]),
        ("11. nixpacks.toml", [
            "L2 — ffmpeg included",
            "L2 — python312 may duplicate auto-detected Python",
            "L5 — PYTHONPATH=/app correct; matches railway.toml",
        ]),
    ]

    for heading, items in sections:
        story.append(P(f"<b>{heading}</b>", h2))
        for item in items:
            story.append(P(f"• {item}", body))

    story.append(P("<b>Cross-Cutting Checks</b>", h2))
    story.append(P("main.py imports: <b>All resolve correctly</b>", body))
    story.append(P("requirements vs code: <b>pydub missing</b>", body))
    story.append(P("Local dev: set PYTHONPATH to project root before streamlit run", body))

    story.append(P("<b>Priority Fixes</b>", h2))
    fixes = [
        "1. Add pydub to requirements.txt",
        "2. Fix get_content_for_video() — keep newest per format (database.py:82)",
        "3. Fix save_video() UUID replace orphaning content (database.py:37-45)",
        "4. Escape transcript HTML (main.py:147-149)",
        "5. Fix bot error message — YOUTUBE_COOKIES not sidebar (downloader.py:140)",
        "6. Guard duration_sec None (downloader.py:86, 02_history.py:22)",
        "7. Fix Copy button or use st.clipboard (main.py:234)",
        "8. Add export try/except in 02_history.py",
    ]
    for f in fixes:
        story.append(P(f"• {f}", body))

    issue_rows = [
        ["Severity", "File", "Line", "Issue"],
        ["Critical", "requirements.txt", "—", "pydub missing"],
        ["Critical", "main.py", "147-149", "XSS via unsafe HTML transcript"],
        ["High", "database.py", "82", "Wrong cached content version"],
        ["High", "database.py", "37-45", "Orphaned content on re-save"],
        ["High", "downloader.py", "140", "Misleading cookies error message"],
        ["High", "transcriber.py", "39", "pydub not in requirements"],
        ["Medium", "main.py", "234", "Copy button misleading"],
        ["Medium", "02_history.py", "22", "None duration_sec crash"],
        ["Medium", "downloader.py", "86", "None duration crash"],
        ["Low", "exporter.py", "14,52", "Unused imports"],
    ]
    t = Table(issue_rows, colWidths=[2*cm, 3.5*cm, 1.5*cm, 9*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(P("<b>Issues Table</b>", h2))
    story.append(t)

    doc = SimpleDocTemplate(str(OUT), pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm)
    doc.build(story)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
