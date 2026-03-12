#!/usr/bin/env python3
"""
SELF-RAG VERIFICATION - Phase 5.3
====================================
Post-generation verification: checks if a response is faithful
to the retrieved context chunks.

Workflow:
1. Extract claims from a response
2. Verify each claim against retrieved chunks
3. Score faithfulness (0-1)
4. Flag unsupported claims as speculation
5. If hallucination detected → suggest correction via CRAG pattern

Uses heuristic verification (no LLM call required).
Can be enhanced with LLM-as-judge when available.

Versao: 1.0.0
Data: 2026-03-01
"""

import re

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
MIN_CLAIM_LENGTH = 20         # Minimum chars for a claim
MATCH_THRESHOLD = 0.25        # Minimum overlap score to consider supported
FAITHFULNESS_TARGET = 0.9     # Target faithfulness score
SPECULATION_MARKERS = [
    "provavelmente", "talvez", "acredito que", "penso que",
    "probably", "maybe", "i think", "i believe",
    "possivelmente", "possibly", "might", "could be",
    "na minha opiniao", "in my opinion",
]


# ---------------------------------------------------------------------------
# CLAIM EXTRACTION
# ---------------------------------------------------------------------------
def extract_claims(response: str) -> list[dict]:
    """Extract verifiable claims from a response.

    A claim is a sentence that makes a factual assertion.
    Excludes questions, hedged statements, and meta-commentary.

    Returns: [{"text": str, "type": "factual"|"speculative"|"opinion", "line": int}]
    """
    claims = []

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', response)

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) < MIN_CLAIM_LENGTH:
            continue

        # Skip questions
        if sentence.endswith("?"):
            continue

        # Skip meta-commentary
        if re.match(r'^(?:vou|let me|aqui|here|note|nota)', sentence.lower()):
            continue

        # Classify claim type
        claim_type = "factual"

        # Check for speculation markers
        sentence_lower = sentence.lower()
        for marker in SPECULATION_MARKERS:
            if marker in sentence_lower:
                claim_type = "speculative"
                break

        # Check for RAG citations (already supported)
        has_citation = bool(re.search(r'\[RAG:', sentence))

        claims.append({
            "text": sentence,
            "type": claim_type,
            "line": i + 1,
            "has_citation": has_citation,
        })

    return claims


# ---------------------------------------------------------------------------
# CLAIM VERIFICATION
# ---------------------------------------------------------------------------
def verify_claim(claim: str, chunks: list[str]) -> dict:
    """Verify a single claim against retrieved chunks.

    Uses token overlap scoring (heuristic, no LLM needed).

    Returns:
        {
            "supported": bool,
            "score": float (0-1),
            "best_chunk_idx": int,
            "matching_terms": [str],
        }
    """
    if not chunks:
        return {"supported": False, "score": 0.0,
                "best_chunk_idx": -1, "matching_terms": []}

    claim_tokens = _tokenize(claim)
    if not claim_tokens:
        return {"supported": False, "score": 0.0,
                "best_chunk_idx": -1, "matching_terms": []}

    best_score = 0.0
    best_idx = -1
    best_terms: list[str] = []

    for idx, chunk in enumerate(chunks):
        chunk_tokens = _tokenize(chunk)
        if not chunk_tokens:
            continue

        # Calculate overlap
        claim_set = set(claim_tokens)
        chunk_set = set(chunk_tokens)
        overlap = claim_set & chunk_set

        # Filter out very common words
        meaningful_overlap = {t for t in overlap if len(t) >= 4}

        if not claim_set:
            continue

        score = len(meaningful_overlap) / len(claim_set)

        # Bonus for exact phrase matches
        claim_lower = claim.lower()
        chunk_lower = chunk.lower()
        for phrase_len in [4, 3, 2]:
            claim_ngrams = _get_ngrams(claim_tokens, phrase_len)
            chunk_ngrams = _get_ngrams(chunk_tokens, phrase_len)
            phrase_overlap = claim_ngrams & chunk_ngrams
            if phrase_overlap:
                score += 0.1 * phrase_len * len(phrase_overlap)

        # Bonus for number matches
        claim_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', claim_lower))
        chunk_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', chunk_lower))
        number_overlap = claim_numbers & chunk_numbers
        if number_overlap:
            score += 0.2 * len(number_overlap)

        if score > best_score:
            best_score = score
            best_idx = idx
            best_terms = sorted(meaningful_overlap)

    return {
        "supported": best_score >= MATCH_THRESHOLD,
        "score": min(1.0, round(best_score, 4)),
        "best_chunk_idx": best_idx,
        "matching_terms": best_terms[:10],
    }


