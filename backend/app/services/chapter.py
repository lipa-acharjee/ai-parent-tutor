import hashlib
import io

import pymupdf
import pytesseract
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag import add_chunks


def extract_pdf(data: bytes):
    doc = pymupdf.open(
        stream=data,
        filetype="pdf",
    )

    chunks = []

    for page_no, page in enumerate(doc, start=1):

        text = page.get_text("text").strip()

        # OCR for scanned/image-based pages
        if len(text) < 40:

            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(1.5, 1.5)
            )

            img = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            text = pytesseract.image_to_string(
                img
            ).strip()

        if text:
            chunks.append(
                (page_no, text)
            )

    doc.close()

    return chunks


def chunk_pages(
    pages,
    size=1800,
    overlap=250,
):

    out = []

    for page, text in pages:

        start = 0

        while start < len(text):

            end = min(
                len(text),
                start + size,
            )

            out.append(
                (
                    page,
                    text[start:end],
                )
            )

            if end == len(text):
                break

            start = end - overlap

    return out


def checksum(data: bytes):
    return hashlib.sha256(data).hexdigest()


# =========================================================
# Convert multiple JPG/JPEG images into one PDF
# =========================================================

def images_to_pdf(image_data: list[bytes]) -> bytes:

    if not image_data:
        raise ValueError(
            "No images provided"
        )

    images = []

    try:

        for data in image_data:

            image = Image.open(
                io.BytesIO(data)
            )

            # PDF requires RGB or L mode
            if image.mode not in ("RGB", "L"):

                image = image.convert(
                    "RGB"
                )

            images.append(
                image.copy()
            )

            image.close()

        first_image = images[0]

        remaining_images = images[1:]

        output = io.BytesIO()

        first_image.save(
            output,
            format="PDF",
            save_all=True,
            append_images=remaining_images,
        )

        # Close images
        for image in images:
            image.close()

        return output.getvalue()

    except Exception:

        for image in images:

            try:
                image.close()
            except Exception:
                pass

        raise


async def index_pdf(
    db: AsyncSession,
    chapter_id: str,
    data: bytes,
):

    pages = extract_pdf(data)

    if not pages:
        raise ValueError(
            "No readable text found in PDF"
        )

    await add_chunks(
        db,
        chapter_id,
        chunk_pages(pages),
    )

    return len(pages)