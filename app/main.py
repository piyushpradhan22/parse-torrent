"""Main FastAPI application."""

import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.core.config import settings
from app.api import routes
from app.services.imdb_indexer import IMDBIndexer
from app.services.metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Torrent IMDB Parser - Extract metadata and find IMDB IDs from torrent names",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
indexer: IMDBIndexer = None
extractor: MetadataExtractor = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global indexer, extractor
    
    logger.info("Starting up Torrent IMDB Parser...")
    
    # Initialize IMDB indexer
    indexer = IMDBIndexer(settings.IMDB_INDEX_PATH)

    # Try a one-time bootstrap from local IMDb dataset when index is empty.
    if indexer.get_title_count() == 0:
        basics_tsv = os.path.join(settings.IMDB_DATASETS_PATH, "title.basics.tsv")
        basics_tsv_gz = f"{basics_tsv}.gz"
        if os.path.exists(basics_tsv) or os.path.exists(basics_tsv_gz):
            logger.info("Empty IMDB index detected. Bootstrapping from dataset path: %s", settings.IMDB_DATASETS_PATH)
            indexer.load_from_imdb_dataset(settings.IMDB_DATASETS_PATH)
        else:
            logger.info(
                "IMDB index is empty and dataset file not found at %s or %s",
                basics_tsv,
                basics_tsv_gz,
            )

    # Bootstrap episode index if not loaded yet.
    if not indexer.episode_index:
        ep_tsv = os.path.join(settings.IMDB_DATASETS_PATH, "title.episode.tsv")
        ep_gz = f"{ep_tsv}.gz"
        if os.path.exists(ep_tsv) or os.path.exists(ep_gz):
            logger.info("Bootstrapping episode index from: %s", settings.IMDB_DATASETS_PATH)
            indexer.load_episode_dataset(settings.IMDB_DATASETS_PATH)
        else:
            logger.info("Episode dataset not found at %s – episode-to-series lookup disabled", ep_gz)

    logger.info(f"IMDB indexer initialized with {indexer.get_title_count()} titles")
    
    # Initialize metadata extractor
    extractor = MetadataExtractor()
    logger.info("Metadata extractor initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global extractor
    
    logger.info("Shutting down...")
    
    if extractor:
        await extractor.close()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/stats")
async def get_stats():
    """Get application statistics."""
    global indexer
    
    return {
        "imdb_titles_indexed": indexer.get_title_count() if indexer else 0,
        "api_version": settings.APP_VERSION,
    }


# Include API routes
app.include_router(routes.router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