def verify_response(
    response: str,
    chunks: list[str],
    chunk_ids: list[str] | None = None,
) -> dict:
    """Verify an entire response against retrieved chunks.

    Args:
        response: The generated response text
        chunks: List of retrieved chunk texts
        chunk_ids: Optional chunk IDs for attribution

    Returns:
        {
            "faithfulness": float (0-1),
            "total_claims": int,
            "supported_claims": int,
            "unsupported_claims": int,
            "speculative_claims": int,
            "claims": [{text, type, supported, score, source_chunk}, ...],
            "verdict": "faithful"|"partially_faithful"|"unfaithful",
        }
    """
    claims = extract_claims(response)

    if not claims:
        return {
            "faithfulness": 1.0,
            "total_claims": 0,
            "supported_claims": 0,
            "unsupported_claims": 0,
            "speculative_claims": 0,
            "claims": [],
            "verdict": "faithful",
        }

    verified_claims = []
    supported_count = 0
    unsupported_count = 0
    speculative_count = 0

    for claim in claims:
        if claim["type"] == "speculative":
            speculative_count += 1
            verified_claims.append({
                "text": claim["text"],
                "type": "speculative",
                "supported": None,  # Not verified (explicitly speculative)
                "score": None,
            })
            continue

        # Verify factual claims
        verification = verify_claim(claim["text"], chunks)

        source_chunk = None
        if verification["best_chunk_idx"] >= 0 and chunk_ids:
            idx = verification["best_chunk_idx"]
            if idx < len(chunk_ids):
                source_chunk = chunk_ids[idx]

        if verification["supported"]:
            supported_count += 1
        else:
            unsupported_count += 1

        verified_claims.append({
            "text": claim["text"],
            "type": claim["type"],
            "supported": verification["supported"],
            "score": verification["score"],
            "source_chunk": source_chunk,
            "matching_terms": verification["matching_terms"],
        })

    # Calculate faithfulness
    factual_claims = supported_count + unsupported_count
    if factual_claims == 0:
        faithfulness = 1.0
    else:
        faithfulness = supported_count / factual_claims

    # Verdict
    if faithfulness >= 0.9:
        verdict = "faithful"
    elif faithfulness >= 0.6:
        verdict = "partially_faithful"
    else:
        verdict = "unfaithful"

    return {
        "faithfulness": round(faithfulness, 3),
        "total_claims": len(claims),
        "supported_claims": supported_count,
        "unsupported_claims": unsupported_count,
        "speculative_claims": speculative_count,
        "claims": verified_claims,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# CORRECTIVE RAG (CRAG) PATTERN
# ---------------------------------------------------------------------------
def suggest_corrections(verification: dict) -> list[dict]:
    """Suggest corrections for unsupported claims.

    Returns list of suggestions for each unsupported claim.
    """
    corrections = []

    for claim in verification.get("claims", []):
        if claim.get("supported") is False:
            corrections.append({
                "original": claim["text"],
                "issue": "unsupported_by_context",
                "suggestion": "Mark as speculation or remove",
                "score": claim.get("score", 0),
            })

    return corrections


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _tokenize(text: str) -> list[str]:
    """Simple tokenizer for verification."""
    return re.findall(r'[a-z\u00e0-\u024f]{2,}', text.lower())


def _get_ngrams(tokens: list[str], n: int) -> set:
    """Get n-grams from token list."""
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    print(f"\n{'='*60}")
    print("SELF-RAG VERIFICATION")
    print(f"{'='*60}\n")

    # Demo verification
    demo_response = """
    A estrutura recomendada para times de vendas outbound é a Christmas Tree Structure,
    onde BDRs ficam na base fazendo 100 calls por dia. O SDS no meio qualifica e
    entrega valor. O BC no topo fecha os deals.

    A comissão ideal para closers é entre 8-12% do valor fechado. Para top performers,
    pode chegar a 15% com bônus de performance.

    Provavelmente seria bom também implementar um CRM robusto para tracking.
    """

    demo_chunks = [
        "Christmas Tree Structure: BDR na base faz 100 calls/dia, SDS no meio "
        "qualifica e entrega valor, BC no topo fecha. Parece uma arvore de natal "
        "se voce olhar o org chart.",
        "Comissao entre 8-12% do valor fechado. Top performers podem receber ate "
        "15% com bonus de performance.",
        "1 Sales Manager para cada 6-10 closers.",
    ]

    demo_ids = ["chunk_001", "chunk_002", "chunk_003"]

    result = verify_response(demo_response, demo_chunks, demo_ids)

    print(f"Faithfulness: {result['faithfulness']}")
    print(f"Verdict: {result['verdict']}")
    print(f"Total claims: {result['total_claims']}")
    print(f"Supported: {result['supported_claims']}")
    print(f"Unsupported: {result['unsupported_claims']}")
    print(f"Speculative: {result['speculative_claims']}")

    print("\nClaims:")
    for c in result["claims"]:
        status = "✅" if c.get("supported") else ("⚠️" if c["type"] == "speculative" else "❌")
        text = c["text"][:80]
        print(f"  {status} {text}...")
        if c.get("source_chunk"):
            print(f"     Source: {c['source_chunk']}")
        if c.get("matching_terms"):
            print(f"     Terms: {', '.join(c['matching_terms'][:5])}")

    corrections = suggest_corrections(result)
    if corrections:
        print("\nCorrections needed:")
        for corr in corrections:
            print(f"  - {corr['original'][:60]}...")
            print(f"    Issue: {corr['issue']}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
