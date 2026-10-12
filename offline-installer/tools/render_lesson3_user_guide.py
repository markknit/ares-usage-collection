#!/usr/bin/env python3
"""Render the bundled Lesson3 Markdown guide as a compact ARES PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


TEAL = colors.HexColor("#176B87")
DARK = colors.HexColor("#222222")
MUTED = colors.HexColor("#5C6570")
PALE_TEAL = colors.HexColor("#EAF4F5")
PALE_GOLD = colors.HexColor("#F5F0E2")
RULE = colors.HexColor("#B8C4C8")

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("GuideSans", FONT_DIR / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("GuideSans-Bold", FONT_DIR / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("GuideMono", FONT_DIR / "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily(
    "GuideSans",
    normal="GuideSans",
    bold="GuideSans-Bold",
    italic="GuideSans",
    boldItalic="GuideSans-Bold",
)


def normalize(text: str) -> str:
    replacements = {
        "\u2014": " - ",
        "\u2013": "-",
        "\u2011": "-",
        "\u00a0": " ",
        "\u2192": "->",
        "\u2197": "",
        "\u2606": "Favorite",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00b7": " | ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def inline_markup(text: str) -> str:
    text = normalize(text)
    tokens: list[str] = []

    def reserve(value: str) -> str:
        tokens.append(value)
        return f"@@TOKEN{len(tokens) - 1}@@"

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: reserve(
            f'<link href="{html.escape(m.group(2), quote=True)}" color="#176B87">'
            f"{html.escape(m.group(1))}</link>"
        ),
        text,
    )
    text = re.sub(
        r"`([^`]+)`",
        lambda m: reserve(f'<font name="GuideMono">{html.escape(m.group(1))}</font>'),
        text,
    )
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"_([^_]+)_", r"<i>\1</i>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    for index, value in enumerate(tokens):
        text = text.replace(f"@@TOKEN{index}@@", value)
    return text


def parse_markdown(path: Path) -> list[tuple[str, str | list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, str | list[str]]] = []
    paragraph: list[str] = []
    bullets: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(("p", " ".join(part.strip() for part in paragraph)))
            paragraph.clear()

    def flush_bullets() -> None:
        if bullets:
            blocks.append(("bullets", list(bullets)))
            bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("<!--"):
            continue
        if not line.strip():
            flush_paragraph()
            flush_bullets()
            continue
        if line.strip() == "---":
            flush_paragraph()
            flush_bullets()
            blocks.append(("rule", ""))
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            flush_bullets()
            blocks.append((f"h{len(heading.group(1))}", heading.group(2)))
            continue
        bullet = re.match(r"^-\s+(.*)$", line)
        if bullet:
            flush_paragraph()
            bullets.append(bullet.group(1).strip())
            continue
        if bullets and (line.startswith("  ") or line.startswith("    ")):
            bullets[-1] += " " + line.strip()
            continue
        flush_bullets()
        paragraph.append(line.strip())

    flush_paragraph()
    flush_bullets()
    return blocks


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "GuideTitle",
            parent=base["Title"],
            fontName="GuideSans-Bold",
            fontSize=24,
            leading=28,
            textColor=TEAL,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "version": ParagraphStyle(
            "Version",
            parent=base["Normal"],
            fontName="GuideSans-Bold",
            fontSize=9,
            leading=11,
            textColor=MUTED,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="GuideSans-Bold",
            fontSize=15,
            leading=18,
            textColor=TEAL,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="GuideSans-Bold",
            fontSize=11.5,
            leading=14,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=8.9,
            leading=11.5,
            textColor=DARK,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=8.8,
            leading=11.2,
            textColor=DARK,
            leftIndent=15,
            firstLineIndent=-9,
            bulletIndent=0,
            bulletFontName="GuideSans",
            bulletFontSize=8,
            bulletColor=TEAL,
            spaceAfter=2,
        ),
        "table_role": ParagraphStyle(
            "TableRole",
            parent=base["BodyText"],
            fontName="GuideSans-Bold",
            fontSize=8.7,
            leading=10.7,
            textColor=TEAL,
        ),
        "table_text": ParagraphStyle(
            "TableText",
            parent=base["BodyText"],
            fontName="GuideSans",
            fontSize=8.5,
            leading=10.5,
            textColor=DARK,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName="GuideSans",
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
    }


def at_a_glance(styles):
    rows = [
        ("Teachers", "Find, read, download, discuss, favorite, share, and request editing access."),
        ("Editors", "Update lesson content, save versions, restore work, compare, and discuss changes."),
        ("Subject-grade administrators", "Manage structure, access, settings, and Official versions."),
        ("Site administrators", "Manage the whole site, accounts, curriculum, discussions, and system status."),
    ]
    data = [
        [Paragraph(role, styles["table_role"]), Paragraph(text, styles["table_text"])]
        for role, text in rows
    ]
    table = Table(data, colWidths=[1.55 * inch, 5.3 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_TEAL),
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def page_decor(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    if doc.page > 1:
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(0.65 * inch, height - 0.46 * inch, width - 0.65 * inch, height - 0.46 * inch)
        canvas.setFont("GuideSans-Bold", 7.5)
        canvas.setFillColor(TEAL)
        canvas.drawString(0.65 * inch, height - 0.36 * inch, "ARES LESSON LIBRARY - USER GUIDE")
    canvas.setStrokeColor(RULE)
    canvas.line(0.65 * inch, 0.5 * inch, width - 0.65 * inch, 0.5 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("GuideSans", 7.3)
    canvas.drawString(0.65 * inch, 0.34 * inch, "Lesson3 v0.94 | ARES Education and Seavuria")
    canvas.drawRightString(width - 0.65 * inch, 0.34 * inch, f"Page {doc.page}")
    canvas.restoreState()


def render(source: Path, output: Path) -> None:
    styles = build_styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.65 * inch,
        title="ARES Lesson Library Editor User Guide",
        author="ARES Education",
        subject="Lesson3 v0.94 offline user guide",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="guide")
    doc.addPageTemplates([PageTemplate(id="guide", frames=[frame], onPage=page_decor)])

    story = []
    inserted_glance = False
    for kind, value in parse_markdown(source):
        if kind == "h1":
            story.append(Paragraph(inline_markup(str(value)), styles["title"]))
            story.append(Paragraph("Lesson3 v0.94 | Complete offline reference | October 2026", styles["version"]))
        elif kind == "h2":
            if str(value) == "Teachers" and not inserted_glance:
                story.extend(
                    [
                        Paragraph("At a glance", styles["h2"]),
                        at_a_glance(styles),
                        Spacer(1, 5),
                    ]
                )
                inserted_glance = True
            story.append(Paragraph(inline_markup(str(value)), styles["h2"]))
        elif kind == "h3":
            story.append(Paragraph(inline_markup(str(value)), styles["h3"]))
        elif kind == "p":
            story.append(Paragraph(inline_markup(str(value)), styles["body"]))
        elif kind == "bullets":
            for item in value:
                story.append(Paragraph(inline_markup(item), styles["bullet"], bulletText="•"))
        elif kind == "rule":
            story.append(HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=8, spaceAfter=8))

    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.source, args.output)


if __name__ == "__main__":
    main()
