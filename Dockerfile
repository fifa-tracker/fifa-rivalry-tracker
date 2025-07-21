# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy pyproject.toml and uv.lock files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Set permissions for certs directory
RUN mkdir -p /app/certs && chmod 755 /app/certs

# Expose the port the app runs on
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]