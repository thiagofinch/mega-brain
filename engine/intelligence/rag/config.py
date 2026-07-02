"""
RAG Configuration
=================
Centralized configuration for the RAG retrieval pipeline.
Tuning parameters live here so they can be adjusted without
touching query/index logic.
"""

# ---------------------------------------------------------------------------
# MMR (Maximal Marginal Relevance) Penalty
# ---------------------------------------------------------------------------
# Jaccard token overlap threshold above which a chunk is considered redundant
MMR_OVERLAP_THRESHOLD = 0.80

# Score penalty applied to redundant chunks (subtracted from RRF score)
MMR_PENALTY_WEIGHT = 0.3

# When True, penalty is logged but chunk is still included in results
MMR_WARN_ONLY = True
