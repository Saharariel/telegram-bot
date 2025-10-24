# Multi-stage build for secure Telegram Bot
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (hardened)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.11/site-packages:$PYTHONPATH

# Copy application code
COPY main.py .
COPY cloudflare_access.py .

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/false botuser && \
    chown -R botuser:botuser /app && \
    chown -R botuser:botuser /root/.local

# Remove unnecessary packages for security
RUN apt-get update && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Switch to non-root user
USER botuser

# Health check (optional - checks if bot is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

# Run the bot
CMD ["python", "-u", "main.py"]
