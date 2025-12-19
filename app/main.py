from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.data.init_db import init_database
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize database
    logger.info("Initializing database...")
    db_path = init_database()
    logger.info(f"Database ready at: {db_path}")

    # Log configuration
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Chaos config: model_failure={settings.chaos_model_failure_rate}, "
                f"external_timeout={settings.chaos_external_timeout_rate}")

    yield

    # Shutdown
    logger.info("Shutting down service...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

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
