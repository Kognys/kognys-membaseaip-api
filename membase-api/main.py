from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from core.config import settings
from api import agents, tasks, memory, knowledge

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Membase ID: {settings.membase_id}")
    logger.info(f"API listening on {settings.api_host}:{settings.api_port}")
    
    # Verify configuration
    if not settings.membase_account or settings.membase_account == "0x0000000000000000000000000000000000000000":
        logger.warning("MEMBASE_ACCOUNT not configured or using default value")
    
    if not settings.membase_secret_key or settings.membase_secret_key == "0x0000000000000000000000000000000000000000000000000000000000000000":
        logger.warning("MEMBASE_SECRET_KEY not configured or using default value")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Check if the API is running and healthy."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "agents": f"{settings.api_prefix}/agents",
            "tasks": f"{settings.api_prefix}/tasks",
            "memory": f"{settings.api_prefix}/memory",
            "knowledge": f"{settings.api_prefix}/knowledge"
        }
    }

# Include routers
app.include_router(agents.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(knowledge.router, prefix=settings.api_prefix)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Enable auto-reload in development
        log_level=settings.log_level.lower()
    )