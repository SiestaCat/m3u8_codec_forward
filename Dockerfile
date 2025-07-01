FROM python:3.11-slim

# Install FFmpeg, VLC and other system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    vlc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY setup.py .
COPY pytest.ini .
COPY api.html .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create working directory for transcoding
RUN mkdir -p /app/workdir

# Expose port
EXPOSE 80

# Set environment variables
ENV PYTHONPATH=/app/src
ENV WORKING_DIR=/app/workdir

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:80/health')" || exit 1

# Run the application
CMD ["python", "-m", "m3u8_codec_forward.main", "--host", "0.0.0.0", "--port", "80"]