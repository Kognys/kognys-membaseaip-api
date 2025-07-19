# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Install the membase package in development mode first
RUN pip install -e .

# Change to API directory
WORKDIR /app/membase-api

# Install API dependencies
RUN pip install -r requirements.txt

# Set environment variables for Railway
ENV PORT=8000
ENV API_HOST=0.0.0.0

# Expose the port
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "main.py"]