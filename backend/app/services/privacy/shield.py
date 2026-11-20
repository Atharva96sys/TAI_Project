import re
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.security import PrivacyEvent


@dataclass
class RedactedEntity:
    entity_type: str
    original_value: str
    token: str
    start_char: int
    end_char: int


@dataclass
class PrivacyScanResult:
    has_pii: bool
    total_redactions: int
    protected_text: str
    entities_detected: list[RedactedEntity] = field(default_factory=list)
    token_map: dict[str, str] = field(default_factory=dict)  # token -> original


class PrivacyShield:
    """HIPAA 18 Safe Harbor PII/PHI detection and pseudonymization engine."""

    # Deterministic pattern rules for structured HIPAA 18 entities
    PATTERNS: list[tuple[str, re.Pattern]] = [
        # Medical Record Numbers (MRN)
        ("MRN", re.compile(r"\b(?:MRN|Medical\s+Record\s+Number|Patient\s+ID)[:\s\-#]*([A-Za-z0-9]{6,12})\b", re.IGNORECASE)),
        # Social Security Numbers (SSN)
        ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        # Phone numbers (US & international standard formats)
        ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
        # Email addresses
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")),
        # Dates (DOB, admission, discharge: YYYY-MM-DD, MM/DD/YYYY, etc.)
        ("DATE_OF_BIRTH", re.compile(r"\b(?:DOB|Date\s+of\s+Birth|Born)[:\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", re.IGNORECASE)),
        ("DATE", re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b")),
        # Street addresses & ZIP codes
        ("ZIP_CODE", re.compile(r"\b(?:ZIP|Postal\s+Code)[:\s]*(\d{5}(?:-\d{4})?)\b", re.IGNORECASE)),
        ("ADDRESS", re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b", re.IGNORECASE)),
        # Contextual Patient Name references
        ("PATIENT_NAME", re.compile(r"\b(?:patient|for|pt\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b")),
        ("PATIENT_NAME", re.compile(r"\b(?:Mr\.|Mrs\.|Ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")),
    ]

    @classmethod
    def scan_and_pseudonymize(cls, text: str) -> PrivacyScanResult:
        """Detect and pseudonymize PII entities into synthetic tokenized placeholders."""
        if not text or not text.strip():
            return PrivacyScanResult(has_pii=False, total_redactions=0, protected_text="")

        protected = text
        entities: list[RedactedEntity] = []
        token_map: dict[str, str] = {}
        token_counters: dict[str, int] = {}

        # Scan for each pattern
        for entity_type, pattern in cls.PATTERNS:
            for match in list(pattern.finditer(protected)):
                matched_val = match.group(0).strip()
                # If matched group has subgroup (like capturing only the MRN number), prioritize that
                val_to_mask = match.group(1).strip() if match.groups() else matched_val

                # Skip if already tokenized (e.g. [MRN_001])
                if val_to_mask.startswith("[") and val_to_mask.endswith("]"):
                    continue

                counter = token_counters.get(entity_type, 0) + 1
                token_counters[entity_type] = counter
                token = f"[{entity_type}_{counter:03d}]"

                # Record entity
                entities.append(
                    RedactedEntity(
                        entity_type=entity_type,
                        original_value=val_to_mask,
                        token=token,
                        start_char=match.start(),
                        end_char=match.end(),
                    )
                )
                token_map[token] = val_to_mask

                # Replace in text
                protected = protected.replace(val_to_mask, token)

        return PrivacyScanResult(
            has_pii=len(entities) > 0,
            total_redactions=len(entities),
            protected_text=protected,
            entities_detected=entities,
            token_map=token_map,
        )

    @classmethod
    def restore_tokens(cls, protected_text: str, token_map: dict[str, str]) -> str:
        """Reversible pseudonymization restore for authorized clinical review."""
        restored = protected_text
        for token, original in token_map.items():
            restored = restored.replace(token, original)
        return restored

    @classmethod
    async def log_privacy_events(
        cls,
        session: AsyncSession,
        source_type: str,
        entities: list[RedactedEntity],
        source_id: str | None = None,
    ) -> list[PrivacyEvent]:
        """Persist recorded privacy incidents to the database."""
        events: list[PrivacyEvent] = []
        for ent in entities:
            # Mask snippet: display token and first/last char
            masked_snippet = f"{ent.token} (redacted {ent.entity_type})"
            p_ev = PrivacyEvent(
                source_type=source_type,
                source_id=source_id,
                entity_type=ent.entity_type,
                masked_snippet=masked_snippet,
                redacted_token=ent.token,
            )
            session.add(p_ev)
            events.append(p_ev)

        if events:
            await session.flush()
        return events
