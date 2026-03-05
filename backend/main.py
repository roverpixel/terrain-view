from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from rio_tiler.models import ImageData
import numpy as np

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
    """Encode elevation data into RGB terrain."""
    elevation = img.array[0] # Note: older rio-tiler uses .data, newer uses .array
    # wait, earlier when checking logs, `img.data[0]` worked, but `ImageData(data=new_data)` failed.
    # Looking at the traceback: `TypeError: ImageData.__init__() got an unexpected keyword argument 'data'`
    # Ah! `ImageData(array=new_data)` is the correct signature in rio-tiler >= 3.0.0.
    v = (elevation.astype("float32") + 10000) * 10
    v = np.clip(v, 0, 16777215) # max for 24-bit RGB
    r = (v // 65536).astype("uint8")
    g = ((v % 65536) // 256).astype("uint8")
    b = (v % 256).astype("uint8")
    new_data = np.stack([r, g, b])

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
