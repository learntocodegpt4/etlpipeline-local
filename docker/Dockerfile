FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    apt-transport-https \
    ca-certificates \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 17 for SQL Server (modern method)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    file \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/
# Runtime entrypoint to normalize encodings and strip null bytes
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose API port
EXPOSE 8000

# Default entrypoint - sanitize source then run API
ENTRYPOINT ["/app/entrypoint.sh"]
COPY pyproject.toml .

# Copy .env if it exists
COPY .env* ./

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Remove null bytes and fix line endings in all Python files
RUN find /app/src -name "*.py" -type f -exec sed -i 's/\x0//g' {} + && \
    find /app/src -name "*.py" -type f -exec dos2unix {} + 2>/dev/null || true

# Expose API port
EXPOSE 8000

# Default command - run API server
CMD ["python", "run.py"]
#CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]