from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from rio_tiler.models import ImageData
import numpy as np

import os
os.environ["PROJ_IGNORE_CELESTIAL_BODY"] = "YES"

app = FastAPI(title="Terrain-View Backend")

# Ensure middleware handles CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cog = TilerFactory(
    router_prefix="/ortho",
)

def elevation_to_rgb(img: ImageData) -> ImageData:
    """Encode elevation data into standard Mapbox Terrain-RGB."""
    # Convert to float64 to prevent overflow during initial math
    elevation = img.array[0].astype("float64")

    # Mapbox Formula: v = (alt + offset) * precision
    v = (elevation + 10000) * 10

    # Clip to 24-bit range and convert to uint32 for bit shifting
    v = np.clip(v, 0, 16777215).astype("uint32")

    # Bitwise shift is more robust than modulo for byte packing
    r = (v >> 16) & 255
    g = (v >> 8) & 255
    b = v & 255

    # Stack into (3, H, W) and ensure uint8 type
    new_data = np.stack([r, g, b]).astype("uint8")

    return ImageData(
        new_data,
        img.mask,
        assets=img.assets,
        crs=img.crs,
        bounds=img.bounds,
        band_names=["R", "G", "B"]
    )

class TerrainTilerFactory(TilerFactory):
    pass

dem_cog = TerrainTilerFactory(
    router_prefix="/dem",
    process_dependency=lambda: elevation_to_rgb
)

# We define the routers without prefixes inside the factory, and add them with the app prefix
app.include_router(cog.router, prefix="/ortho", tags=["Orthoimage"])
app.include_router(dem_cog.router, prefix="/dem", tags=["DEM"])

add_exception_handlers(app, DEFAULT_STATUS_CODES)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
