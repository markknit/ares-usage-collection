"""Local QA: verify guide URL text and combine rendered pages for visual inspection."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from pypdf import PdfReader

root = Path("output/reconciliation/test-docs/pdf")
for path in root.glob("*.pdf"):
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    assert "ares.local" not in text, path
    assert "ares-test.local" in text, path
    print(path.name, len(PdfReader(path).pages), "pages, test URLs PASS")
images = []
for path in sorted(root.glob("*.png")):
    image = Image.open(path).convert("RGB")
    image.thumbnail((480, 680))
    tile = Image.new("RGB", (500, 710), "#ddd")
    tile.paste(image, ((500 - image.width) // 2, 20))
    ImageDraw.Draw(tile).text((10, 690), path.name, fill="black")
    images.append(tile)
sheet = Image.new("RGB", (500 * 3, 710 * ((len(images) + 2) // 3)), "white")
for index, image in enumerate(images):
    sheet.paste(image, ((index % 3) * 500, (index // 3) * 710))
sheet.save(root / "contact-sheet.jpg")
