from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.documents import router as documents_router
from backend.app.api.retrieval import router as retrieval_router
from backend.app.api.review import router as review_router
from backend.app.api.verification import router as verification_router
from backend.app.api.security import router as security_router
from backend.app.api.privacy import router as privacy_router
from backend.app.api.audit import router as audit_router
from backend.app.api.governance import router as governance_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.v1 import router as v1_router
from backend.app.core.config import settings
from backend.app.core.database import async_session_factory, init_db
from backend.app.services.retrieval.engine import retrieval_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialize database tables and synchronize index state."""
    settings.init_directories()
    await init_db()
    async with async_session_factory() as session:
        await retrieval_engine.sync_from_database(session)
    yield
    retrieval_engine.save_indexes()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Trustworthy Clinical AI Verification & Decision-Support Platform API",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Subrouters
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(retrieval_router, prefix=settings.API_PREFIX)
app.include_router(verification_router, prefix=settings.API_PREFIX)
app.include_router(review_router, prefix=settings.API_PREFIX)
app.include_router(security_router, prefix=settings.API_PREFIX)
app.include_router(privacy_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(governance_router, prefix=settings.API_PREFIX)
app.include_router(evaluation_router, prefix=settings.API_PREFIX)
app.include_router(v1_router, prefix=settings.API_PREFIX)


@app.get("/api/health", tags=["System Health"])
async def health_check():
    """Health check endpoint communicating system operational status."""
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "indexed_chunks": retrieval_engine.get_stats()["total_vector_chunks"],
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "status": "ONLINE",
    }
