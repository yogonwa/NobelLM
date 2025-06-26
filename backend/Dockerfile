# -------------------------
# STAGE 1: Builder
# -------------------------
FROM python:3.10-bullseye AS builder

WORKDIR /app

# Install build tools and virtualenv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip early to avoid surprises
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only requirements file first for better layer caching
COPY backend/requirements.txt .

# Optional: isolate heavy packages for better debugging/caching
RUN pip install --no-cache-dir numpy==1.23.5 scipy scikit-learn

# Install remaining packages
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------
# STAGE 2: Runtime
# -------------------------
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set PYTHONPATH to include /app for top-level module imports
ENV PYTHONPATH="/app:$PYTHONPATH"

# Copy application code last (to avoid cache busting earlier layers)
COPY backend/app ./app
COPY rag ./rag
COPY utils ./utils
COPY config ./config
# Data files are mounted via Fly.io volumes at /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 