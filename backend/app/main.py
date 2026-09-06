import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import register_routers
from app.schemas.root import RootResponse

setup_logging()
logger = logging.getLogger(__name__)

APP_NAME = "CivicSense"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.(vercel\.app|up\.railway\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    logger.info("Root health probe")
    return RootResponse(name=APP_NAME, version=APP_VERSION, status="running")


register_routers(app, settings.API_V1_PREFIX)

logger.info("CivicSense API started")
