FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        curl \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create directory for SQLite database
RUN mkdir -p /app/data

# Create non-root user
RUN adduser --disabled-password --gecos '' dianabot \
    && chown -R dianabot:dianabot /app
USER dianabot

# Expose port (opcional, para health checks)
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
