# Use Python 3.10 slim as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core directory (contains our MCP script)
COPY core/ core/

# NOTE: DO NOT copy .env into Docker image
# Credentials are passed via environment variables at runtime
# Example: docker run -e MERCADOLIVRE_ACCESS_TOKEN=... -e MERCADOLIVRE_CLIENT_ID=...

# Entrypoint to run the MCP server
# Use -u for unbuffered output to ensure JSON-RPC lines are sent immediately
ENTRYPOINT ["python", "-u", "core/mcp/mercadolivre_mcp.py"]
