from pathlib import Path
import pytest
from backend.app.services.ingestion.parser import DocumentParser, IngestionError


def test_parse_valid_multipage_pdf(sample_guidelines_dir: Path):
    pdf_path = sample_guidelines_dir / "sepsis_guideline_2026.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        content = f.read()

    parsed = DocumentParser.parse(
        content=content,
        filename="sepsis_guideline_2026.pdf",
        mime_type="application/pdf",
    )

    assert parsed.total_pages == 3
    assert len(parsed.pages) == 3
    assert parsed.filename == "sepsis_guideline_2026.pdf"
    assert len(parsed.content_hash) == 64  # SHA-256 length

    # Page 1 checks
    p1 = parsed.pages[0]
    assert p1.page_number == 1
    assert "SURVIVING SEPSIS CAMPAIGN" in p1.text

    # Page 2 checks (Antimicrobial timing)
    p2 = parsed.pages[1]
    assert p2.page_number == 2
    assert "within 1 hour of recognition" in p2.text
    assert any("3.1" in s.heading or "ANTIMICROBIAL" in s.heading.upper() for s in p2.sections)

    # Page 3 checks (Norepinephrine & MAP)
    p3 = parsed.pages[2]
    assert p3.page_number == 3
    assert "Norepinephrine" in p3.text
    assert "mean arterial pressure" in p3.text.lower()


def test_parse_markdown_text():
    raw_md = (
        "# CLINICAL PROTOCOL: HYPERKALEMIA\n"
        "Document Version: 2026.1\n\n"
        "## 1.0 EMERGENCY TREATMENT\n"
        "Administer 10% Calcium Gluconate 10 mL IV over 2 to 5 minutes for myocardial membrane stabilization.\n"
        "Follow with 10 units regular insulin in 50 mL 50% dextrose over 15 minutes.\n"
    )
    content = raw_md.encode("utf-8")

    parsed = DocumentParser.parse(
        content=content,
        filename="hyperkalemia_protocol.md",
        mime_type="text/markdown",
    )

    assert parsed.total_pages == 1
    assert len(parsed.pages) == 1
    assert parsed.mime_type == "text/markdown"
    assert "Calcium Gluconate" in parsed.pages[0].text
    assert len(parsed.pages[0].sections) >= 1


def test_reject_empty_file():
    with pytest.raises(IngestionError, match="is empty"):
        DocumentParser.parse(
            content=b"",
            filename="empty_file.pdf",
            mime_type="application/pdf",
        )


def test_reject_corrupt_pdf(sample_guidelines_dir: Path):
    corrupt_path = sample_guidelines_dir / "corrupted_sample.pdf"
    with open(corrupt_path, "rb") as f:
        content = f.read()

    with pytest.raises(IngestionError, match="corrupt or malformed"):
        DocumentParser.parse(
            content=content,
            filename="corrupted_sample.pdf",
            mime_type="application/pdf",
        )


def test_reject_unsupported_format():
    with pytest.raises(IngestionError, match="Unsupported file format"):
        DocumentParser.parse(
            content=b"BINARY_EXECUTABLE_DATA",
            filename="malicious.exe",
            mime_type="application/x-msdownload",
        )
