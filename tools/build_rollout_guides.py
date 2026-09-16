#!/usr/bin/env python3
"""Build printable rollout PDFs from the authoritative Markdown guides."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"
GUIDES = (
    (ROOT / "docs" / "TECHNICIAN_PHONE_INSTALL.md", OUTPUT_DIR / "ARES_Sync_Technician_Guide.pdf"),
    (ROOT / "docs" / "TEACHER_PHONE_GUIDE.md", OUTPUT_DIR / "ARES_Sync_Teacher_Guide.pdf"),
)

ARES_BLUE = colors.HexColor("#16708E")
ARES_DARK = colors.HexColor("#23363F")
ARES_WARM = colors.HexColor("#F5EED8")
ARES_PALE = colors.HexColor("#EAF5F2")
TEXT = colors.HexColor("#2D3436")

pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily(
    "DejaVu",
    normal="DejaVu",
    bold="DejaVu-Bold",
    italic="DejaVu-Oblique",
    boldItalic="DejaVu-Bold",
)


def inline_markup(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r'<font name="DejaVuMono">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AresTitle",
            parent=base["Title"],
            fontName="DejaVu-Bold",
            fontSize=21,
            leading=24,
            textColor=ARES_BLUE,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "AresH2",
            parent=base["Heading2"],
            fontName="DejaVu-Bold",
            fontSize=13.2,
            leading=16,
            textColor=ARES_BLUE,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "AresH3",
            parent=base["Heading3"],
            fontName="DejaVu-Bold",
            fontSize=11,
            leading=13.5,
            textColor=ARES_DARK,
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "AresBody",
            parent=base["BodyText"],
            fontName="DejaVu",
            fontSize=9,
            leading=12.2,
            textColor=TEXT,
            spaceAfter=3.5,
        ),
        "quote": ParagraphStyle(
            "AresQuote",
            parent=base["BodyText"],
            fontName="DejaVu-Oblique",
            fontSize=9,
            leading=12.2,
            textColor=ARES_DARK,
            leftIndent=8 * mm,
            rightIndent=5 * mm,
            borderColor=ARES_BLUE,
            borderWidth=1,
            borderPadding=6,
            backColor=ARES_PALE,
            spaceBefore=3,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "AresBullet",
            parent=base["BodyText"],
            fontName="DejaVu",
            fontSize=8.9,
            leading=11.7,
            textColor=TEXT,
        ),
        "footer": ParagraphStyle(
            "AresFooter",
            parent=base["BodyText"],
            fontName="DejaVu",
            fontSize=7.5,
            textColor=colors.HexColor("#66757D"),
        ),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(ARES_BLUE)
    canvas.rect(0, height - 7 * mm, width, 7 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(colors.HexColor("#C7D4D8"))
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFillColor(colors.HexColor("#66757D"))
    canvas.setFont("DejaVu", 7.5)
    canvas.drawString(18 * mm, 10 * mm, "ARES Education - ARES Sync rollout guide - Revision 2026-09-16")
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown(path: Path, style_map):
    lines = path.read_text(encoding="utf-8").splitlines()
    story = []
    list_items = []
    list_kind = None
    quote_lines = []

    def flush_list():
        nonlocal list_items, list_kind
        if not list_items:
            return
        bullet_type = "1" if list_kind == "number" else "bullet"
        start = "1" if list_kind == "number" else "circle"
        story.append(
            ListFlowable(
                [ListItem(Paragraph(inline_markup(item), style_map["bullet"])) for item in list_items],
                bulletType=bullet_type,
                start=start,
                leftIndent=7 * mm,
                bulletFontName="DejaVu",
                bulletFontSize=8,
                spaceAfter=4,
            )
        )
        list_items = []
        list_kind = None

    def flush_quote():
        nonlocal quote_lines
        if quote_lines:
            story.append(Paragraph(inline_markup(" ".join(quote_lines)), style_map["quote"]))
            quote_lines = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_list()
            flush_quote()
            continue
        if line.startswith("> "):
            flush_list()
            quote_lines.append(line[2:])
            continue
        flush_quote()
        if line == "<!-- pagebreak -->":
            flush_list()
            story.append(PageBreak())
        elif line.startswith("# "):
            flush_list()
            story.append(Paragraph(inline_markup(line[2:]), style_map["title"]))
        elif line.startswith("## "):
            flush_list()
            story.append(Paragraph(inline_markup(line[3:]), style_map["h2"]))
        elif line.startswith("### "):
            flush_list()
            story.append(Paragraph(inline_markup(line[4:]), style_map["h3"]))
        elif re.match(r"^\d+\.\s+", line):
            if list_kind not in (None, "number"):
                flush_list()
            list_kind = "number"
            list_items.append(re.sub(r"^\d+\.\s+", "", line))
        elif line.startswith("- "):
            if list_kind not in (None, "bullet"):
                flush_list()
            list_kind = "bullet"
            list_items.append(line[2:])
        else:
            flush_list()
            story.append(Paragraph(inline_markup(line), style_map["body"]))

    flush_list()
    flush_quote()
    return story


def build(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(destination),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=12 * mm,
        bottomMargin=18 * mm,
        title=source.stem.replace("_", " ").title(),
        author="ARES Education",
        subject="ARES Sync rollout guidance",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="ares", frames=[frame], onPage=header_footer)])
    doc.build(parse_markdown(source, styles()))


def main() -> None:
    for source, destination in GUIDES:
        build(source, destination)
        print(destination.relative_to(ROOT))


if __name__ == "__main__":
    main()
