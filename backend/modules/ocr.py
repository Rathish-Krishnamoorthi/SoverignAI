from pathlib import Path
import logging

from backend.models.schemas import DocumentPage, StructuredDocument

logger = logging.getLogger("sovereign_x.ocr")

DEMO_TEXT = (
    "Inspection Report\n"
    "Equipment: Flange B-12\n"
    "Finding: Pitting corrosion.\n"
    "Pit depth measured at 2.0 mm.\n"
    "Photo 3 documents the finding."
)


def demo_document(filename: str) -> StructuredDocument:
    return StructuredDocument(
        document=filename,
        pages=[DocumentPage(page=6, text=DEMO_TEXT, images=[{"photo_id": "Photo 3"}])],
    )


def extract_document(path: Path, demo_mode: bool) -> StructuredDocument:
    if demo_mode:
        return demo_document(path.name)
    suffix = path.suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValueError("Unsupported file type. Upload a PDF, PNG, or JPG.")
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError("The uploaded document is empty.")
    try:
        logger.info("ocr_file_start filename=%s suffix=%s", path.name, suffix)
        pages = _extract_pdf(path) if suffix == ".pdf" else _extract_image(path)
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"OCR failed: {exc}") from exc
    if not any(page.text.strip() for page in pages):
        raise RuntimeError(
            "OCR produced no readable text. This may be a scanned PDF; install the optional OCR packages "
            "and retry."
        )
    return StructuredDocument(document=path.name, pages=pages)


def _extract_pdf(path: Path) -> list[DocumentPage]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path), strict=False)
        pages = [
            DocumentPage(page=index, text=page.extract_text() or "", images=[])
            for index, page in enumerate(reader.pages, start=1)
        ]
    except Exception as pypdf_error:
        # Some valid PDFs use structures that pypdf cannot parse; PyMuPDF is
        # used as a second local parser before reporting the file as invalid.
        try:
            import fitz

            document = fitz.open(str(path))
            try:
                pages = [
                    DocumentPage(page=index, text=page.get_text("text"), images=[])
                    for index, page in enumerate(document, start=1)
                ]
            finally:
                document.close()
            if any(page.text.strip() for page in pages):
                logger.info("ocr_method=pdf_text_layer filename=%s", path.name)
                return pages
        except Exception:
            pass
        raise ValueError(
            "The PDF could not be opened by the local PDF parsers. "
            "It is not a valid, uncorrupted PDF. "
            "Upload the original PDF (not a .txt/.md/image renamed to .pdf), "
            "or export it again as a standard searchable PDF."
        ) from pypdf_error

    if any(page.text.strip() for page in pages):
        return pages

    # Render image-only PDF pages locally, then send each page through PaddleOCR.
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "This PDF contains no text layer. Install backend\\requirements-optional.txt "
            "to enable scanned-PDF OCR."
        ) from exc

    ocr = _paddle_ocr()
    logger.info("ocr_method=paddleocr_scanned_pdf filename=%s", path.name)
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Scanned-PDF OCR requires numpy with PaddleOCR.") from exc
    scanned_pages: list[DocumentPage] = []
    document = fitz.open(str(path))
    try:
        for index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, pixmap.n
            )
            result = ocr.ocr(image, cls=True)
            scanned_pages.append(
                DocumentPage(page=index, text=_flatten_ocr(result), images=[])
            )
    finally:
        document.close()
    return scanned_pages


def _extract_image(path: Path) -> list[DocumentPage]:
    logger.info("ocr_method=paddleocr_image filename=%s", path.name)
    ocr = _paddle_ocr()
    result = ocr.ocr(str(path), cls=True)
    return [DocumentPage(page=1, text=_flatten_ocr(result), images=[])]


def _paddle_ocr():
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "Image OCR requires PaddleOCR. Install backend\\requirements-optional.txt "
            "and the matching PaddlePaddle runtime."
        ) from exc
    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


def _flatten_ocr(result) -> str:
    return " ".join(
        line[1][0]
        for block in (result or [])
        for line in (block or [])
        if line and len(line) > 1 and line[1]
    )
