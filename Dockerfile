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
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.2

# Copy poetry configuration files
COPY pyproject.toml ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Generate a fresh lock file and install dependencies
RUN poetry lock --no-update && poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

# Set permissions for certs directory
RUN mkdir -p /app/certs && chmod 755 /app/certs

# Expose the port the app runs on
EXPOSE 8000

# Run the application with SSL
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]