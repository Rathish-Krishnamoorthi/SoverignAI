import csv
import json
import logging
import os
import tempfile
from pathlib import Path

from backend.models.schemas import DocumentPage, StructuredDocument

logger = logging.getLogger("sovereign_x.ocr")

OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() == "true"
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "en")
OCR_OFFLINE = os.getenv("AIR_GAPPED_MODE", "true").lower() == "true"
OCR_MODEL_DIR = Path(os.getenv(
    "OCR_MODEL_DIR",
    str(Path(__file__).resolve().parents[1] / "ocr_models"),
))
OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "120"))
_OCR_INSTANCE = None

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
    supported = {
        ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff",
        ".docx", ".txt", ".md", ".csv", ".json",
    }
    if suffix not in supported:
        raise ValueError(
            "Unsupported file type. Upload PDF, DOCX, TXT, Markdown, CSV, JSON, "
            "or a PNG/JPG/TIFF/WEBP/BMP image."
        )
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError("The uploaded document is empty.")
    try:
        logger.info("ocr_file_start filename=%s suffix=%s", path.name, suffix)
        if suffix == ".pdf":
            pages = _extract_pdf(path)
        elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
            pages = _extract_image(path)
        else:
            pages = _extract_text_document(path, suffix)
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"OCR_FAILED: {exc}") from exc
    if not any(page.text.strip() for page in pages):
        raise RuntimeError("OCR_FAILED: no readable text was extracted by the local OCR runtime.")
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
            "It is not a valid, uncorrupted PDF."
        ) from pypdf_error

    if any(page.text.strip() for page in pages):
        logger.info("ocr_method=pdf_text_layer filename=%s", path.name)
        return pages

    logger.info("Processing scanned PDF locally: %s", path.name)
    try:
        import fitz
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "OCR_UNAVAILABLE: scanned-PDF OCR requires PyMuPDF and NumPy."
        ) from exc

    ocr = _paddle_ocr()
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
    logger.info("OCR completed successfully: scanned PDF %s", path.name)
    return scanned_pages


def _extract_image(path: Path) -> list[DocumentPage]:
    logger.info("Processing image with local PaddleOCR: %s", path.name)
    result = _paddle_ocr().ocr(str(path), cls=True)
    text = _flatten_ocr(result)
    logger.info("OCR completed successfully: %s", path.name)
    return [DocumentPage(page=1, text=text, images=[])]


def _extract_text_document(path: Path, suffix: str) -> list[DocumentPage]:
    if suffix == ".docx":
        try:
            from docx import Document

            document = Document(str(path))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            for table in document.tables:
                text += "\n" + "\n".join(
                    " | ".join(cell.text for cell in row.cells) for row in table.rows
                )
        except Exception as exc:
            raise ValueError(f"DOCX extraction failed locally: {exc}") from exc
    else:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        if suffix == ".csv":
            text = "\n".join(" | ".join(row) for row in csv.reader(raw.splitlines()))
        elif suffix == ".json":
            try:
                text = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON extraction failed: {exc}") from exc
        else:
            text = raw
    return [DocumentPage(page=1, text=text, images=[])]


def _paddle_ocr():
    global _OCR_INSTANCE
    if not OCR_ENABLED:
        raise RuntimeError("OCR_UNAVAILABLE: OCR_ENABLED=false.")
    required = (
        "det/inference.pdiparams",
        "det/inference.pdmodel",
        "rec/inference.pdiparams",
        "rec/inference.pdmodel",
        "cls/inference.pdiparams",
        "cls/inference.pdmodel",
    )
    missing = [str(OCR_MODEL_DIR / item) for item in required if not (OCR_MODEL_DIR / item).is_file()]
    if missing:
        raise RuntimeError(
            "OCR_UNAVAILABLE: local PaddleOCR model files are missing: " + ", ".join(missing)
        )
    if _OCR_INSTANCE is not None:
        return _OCR_INSTANCE
    if OCR_OFFLINE:
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    try:
        import paddle
        from paddleocr import PaddleOCR

        _OCR_INSTANCE = PaddleOCR(
            use_angle_cls=True,
            lang=OCR_LANGUAGE,
            show_log=False,
            det_model_dir=str(OCR_MODEL_DIR / "det"),
            rec_model_dir=str(OCR_MODEL_DIR / "rec"),
            cls_model_dir=str(OCR_MODEL_DIR / "cls"),
        )
    except Exception as exc:
        raise RuntimeError(
            f"OCR_UNAVAILABLE: PaddlePaddle/PaddleOCR could not initialize: {exc}"
        ) from exc
    logger.info("OCR runtime initialized")
    logger.info("OCR model loaded from local cache: %s", OCR_MODEL_DIR)
    return _OCR_INSTANCE


def ocr_runtime_health(run_test: bool = False) -> dict:
    if not OCR_ENABLED:
        return {"status": "disabled", "reason": "OCR_ENABLED=false"}
    try:
        ocr = _paddle_ocr()
        if run_test:
            from PIL import Image, ImageDraw

            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "ocr-health.png"
                image = Image.new("RGB", (900, 180), "white")
                ImageDraw.Draw(image).text((30, 60), "SOVEREIGN X OCR HEALTH", fill="black")
                image.save(path)
                if not _flatten_ocr(ocr.ocr(str(path), cls=True)).strip():
                    raise RuntimeError("OCR health image produced no text")
        return {
            "status": "ready",
            "model_directory": str(OCR_MODEL_DIR),
            "language": OCR_LANGUAGE,
            "offline": OCR_OFFLINE,
            "timeout_seconds": OCR_TIMEOUT_SECONDS,
        }
    except Exception as exc:
        logger.error("OCR unavailable: %s", exc)
        return {"status": "OCR_UNAVAILABLE", "reason": str(exc), "offline": OCR_OFFLINE}


def _flatten_ocr(result) -> str:
    lines: list[str] = []

    def visit(value):
        if isinstance(value, (list, tuple)):
            if (
                len(value) > 1
                and isinstance(value[1], (list, tuple))
                and value[1]
                and isinstance(value[1][0], str)
            ):
                lines.append(value[1][0])
                return
            for item in value:
                visit(item)

    visit(result or [])
    return " ".join(lines)
