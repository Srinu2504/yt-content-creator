"""One-off script to build downloader-analysis.pdf from the markdown source."""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE = Path(__file__).parent
MD_PATH = BASE / "downloader-analysis.md"
PDF_PATH = BASE / "downloader-analysis.pdf"


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def parse_md(lines: list[str]) -> list:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13, spaceAfter=6)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=14, bulletIndent=6)
    code = ParagraphStyle("Code", parent=styles["Code"], fontSize=7.5, leading=10, backColor=colors.HexColor("#f4f4f5"))

    story = []
    i = 0
    in_code = False
    code_lines: list[str] = []
    table_rows: list[list[str]] = []

    while i < len(lines):
        line = lines[i].rstrip("\n")

        if line.strip() == "---":
            story.append(Spacer(1, 0.15 * cm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e4e4e7")))
            story.append(Spacer(1, 0.15 * cm))
            i += 1
            continue

        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                story.append(Preformatted("\n".join(code_lines), code))
                story.append(Spacer(1, 0.1 * cm))
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if line.startswith("|") and "|" in line[1:]:
            if re.match(r"^\|[-\s|:]+\|$", line.replace(" ", "")):
                i += 1
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_rows.append(cells)
            if i + 1 >= len(lines) or not lines[i + 1].startswith("|"):
                t = Table(table_rows, colWidths=[2.2 * cm, 5.5 * cm, 8.5 * cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27272a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d4d4d8")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.15 * cm))
                table_rows = []
            i += 1
            continue

        if line.startswith("# "):
            story.append(Paragraph(esc(line[2:]), h1))
        elif line.startswith("## "):
            story.append(Paragraph(esc(line[3:]), h2))
        elif line.startswith("### "):
            story.append(Paragraph(esc(line[4:]), h3))
        elif line.startswith("- "):
            text = esc(line[2:])
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
            story.append(Paragraph(f"• {text}", bullet))
        elif line.strip().startswith("**User sees:**"):
            text = esc(line.strip())
            text = text.replace("**User sees:**", "<b>User sees:</b>")
            text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
            story.append(Paragraph(text, body))
        elif line.strip():
            text = esc(line)
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
            text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
            story.append(Paragraph(text, body))
        else:
            story.append(Spacer(1, 0.08 * cm))

        i += 1

    return story


def main():
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Downloader Analysis",
        author="YT Content Creator",
    )
    doc.build(parse_md(lines))
    print(f"Created: {PDF_PATH}")


if __name__ == "__main__":
    main()
