#!/usr/bin/env python3
"""Build printable rollout PDFs from the authoritative Markdown guides."""

from __future__ import annotations

import html
import re
import argparse
from pathlib import Path
import reportlab

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


ROOT = Path(__file__).resolve().parents[2]
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

def font_path(linux_name, fallback):
    path = Path("/usr/share/fonts/truetype/dejavu") / linux_name
    return str(path if path.exists() else Path(reportlab.__file__).parent / "fonts" / fallback)


pdfmetrics.registerFont(TTFont("DejaVu", font_path("DejaVuSans.ttf", "Vera.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_path("DejaVuSans-Bold.ttf", "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", font_path("DejaVuSansMono-Oblique.ttf", "VeraIt.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuMono", font_path("DejaVuSansMono.ttf", "Vera.ttf")))
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
    revision = getattr(doc, 'guide_revision', '2026-11-04')
    canvas.drawString(18 * mm, 10 * mm, "ARES Education - ARES Sync rollout guide - Revision " + revision)
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown(path: Path, style_map):
    lines = path.read_text(encoding="utf-8").splitlines()
    story = []
    list_items = []
    list_kind = None
    list_start = 1
    quote_lines = []
    in_code = False

    def flush_list():
        nonlocal list_items, list_kind
        if not list_items:
            return
        bullet_type = "1" if list_kind == "number" else "bullet"
        start = str(list_start) if list_kind == "number" else "circle"
        if list_kind == "bullet":
            story.extend(Paragraph("- " + inline_markup(item), style_map["bullet"]) for item in list_items)
            list_items = []
            list_kind = None
            return
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
        if line.startswith("```"):
            flush_list()
            flush_quote()
            in_code = not in_code
            continue
        if in_code:
            if line:
                story.append(Paragraph(inline_markup("`" + line + "`"), style_map["body"]))
            continue
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
            if not list_items:
                list_start = int(line.split(".", 1)[0])
            list_items.append(re.sub(r"^\d+\.\s+", "", line))
        elif line.startswith("- "):
            if list_kind not in (None, "bullet"):
                flush_list()
            list_kind = "bullet"
            list_items.append(line[2:])
        elif list_items and raw.startswith(" "):
            list_items[-1] += " " + line
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
    doc.guide_revision = ('2026-11-07' if source.stem in
                          ('TECHNICIAN_PHONE_INSTALL', 'TECHNICIAN_OVERVIEW') else '2026-11-04')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="ares", frames=[frame], onPage=header_footer)])
    doc.build(parse_markdown(source, styles()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if bool(args.source_dir) != bool(args.output_dir):
        parser.error("--source-dir and --output-dir must be supplied together")
    guides = GUIDES if not args.source_dir else (
        (args.source_dir / "TECHNICIAN_PHONE_INSTALL.md", args.output_dir / "ARES_Sync_Technician_Guide.pdf"),
        (args.source_dir / "TEACHER_PHONE_GUIDE.md", args.output_dir / "ARES_Sync_Teacher_Guide.pdf"),
    )
    for source, destination in guides:
        build(source, destination)
        print(destination)
    if args.source_dir and (args.source_dir / "TECHNICIAN_OVERVIEW.md").is_file():
        destination = args.output_dir / "ARES_Offline_Installer_Overview.pdf"
        build(args.source_dir / "TECHNICIAN_OVERVIEW.md", destination)
        print(destination)


if __name__ == "__main__":
    main()
