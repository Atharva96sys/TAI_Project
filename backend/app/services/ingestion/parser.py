import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
from backend.app.core.config import settings


class IngestionError(Exception):
    """Custom exception raised during document ingestion and validation."""
    pass


@dataclass
class SectionBlock:
    heading: str
    text: str


@dataclass
class ParsedPage:
    page_number: int
    text: str
    sections: list[SectionBlock]
    char_count: int


@dataclass
class ParsedDocument:
    filename: str
    file_size: int
    mime_type: str
    content_hash: str
    total_pages: int
    pages: list[ParsedPage]


class DocumentParser:
    """Extracts structured text, pages, section headings, and computes integrity hashes."""

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        """Compute SHA-256 checksum of raw file bytes."""
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def parse(cls, content: bytes, filename: str, mime_type: str | None = None) -> ParsedDocument:
        """Parse raw document bytes into a structured ParsedDocument with page-level provenance."""
        if not content or len(content.strip()) == 0:
            raise IngestionError(f"Rejected: Document '{filename}' is empty (0 bytes).")

        file_size = len(content)
        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise IngestionError(
                f"Rejected: Document '{filename}' exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES} bytes."
            )

        content_hash = cls.compute_sha256(content)

        # Detect or validate MIME type
        detected_mime = mime_type or cls._infer_mime_type(filename)
        if detected_mime not in settings.ALLOWED_MIME_TYPES:
            raise IngestionError(
                f"Rejected: Unsupported file format '{detected_mime}'. Allowed formats: {settings.ALLOWED_MIME_TYPES}"
            )

        if detected_mime == "application/pdf":
            pages = cls._parse_pdf(content, filename)
        else:
            pages = cls._parse_text_or_markdown(content, filename)

        if not pages or all(len(p.text.strip()) == 0 for p in pages):
            raise IngestionError(f"Rejected: Document '{filename}' yielded no readable text content.")

        if len(pages) > settings.MAX_PDF_PAGES:
            raise IngestionError(
                f"Rejected: Document '{filename}' has {len(pages)} pages, exceeding limit of {settings.MAX_PDF_PAGES}."
            )

        return ParsedDocument(
            filename=filename,
            file_size=file_size,
            mime_type=detected_mime,
            content_hash=content_hash,
            total_pages=len(pages),
            pages=pages,
        )

    @classmethod
    def _infer_mime_type(cls, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return "application/pdf"
        elif ext in [".md", ".markdown"]:
            return "text/markdown"
        elif ext in [".txt", ".text"]:
            return "text/plain"
        return "application/octet-stream"

    @classmethod
    def _parse_pdf(cls, content: bytes, filename: str) -> list[ParsedPage]:
        """Extract text and section blocks from a PDF using PyMuPDF."""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise IngestionError(f"Rejected: PDF file '{filename}' is corrupt or malformed. Error: {str(e)}")

        pages: list[ParsedPage] = []
        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1
                raw_text = page.get_text("text") or ""
                sections = cls._extract_sections_from_text(raw_text, default_heading=f"Page {page_num}")
                pages.append(
                    ParsedPage(
                        page_number=page_num,
                        text=raw_text.strip(),
                        sections=sections,
                        char_count=len(raw_text),
                    )
                )
        finally:
            doc.close()

        return pages

    @classmethod
    def _parse_text_or_markdown(cls, content: bytes, filename: str) -> list[ParsedPage]:
        """Extract structured sections from text or markdown file."""
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as e:
                raise IngestionError(f"Rejected: Text document '{filename}' has invalid encoding. Error: {str(e)}")

        sections = cls._extract_sections_from_text(text, default_heading="Clinical Document Section")
        return [
            ParsedPage(
                page_number=1,
                text=text.strip(),
                sections=sections,
                char_count=len(text),
            )
        ]

    @classmethod
    def _extract_sections_from_text(cls, text: str, default_heading: str) -> list[SectionBlock]:
        """Extract headings and text segments using markdown or clinical protocol header patterns."""
        # Regex matching markdown headers (# Heading), numbered sections (1.0 Section, Section 2:), or uppercase titles
        header_pattern = re.compile(
            r"(?:^|\n)(#{1,4}\s+[^\n]+|(?:Section|PROTOCOL|GUIDELINE|CHAPTER)\s+[0-9A-Z\.\:\-]+[^\n]*|[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9])?\s+[A-Z][^\n]+)",
            re.MULTILINE | re.IGNORECASE,
        )

        matches = list(header_pattern.finditer(text))
        if not matches:
            return [SectionBlock(heading=default_heading, text=text.strip())]

        sections: list[SectionBlock] = []
        current_heading = default_heading
        current_start = 0

        for match in matches:
            section_text = text[current_start : match.start()].strip()
            if section_text:
                sections.append(SectionBlock(heading=current_heading, text=section_text))

            current_heading = match.group(1).strip().lstrip("#").strip()
            current_start = match.end()

        # Add remaining text
        tail_text = text[current_start:].strip()
        if tail_text:
            sections.append(SectionBlock(heading=current_heading, text=tail_text))

        return sections if sections else [SectionBlock(heading=default_heading, text=text.strip())]
