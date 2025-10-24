# Multi-stage build for secure Telegram Bot
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /tmp/build

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -t /tmp/build/packages -r requirements.txt

# Stage 2: Runtime (hardened)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /tmp/build/packages /app/packages

# Add packages to Python path
ENV PYTHONPATH=/app/packages:$PYTHONPATH

# Copy application code
COPY bot/ ./bot/
COPY run.py .

# Create a placeholder for environment variables (actual config should be provided at runtime)
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/false botuser && \
    chown -R botuser:botuser /app

# Remove unnecessary packages for security
RUN apt-get update && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Switch to non-root user
USER botuser

# Health check (optional - checks if bot is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*run.py" || exit 1

# Run the bot with the new entry point
CMD ["python", "-u", "run.py"]
