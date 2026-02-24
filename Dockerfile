# ═══════════════════════════════════════════════════════════
# DIDGERI-BOOM — Docker Production Image
# Multi-stage build for minimal image size
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim AS base

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/raw_videos data/processed_videos data/upload_queue data templates

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/api/health'); exit(0 if r.status_code == 200 else 1)" || exit 1

# Launch server
CMD ["python", "server.py"]
