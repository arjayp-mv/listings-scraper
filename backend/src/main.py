# =============================================================================
# Amazon Reviews Scraper - FastAPI Application
# =============================================================================
# Purpose: Main entry point for the API server
# Public API: app
# Dependencies: fastapi, uvicorn, routers
# =============================================================================

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func

from .config import settings
from .database import SessionLocal, engine, Base
from .skus.router import router as skus_router
from .jobs.router import router as jobs_router
from .reviews.router import router as reviews_router
from .jobs.models import ScrapeJob
from .skus.models import Sku
from .workers.scraper_worker import start_worker, stop_worker


# ===== Logging Setup =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ===== Lifespan Management =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.

    Starts background worker on startup, stops on shutdown.
    """
    logger.info("Starting Amazon Reviews Scraper API")

    # Start background worker
    start_worker()
    logger.info("Background worker started")

    yield

    # Shutdown
    stop_worker()
    logger.info("Background worker stopped")
    logger.info("Shutting down API")


# ===== Application Setup =====
app = FastAPI(
    title="Amazon Reviews Scraper",
    description="API for scraping Amazon product reviews using Apify",
    version="1.0.0",
    lifespan=lifespan,
)


# ===== CORS Middleware =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Register Routers =====
app.include_router(skus_router)
app.include_router(jobs_router)
app.include_router(reviews_router)


# ===== Dashboard Endpoint =====
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Get dashboard statistics.

    Returns counts and recent activity for the dashboard page.
    """
    db = SessionLocal()
    try:
        # Job counts by status
        status_counts = dict(
            db.query(ScrapeJob.status, func.count(ScrapeJob.id))
            .group_by(ScrapeJob.status)
            .all()
        )

        # Total reviews
        total_reviews = (
            db.query(func.sum(ScrapeJob.total_reviews))
            .scalar() or 0
        )

        # Total SKUs
        total_skus = db.query(func.count(Sku.id)).scalar() or 0

        # Recent jobs
        recent_jobs = (
            db.query(ScrapeJob)
            .order_by(ScrapeJob.created_at.desc())
            .limit(5)
            .all()
        )

        recent_jobs_data = [
            {
                "id": j.id,
                "job_name": j.job_name,
                "status": j.status,
                "total_reviews": j.total_reviews,
                "created_at": j.created_at.isoformat(),
            }
            for j in recent_jobs
        ]

        return {
            "total_jobs": sum(status_counts.values()),
            "queued_jobs": status_counts.get("queued", 0),
            "running_jobs": status_counts.get("running", 0),
            "completed_jobs": status_counts.get("completed", 0),
            "failed_jobs": status_counts.get("failed", 0),
            "total_reviews": int(total_reviews),
            "total_skus": total_skus,
            "recent_jobs": recent_jobs_data,
        }
    finally:
        db.close()


# ===== Queue Status Endpoint =====
@app.get("/api/queue/status")
async def get_queue_status():
    """Get current queue status."""
    db = SessionLocal()
    try:
        queued = (
            db.query(func.count(ScrapeJob.id))
            .filter(ScrapeJob.status == "queued")
            .scalar() or 0
        )
        running = (
            db.query(func.count(ScrapeJob.id))
            .filter(ScrapeJob.status == "running")
            .scalar() or 0
        )

        return {
            "queued": queued,
            "running": running,
            "worker_interval": settings.worker_interval_seconds,
        }
    finally:
        db.close()


# ===== Health Check =====
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ===== Static Files =====
# Mount frontend directory to serve static files
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


# ===== Run Server =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
