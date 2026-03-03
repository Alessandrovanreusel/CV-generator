FROM python:3.11-slim

# Install WeasyPrint system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libcairo2 libgdk-pixbuf2.0-0 libffi-dev libxml2 libxslt1.1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy entire source tree (pyproject.toml needs src/ for setuptools)
COPY . .

RUN pip install --no-cache-dir ".[web]"

# Create non-root user and output directory
RUN useradd --create-home appuser \
    && mkdir -p /app/output \
    && chown -R appuser:appuser /app
VOLUME /app/output

# WARNING: The claude CLI must be available in PATH for AI calls.
# Mount from host or install separately. Without it, pipeline will fail.
# Example: docker run -v $(which claude):/usr/local/bin/claude -v ~/.claude:/home/appuser/.claude ...

USER appuser
EXPOSE 8000
ENV CORS_ORIGINS="http://localhost:8000"
CMD ["cv-web"]
