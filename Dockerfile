
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_production.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 miniapp && chown -R miniapp:miniapp /app
USER miniapp

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run unified application (Bot + Mini App Server)
CMD ["python", "main_unified.py"]
