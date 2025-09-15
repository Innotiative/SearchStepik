import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import *
from app.services import encoder, qdrant
from app.config import settings

from contextlib import asynccontextmanager
from .config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the embedding model
    await encoder.initialize()
    print("Connecting to qdrant", flush=True)
    qdrant.initialize(settings.qdrant_host, settings.qdrant_port)
    if settings.load_courses:
        app.state.courses_load_task = asyncio.create_task(qdrant.loadCourses())
    yield


app = FastAPI(
    docs_url="/api/swagger",  # вместо /docs
    redoc_url="/api/redocly",  # вместо /redoc
    openapi_url="/api/schema",  # вместо /openapi.json
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stepik.router)


logger.info("Application started")


@app.get("/")
async def root():
    return {"message": "Hello Universe!"}
