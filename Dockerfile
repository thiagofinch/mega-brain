# Mega Brain AI -- Python Engine
# Multi-stage build for minimal production image
#
# Usage:
#   docker build -t mega-brain .
#   docker run -v $(pwd)/.data:/app/.data mega-brain

FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip

# Copy dependency files
COPY pyproject.toml requirements.txt ./
COPY core/ core/

# Install Python dependencies
RUN pip install --no-cache-dir pyyaml chromadb fastapi uvicorn

FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY core/ core/
COPY agents/ agents/
COPY knowledge/ knowledge/

# Create data directories
RUN mkdir -p .data/chroma .data/embedding_cache .data/rag_index .data/benchmarks

# Non-root user
RUN useradd -m -s /bin/bash megabrain && chown -R megabrain:megabrain /app
USER megabrain

# Expose ports
EXPOSE 8200 8100

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import core; print('healthy')" || exit 1

# Default: run agent API
CMD ["uvicorn", "core.api.agent_server:app", "--host", "0.0.0.0", "--port", "8200"]
