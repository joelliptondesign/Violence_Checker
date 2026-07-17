import re
from typing import Dict, List


TERM_PATTERNS = {
    "hit": r"\bhit\b",
    "punch": r"\bpunch(?:ed)?\b",
    "kick": r"\bkick(?:ed)?\b",
    "assault": r"\bassault(?:ed)?\b",
    "swing": r"\bsw(?:ing|ung)\b",
    "grab": r"\bgrabbed\b",
}

PHRASE_PATTERNS = {
    "gonna punch": r"\bgonna\s+punch\b",
    "watch yourself": r"\bwatch\s+yourself\b",
}


def detect_violence_terms(narrative: str) -> Dict[str, object]:
    matched_terms: List[str] = []
    matched_patterns: List[str] = []

    for label, pattern in {**TERM_PATTERNS, **PHRASE_PATTERNS}.items():
        if re.search(pattern, narrative, flags=re.IGNORECASE):
            matched_terms.append(label)
            matched_patterns.append(pattern)

    return {
        "detected": bool(matched_terms),
        "matched_terms": matched_terms,
        "matched_patterns": matched_patterns,
    }
