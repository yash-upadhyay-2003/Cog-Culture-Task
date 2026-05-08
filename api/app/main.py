import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.app.routes import verify as verify_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TruthLayer AI",
    description="AI-powered fact-checking API. Upload a PDF and verify its factual claims against live web data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verify_router.router, prefix="", tags=["Verification"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "TruthLayer AI API"}


@app.get("/", tags=["Info"])
async def root():
    return {
        "service": "TruthLayer AI",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoint": "POST /verify"
    }
