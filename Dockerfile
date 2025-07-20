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

# Install core AIP dependencies first to avoid conflicts
# Pin versions to match aip-agent requirements exactly
RUN pip install \
    autogen-core==0.4.8 \
    mcp>=1.2.1 \
    chromadb>=0.6.0 \
    instructor>=1.7.0 \
    scikit-learn>=1.6.0 \
    grpcio==1.70.0 \
    tiktoken>=0.9.0 \
    openai>=1.0.0 \
    pydantic>=2.10.4 \
    pydantic-settings>=2.7.0 \
    fastapi>=0.115.6 \
    uvicorn \
    starlette \
    loguru>=0.7.3 \
    rich>=13.9.4

# Create a fallback import mechanism
RUN mkdir -p /app/fallback_modules && \
    echo "import sys; sys.path.insert(0, '/app/aip-agent/src')" > /app/fallback_modules/aip_import_fix.py

# Now install AIP agent without dependencies to avoid conflicts
RUN pip install --no-deps -e ./aip-agent && \
    echo "import sys; sys.path.insert(0, '/app/aip-agent/src')" > /app/membase-api/startup_imports.py

# Install API dependencies
RUN pip install -r membase-api/requirements.txt

# Set environment variables for Railway
ENV PORT=8000
ENV API_HOST=0.0.0.0

# Expose the port
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "membase-api/main.py"]