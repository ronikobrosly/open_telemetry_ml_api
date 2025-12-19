from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.data.init_db import init_database
from app.core.config import settings
from app.core.telemetry import setup_telemetry, instrument_app
from app.core.logging import setup_logging
import logging

# Setup logging FIRST
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup telemetry BEFORE creating app
setup_telemetry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Service starting", extra={"version": settings.app_version})

    # Initialize database
    db_path = init_database()
    logger.info("Database initialized", extra={"path": str(db_path)})

    # Log configuration
    logger.info("Chaos configuration loaded", extra={
        "model_failure_rate": settings.chaos_model_failure_rate,
        "external_timeout_rate": settings.chaos_external_timeout_rate
    })

    yield

    # Shutdown
    logger.info("Service shutting down")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Apply auto-instrumentation AFTER creating app
instrument_app(app)

# Include routers
from app.api import search
app.include_router(search.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
