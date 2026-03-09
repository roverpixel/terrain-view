import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from math import sin, cos, pi

def create_dem_and_ortho(width, height, bounds, dem_path, ortho_path):
    # Bounds: (left, bottom, right, top)
    left, bottom, right, top = bounds
    res_x = (right - left) / width
    res_y = (top - bottom) / height
    transform = from_origin(left, top, res_x, res_y)

    # Generate DEM (16-bit integer)
    x = np.linspace(0, 4*pi, width)
    y = np.linspace(0, 4*pi, height)
    xv, yv = np.meshgrid(x, y)

    dem_data = (np.sin(xv) * np.cos(yv) * 500 + 500).astype(np.uint16)

    # We leave the entire DEM populated with continuous sinusoidal waves.
    # In a real scenario, this simulates having run `gdal_fillnodata.py`
    # to extrapolate edge terrain outward underneath transparent ortho regions.
    # If this DEM had nodata (0) margins matching the ortho, deck.gl would
    # interpolate a physical wall down to 0, blocking views of depressions.

    temp_dem = "temp_dem.tif"
    with rasterio.open(
        temp_dem, 'w', driver='GTiff',
        height=height, width=width, count=1,
        dtype=dem_data.dtype, crs='+proj=latlong',
        transform=transform
    ) as dst:
        dst.write(dem_data, 1)

    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_dem, dem_path, cog_profile, in_memory=True)
    os.remove(temp_dem)

    # Generate Orthoimage
    r = (dem_data / 1000 * 200 + 50).astype(np.uint8)
    g = (dem_data / 1000 * 255).astype(np.uint8)
    b = (dem_data / 1000 * 100 + 20).astype(np.uint8)

    margin = 50
    r[:margin, :] = 0; r[-margin:, :] = 0; r[:, :margin] = 0; r[:, -margin:] = 0
    g[:margin, :] = 0; g[-margin:, :] = 0; g[:, :margin] = 0; g[:, -margin:] = 0
    b[:margin, :] = 0; b[-margin:, :] = 0; b[:, :margin] = 0; b[:, -margin:] = 0

    # Create an alpha channel based on the margin
    a = np.full((height, width), 255, dtype=np.uint8)
    a[:margin, :] = 0; a[-margin:, :] = 0; a[:, :margin] = 0; a[:, -margin:] = 0

    temp_ortho = "temp_ortho.tif"
    with rasterio.open(
        temp_ortho, 'w', driver='GTiff',
        height=height, width=width, count=4,
        dtype=r.dtype, crs='+proj=latlong',
        transform=transform
    ) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)
        dst.write(a, 4)

    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_ortho, ortho_path, cog_profile, in_memory=True)
    os.remove(temp_ortho)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    bounds = (-122.5, 37.7, -122.3, 37.8)
    create_dem_and_ortho(1024, 1024, bounds, "data/dem.tif", "data/ortho.tif")
