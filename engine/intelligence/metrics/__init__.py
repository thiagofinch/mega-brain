"""
core.intelligence.metrics — Observability metrics for AI pipelines.
===================================================================

Submodules
----------
entropy
    Measures convergence, dominance, and diversity across multi-agent
    outputs (conclave / roundtable sessions).

faithfulness
    Deterministic string-match grounded_ratio for conclave outputs.
    Measures what percentage of agent claims are grounded in retrieved
    context.  Async post-processing, never in critical path.
"""
