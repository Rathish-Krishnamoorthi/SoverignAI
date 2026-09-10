import re

from backend.models.schemas import InspectionEvidence, StructuredDocument


def extract_evidence(document: StructuredDocument) -> InspectionEvidence:
    text = "\n".join(page.text for page in document.pages)
    equipment = re.search(r"Equipment:\s*([^\n.]+)", text, re.IGNORECASE)
    measurement = re.search(r"(?:pit depth|depth)[^\d]*(\d+(?:\.\d+)?)\s*mm", text, re.IGNORECASE)
    finding = re.search(r"Finding:\s*([^\n.]+)", text, re.IGNORECASE)
    page = next((item for item in document.pages if item.text.strip()), document.pages[0])
    photo = next((image.get("photo_id", "Not available") for image in page.images), "Not available")
    missing = []
    if not equipment:
        missing.append("Equipment: <name>")
    if not finding:
        missing.append("Finding: <description>")
    if not measurement:
        missing.append("Pit depth measured at <number> mm")
    if missing:
        raise ValueError(
            "Required engineering fields were not extracted: "
            + ", ".join(missing)
            + ". Use a text-based PDF or a clear scanned PDF with these labels and numeric values."
        )
    return InspectionEvidence(
        document=document.document,
        page=page.page,
        photo=photo,
        equipment=(equipment.group(1).strip() if equipment else "Unknown equipment"),
        finding=(finding.group(1).strip() if finding else "Pitting corrosion"),
        measurement=float(measurement.group(1)),
    )
