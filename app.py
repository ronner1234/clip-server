from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routers import search

import logging
from fastapi.responses import FileResponse
from fastapi import Request
import os
from PIL import Image

app = FastAPI(
    title="AutiPDF - Clip",
    openapi_url="/openapi.json",
    
    servers=[
        {"url": "http://{host}:8001", "description": "Dev", "variables": {"host": {"default": "localhost"}}},
    ],
)

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(search.router)

@app.get("/images/{image_path:path}")
async def get_image(image_path: str, request: Request):
    # Define the full path to the image
    full_image_path = os.path.join("images", image_path)

    # For now, we will just return the original image
    return FileResponse(full_image_path)

app.mount("/pdf_images", StaticFiles(directory="pdf_images"), name="images")