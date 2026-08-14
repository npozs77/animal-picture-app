"""FastAPI application — endpoints for fetching and retrieving animal pictures."""

import base64
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import (
    DB_PATH,
    evict_old_batches,
    get_all_pictures,
    get_latest_batch,
    init_db,
    save_pictures,
)
from app.fetcher import fetch_pictures


class Animal(str, Enum):
    cat = "cat"
    dog = "dog"
    bear = "bear"


class FetchRequest(BaseModel):
    animal: Animal
    count: Annotated[int, Field(ge=1, le=5)]


class FetchResponse(BaseModel):
    saved: int


class PicturesResponse(BaseModel):
    pictures: list[str]
    count: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db(DB_PATH)
    yield


app = FastAPI(title="Animal Picture App", lifespan=lifespan)


@app.post("/fetch", response_model=FetchResponse)
async def fetch_and_save(request: FetchRequest) -> FetchResponse:
    """Fetch random animal pictures from external APIs and store them."""
    images = await fetch_pictures(request.animal.value, request.count)

    if not images:
        raise HTTPException(status_code=502, detail="All upstream fetches failed")

    batch_id = str(uuid.uuid4())
    save_pictures(DB_PATH, request.animal.value, images, batch_id)
    evict_old_batches(DB_PATH, request.animal.value)

    return FetchResponse(saved=len(images))


@app.get("/latest/{animal}", response_model=PicturesResponse)
async def latest_pictures(
    animal: Annotated[Animal, PathParam(title="Animal type")],
) -> PicturesResponse:
    """Return all pictures from the most recent fetch call for the given animal."""
    images = get_latest_batch(DB_PATH, animal.value)

    if not images:
        raise HTTPException(status_code=404, detail=f"No pictures stored for '{animal.value}'")

    encoded = [base64.b64encode(img).decode() for img in images]
    return PicturesResponse(pictures=encoded, count=len(encoded))


@app.get("/pictures/{animal}", response_model=PicturesResponse)
async def all_pictures(
    animal: Annotated[Animal, PathParam(title="Animal type")],
) -> PicturesResponse:
    """Return all stored pictures for the given animal type."""
    images = get_all_pictures(DB_PATH, animal.value)

    if not images:
        raise HTTPException(status_code=404, detail=f"No pictures stored for '{animal.value}'")

    encoded = [base64.b64encode(img).decode() for img in images]
    return PicturesResponse(pictures=encoded, count=len(encoded))


@app.get("/image/latest/{animal}")
async def latest_single_image(
    animal: Annotated[Animal, PathParam(title="Animal type")],
) -> Response:
    """Return the single most recent image as raw bytes (for img src usage)."""
    images = get_latest_batch(DB_PATH, animal.value)
    if not images:
        raise HTTPException(status_code=404, detail=f"No pictures stored for '{animal.value}'")
    return Response(content=images[0], media_type="image/jpeg")


# Mount static files last so API routes take priority
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
