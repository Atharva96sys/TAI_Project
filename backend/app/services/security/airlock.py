import re
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.security import SecurityEvent


@dataclass
class SecurityScanResult:
    is_safe: bool
    threat_category: str | None = None
    threat_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    detected_pattern: str | None = None
    sanitized_text: str = ""
    action_taken: str = "CLEAR"  # CLEAR, BLOCKED, QUARANTINED, SANITIZED


class SecurityAirlock:
    """Zero-trust security boundary protecting LLM and retrieval pipeline from adversarial attacks."""

    # 1. Direct Prompt Injection & Jailbreak Signatures
    DIRECT_INJECTION_PATTERNS = [
        (r"\bignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions\b", "Direct Instruction Override", "HIGH"),
        (r"\breveal\s+(?:the\s+)?system\s+(?:prompt|instructions?)\b", "System Prompt Exfiltration", "HIGH"),
        (r"\b(?:you\s+are\s+now|act\s+as)\s+(?:DAN|unrestricted|jailbroken|god\s+mode)\b", "Persona Jailbreak (DAN)", "CRITICAL"),
        (r"\bdisregard\s+(?:medical\s+)?safety\s+(?:guidelines?|protocols?|rules?)\b", "Safety Boundary Bypass", "CRITICAL"),
        (r"\bdeveloper\s+mode\s+(?:enabled|activated|on)\b", "Developer Mode Jailbreak", "HIGH"),
        (r"\bsimulate\s+(?:a\s+doctor|physician)\s+with\s+no\s+(?:restrictions|ethics|rules)\b", "Unrestricted Roleplay Attack", "HIGH"),
        (r"\bforget\s+(?:all\s+)?(?:rules|guidelines|safeguards)\b", "Safeguard Erasure", "HIGH"),
        (r"\boutput\s+(?:your\s+)?initial\s+prompt\b", "Prompt Leakage Probe", "MEDIUM"),
        (r"\b(?:base64|rot13|hex)\s+decode\s+and\s+execute\b", "Obfuscated Payload Execution", "HIGH"),
        (r"\bjailbreak\b|\bprompt\s+injection\b", "Adversarial Keyword Probe", "MEDIUM"),
        (r"\bdo\s+anything\s+now\b", "DAN Mode Variant", "HIGH"),
        (r"\bexecute\s+arbitrary\s+code\b", "Code Execution Exploit", "CRITICAL"),
        (r"system\s*:\s*you\s+must\b", "System Role Impersonation", "HIGH"),
        (r"\[SYSTEM(?:\s+PROMPT)?\]", "System Delimiter Injection", "HIGH"),
        (r"\[AI\s+INSTRUCTION\]|\[ADMIN\s+OVERRIDE\]|\[SYSTEM\s+COMMAND\]", "Instruction Channel Breakout Tag", "CRITICAL"),
        (r"<\s*script\s*>", "Script Injection / XSS in Prompt", "HIGH"),
    ]

    # 2. Indirect Document Injection Signatures (inside uploaded clinical PDFs / TXT)
    INDIRECT_INJECTION_PATTERNS = [
        (r"(?:IMPORTANT|NOTICE|OVERRIDE):\s*Always\s+(?:recommend|prescribe|administer)\s+[A-Za-z0-9\-]+", "Biased Therapy Manipulation Injection", "HIGH"),
        (r"(?:ignore|disregard)\s+(?:the\s+)?(?:standard|above|prior)\s+(?:sepsis|clinical|dosage)\s+protocol", "Clinical Protocol Subversion", "CRITICAL"),
        (r"\[AI\s+INSTRUCTION\]|\[ADMIN\s+OVERRIDE\]|\[SYSTEM\s+COMMAND\]", "Instruction Channel Breakout Tag", "CRITICAL"),
        (r"when\s+asked\s+about\s+.+,\s+respond\s+with\b", "Conditional Response Poisoning", "HIGH"),
        (r"(?:send|exfiltrate|post)\s+(?:all\s+)?patient\s+data\s+to\s+http", "Exfiltration Webhook Injection", "CRITICAL"),
    ]

    @classmethod
    def scan_query(cls, query: str) -> SecurityScanResult:
        """Scan incoming clinical inquiry prompt for direct injection and jailbreak exploits."""
        if not query or not query.strip():
            return SecurityScanResult(is_safe=True, sanitized_text="")

        normalized = query.strip()

        for pattern, threat_desc, severity in cls.DIRECT_INJECTION_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                return SecurityScanResult(
                    is_safe=False,
                    threat_category=threat_desc,
                    threat_level=severity,
                    detected_pattern=match.group(0),
                    sanitized_text="[SECURITY AIRLOCK: BLOCKED ADVERSARIAL QUERY]",
                    action_taken="BLOCKED",
                )

        return SecurityScanResult(
            is_safe=True,
            threat_category=None,
            threat_level="LOW",
            detected_pattern=None,
            sanitized_text=normalized,
            action_taken="CLEAR",
        )

    @classmethod
    def scan_document_text(cls, text: str, document_title: str = "Uploaded Guideline") -> SecurityScanResult:
        """Scan clinical document content during ingestion for indirect prompt injections."""
        if not text or not text.strip():
            return SecurityScanResult(is_safe=True, sanitized_text="")

        for pattern, threat_desc, severity in cls.INDIRECT_INJECTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return SecurityScanResult(
                    is_safe=False,
                    threat_category=f"{threat_desc} in '{document_title}'",
                    threat_level=severity,
                    detected_pattern=match.group(0),
                    sanitized_text=text,
                    action_taken="QUARANTINED",
                )

        # Also screen for direct instruction tags
        for pattern, threat_desc, severity in cls.DIRECT_INJECTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return SecurityScanResult(
                    is_safe=False,
                    threat_category=f"Document Embedded Jailbreak ({threat_desc})",
                    threat_level=severity,
                    detected_pattern=match.group(0),
                    sanitized_text=text,
                    action_taken="QUARANTINED",
                )

        return SecurityScanResult(
            is_safe=True,
            threat_category=None,
            threat_level="LOW",
            detected_pattern=None,
            sanitized_text=text,
            action_taken="CLEAR",
        )

    @classmethod
    def isolate_evidence_chunk(cls, chunk_id: str, document_version: str, raw_content: str) -> str:
        """Encapsulate evidence chunks in immutable XML-safe boundary tags to prevent breakout."""
        # Sanitize any attempted closing boundary tag inside document text
        sanitized = raw_content.replace("</untrusted_clinical_evidence>", "&lt;/untrusted_clinical_evidence&gt;")
        return (
            f'<untrusted_clinical_evidence chunk_id="{chunk_id}" version="{document_version}">\n'
            f'{sanitized}\n'
            f'</untrusted_clinical_evidence>'
        )

    @classmethod
    async def log_security_event(
        cls,
        session: AsyncSession,
        event_type: str,
        threat_level: str,
        source_type: str,
        detected_pattern: str,
        action_taken: str,
        source_id: str | None = None,
    ) -> SecurityEvent:
        """Persist a security event record to the database."""
        sec_event = SecurityEvent(
            event_type=event_type,
            threat_level=threat_level,
            source_type=source_type,
            source_id=source_id,
            detected_pattern=detected_pattern,
            action_taken=action_taken,
        )
        session.add(sec_event)
        await session.flush()
        return sec_event
