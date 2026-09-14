"""Validate source citations before extracted claims reach human review.

This is a structural gate, not a semantic entailment checker: an exact quote
can still be irrelevant to a claim. Human review remains required.
"""

def validate_claim(claim, sources):
    if not isinstance(claim, dict):
        raise ValueError("Claim must be an object")
    if not isinstance(claim.get("text"), str) or not claim["text"].strip():
        raise ValueError("Claim text is required")
    evidence = claim.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("At least one source citation is required")
    for citation in evidence:
        if not isinstance(citation, dict):
            raise ValueError("Citation must be an object")
        source_id, quote = citation.get("source_id"), citation.get("quote")
        if not isinstance(source_id, str) or source_id not in sources:
            raise ValueError("Unknown source")
        if not isinstance(quote, str) or not quote.strip():
            raise ValueError("Nonempty quote required")
        if quote not in sources[source_id]:
            raise ValueError("Quote does not occur in the cited source")
    return {"text": claim["text"], "evidence": [dict(c) for c in evidence],
            "status": "needs_human_review"}
