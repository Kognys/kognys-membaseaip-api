# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install the membase package in development mode first
RUN pip install -e .

# Create a simple alternative for AIP imports if installation fails
# This ensures the API can start even if AIP installation has issues
RUN mkdir -p /app/fallback_modules && \
    echo "import sys; sys.path.insert(0, '/app/aip-agent/src')" > /app/fallback_modules/aip_import_fix.py

# Try to install AIP agent, but don't fail the build if it doesn't work
RUN pip install -e ./aip-agent 2>&1 || \
    (echo "Warning: aip-agent pip install failed, using fallback import method" && \
     echo "import sys; sys.path.insert(0, '/app/aip-agent/src')" >> /app/membase-api/startup_imports.py)

# Install API dependencies
RUN pip install -r membase-api/requirements.txt

# Set environment variables for Railway
ENV PORT=8000
ENV API_HOST=0.0.0.0

# Expose the port
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "membase-api/main.py"]