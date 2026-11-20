import hashlib
import re
from backend.app.core.config import settings
from backend.app.models.document import DocumentChunk
from backend.app.services.ingestion.parser import ParsedDocument


class SemanticChunker:
    """Splits structured parsed clinical documents into provenance-preserved chunks."""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count based on whitespace and punctuation splitting (~1.3 words per token)."""
        words = len(text.split())
        return max(1, int(words * 1.3))

    @staticmethod
    def _compute_chunk_hash(text: str) -> str:
        """Compute SHA-256 hash for chunk text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def chunk_document(
        cls,
        parsed_doc: ParsedDocument,
        document_id: str,
        version_id: str,
        chunk_size_tokens: int = settings.CHUNK_SIZE_TOKENS,
        overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
    ) -> list[DocumentChunk]:
        """Create sequential, provenance-anchored DocumentChunk entities from a ParsedDocument."""
        chunks: list[DocumentChunk] = []
        global_chunk_idx = 0
        doc_short_id = document_id[:8]

        for page in parsed_doc.pages:
            for section in page.sections:
                section_text = section.text.strip()
                if not section_text:
                    continue

                # Split section into logical paragraphs or sentences
                paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
                if not paragraphs:
                    paragraphs = [section_text]

                current_chunk_words: list[str] = []
                current_token_count = 0

                for para in paragraphs:
                    para_words = para.split()
                    para_tokens = int(len(para_words) * 1.3)

                    # If paragraph itself exceeds chunk size, split by sentences
                    if para_tokens > chunk_size_tokens:
                        sentences = re.split(r"(?<=[.!?])\s+", para)
                        for sentence in sentences:
                            sent_words = sentence.split()
                            sent_tokens = max(1, int(len(sent_words) * 1.3))

                            if current_token_count + sent_tokens > chunk_size_tokens and current_chunk_words:
                                chunk_text = " ".join(current_chunk_words)
                                chunk_obj = cls._build_chunk_model(
                                    chunk_id=f"CHK-{doc_short_id}-{global_chunk_idx:03d}",
                                    document_id=document_id,
                                    version_id=version_id,
                                    chunk_index=global_chunk_idx,
                                    page_number=page.page_number,
                                    section_heading=section.heading,
                                    text_content=chunk_text,
                                )
                                chunks.append(chunk_obj)
                                global_chunk_idx += 1

                                # Retain overlap
                                overlap_words_count = max(1, int(overlap_tokens / 1.3))
                                current_chunk_words = current_chunk_words[-overlap_words_count:] + sent_words
                                current_token_count = int(len(current_chunk_words) * 1.3)
                            else:
                                current_chunk_words.extend(sent_words)
                                current_token_count += sent_tokens
                    else:
                        if current_token_count + para_tokens > chunk_size_tokens and current_chunk_words:
                            chunk_text = " ".join(current_chunk_words)
                            chunk_obj = cls._build_chunk_model(
                                chunk_id=f"CHK-{doc_short_id}-{global_chunk_idx:03d}",
                                document_id=document_id,
                                version_id=version_id,
                                chunk_index=global_chunk_idx,
                                page_number=page.page_number,
                                section_heading=section.heading,
                                text_content=chunk_text,
                            )
                            chunks.append(chunk_obj)
                            global_chunk_idx += 1

                            overlap_words_count = max(1, int(overlap_tokens / 1.3))
                            current_chunk_words = current_chunk_words[-overlap_words_count:] + para_words
                            current_token_count = int(len(current_chunk_words) * 1.3)
                        else:
                            current_chunk_words.extend(para_words)
                            current_token_count += para_tokens

                # Emit leftover words for this section
                if current_chunk_words:
                    chunk_text = " ".join(current_chunk_words)
                    chunk_obj = cls._build_chunk_model(
                        chunk_id=f"CHK-{doc_short_id}-{global_chunk_idx:03d}",
                        document_id=document_id,
                        version_id=version_id,
                        chunk_index=global_chunk_idx,
                        page_number=page.page_number,
                        section_heading=section.heading,
                        text_content=chunk_text,
                    )
                    chunks.append(chunk_obj)
                    global_chunk_idx += 1

        return chunks

    @classmethod
    def _build_chunk_model(
        cls,
        chunk_id: str,
        document_id: str,
        version_id: str,
        chunk_index: int,
        page_number: int,
        section_heading: str,
        text_content: str,
    ) -> DocumentChunk:
        """Construct a validated DocumentChunk SQLAlchemy instance."""
        token_count = cls._estimate_tokens(text_content)
        content_hash = cls._compute_chunk_hash(text_content)
        return DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            version_id=version_id,
            chunk_index=chunk_index,
            page_number=page_number,
            section_heading=section_heading,
            text_content=text_content,
            protected_text=text_content,  # Passed to Privacy Shield in later slice
            token_count=token_count,
            content_hash=content_hash,
            embedding_id=None,
        )
