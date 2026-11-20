import re


class ClaimExtractor:
    """Decomposes generated clinical responses into atomic, self-contained declarative propositions."""

    # Conversational preambles to clean from claims
    PREAMBLE_PATTERNS = [
        r"^according to (?:the )?(?:guidelines?|clinical protocol|sources?|evidence)[,\s:]*",
        r"^in summary[,\s:]*",
        r"^based on (?:the )?(?:guidelines?|clinical evidence)[,\s:]*",
        r"^the guideline recommends that\s*",
        r"^the protocol states that\s*",
        r"^note that\s*",
        r"^furthermore[,\s:]*",
        r"^additionally[,\s:]*",
    ]

    @classmethod
    def extract_claims(cls, text: str) -> list[str]:
        """Parse raw response text into a list of atomic clinical claims."""
        if not text or not text.strip():
            return []

        # 1. Clean numbered list tags [1], 1., (1), bullets
        lines = text.strip().split("\n")
        raw_statements: list[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Strip list prefixes like [1], 1., -, *
            clean_line = re.sub(r"^(?:\[\d+\]|\d+[\.\)]|[\-\*\•])\s*", "", line_str).strip()
            if not clean_line:
                continue

            # 2. Split sentence boundaries within line
            sentences = re.split(r"(?<=[.!?])\s+", clean_line)
            for sentence in sentences:
                s = sentence.strip()
                if not s:
                    continue

                # 3. Check for compound assertions that can be split
                sub_claims = cls._split_compound_sentences(s)
                raw_statements.extend(sub_claims)

        # 4. Clean preambles and deduplicate
        final_claims: list[str] = []
        seen = set()

        for stmt in raw_statements:
            cleaned_stmt = cls._clean_claim(stmt)
            if len(cleaned_stmt) > 15 and cleaned_stmt not in seen:
                final_claims.append(cleaned_stmt)
                seen.add(cleaned_stmt)

        return final_claims if final_claims else [text.strip()]

    @classmethod
    def _split_compound_sentences(cls, sentence: str) -> list[str]:
        """Split compound sentences with conjunctions asserting multiple separate facts."""
        # Check for ';' splits
        if ";" in sentence:
            parts = [p.strip() for p in sentence.split(";") if p.strip()]
            return parts

        # Match compound conjunctions like "followed by dynamic measures", "and additionally"
        pattern = re.compile(
            r"(?:\s*,\s*(?:and\s+)?(?:followed\s+by|additionally|furthermore|whereas|subsequently)\s+)",
            re.IGNORECASE,
        )
        parts = pattern.split(sentence)
        if len(parts) > 1 and all(len(p.strip()) > 15 for p in parts):
            return [p.strip() for p in parts]

        return [sentence]

    @classmethod
    def _clean_claim(cls, claim: str) -> str:
        """Strip conversational preambles and normalize punctuation."""
        c = claim.strip()
        for p in cls.PREAMBLE_PATTERNS:
            c = re.sub(p, "", c, flags=re.IGNORECASE).strip()
        # Capitalize first letter and ensure ending period
        if c:
            c = c[0].upper() + c[1:]
            if not c.endswith((".", "!", "?")):
                c += "."
        return c
