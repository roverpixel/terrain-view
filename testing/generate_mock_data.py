import os
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from math import sin, cos, pi

def create_dem_and_ortho(bounds, dem_path, ortho_path):
    # Bounds: (left, bottom, right, top)
    left, bottom, right, top = bounds

    # DEM is lower resolution
    dem_width = 1024
    dem_height = 1024

    # Ortho is higher resolution (x2)
    ortho_width = 2048
    ortho_height = 2048

    # Generate DEM (16-bit integer)
    dem_res_x = (right - left) / dem_width
    dem_res_y = (top - bottom) / dem_height
    dem_transform = from_origin(left, top, dem_res_x, dem_res_y)

    x = np.linspace(0, 4*pi, dem_width)
    y = np.linspace(0, 4*pi, dem_height)
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
        height=dem_height, width=dem_width, count=1,
        dtype=dem_data.dtype, crs='+proj=latlong',
        transform=dem_transform
    ) as dst:
        dst.write(dem_data, 1)

    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_dem, dem_path, cog_profile, in_memory=True)
    os.remove(temp_dem)

    # Generate Orthoimage
    ortho_res_x = (right - left) / ortho_width
    ortho_res_y = (top - bottom) / ortho_height
    ortho_transform = from_origin(left, top, ortho_res_x, ortho_res_y)

    x_ortho = np.linspace(0, 4*pi, ortho_width)
    y_ortho = np.linspace(0, 4*pi, ortho_height)
    xv_o, yv_o = np.meshgrid(x_ortho, y_ortho)
    dem_data_up = (np.sin(xv_o) * np.cos(yv_o) * 500 + 500).astype(np.uint16)

    r = (dem_data_up / 1000 * 200 + 50).astype(np.uint8)
    g = (dem_data_up / 1000 * 255).astype(np.uint8)
    b = (dem_data_up / 1000 * 100 + 20).astype(np.uint8)

    margin = 100
    r[:margin, :] = 0; r[-margin:, :] = 0; r[:, :margin] = 0; r[:, -margin:] = 0
    g[:margin, :] = 0; g[-margin:, :] = 0; g[:, :margin] = 0; g[:, -margin:] = 0
    b[:margin, :] = 0; b[-margin:, :] = 0; b[:, :margin] = 0; b[:, -margin:] = 0

    # Create an alpha channel based on the margin
    a = np.full((ortho_height, ortho_width), 255, dtype=np.uint8)
    a[:margin, :] = 0; a[-margin:, :] = 0; a[:, :margin] = 0; a[:, -margin:] = 0

    temp_ortho = "temp_ortho.tif"
    with rasterio.open(
        temp_ortho, 'w', driver='GTiff',
        height=ortho_height, width=ortho_width, count=4,
        dtype=r.dtype, crs='+proj=latlong',
        transform=ortho_transform
    ) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)
        dst.write(a, 4)

    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_ortho, ortho_path, cog_profile, in_memory=True)
    os.remove(temp_ortho)

    # Automatically erode the alpha channel of the generated ortho
    # This matches the preprocessing requirement to fix striped draping
    # by ensuring the edge of the ortho alpha mask is slightly recessed
    # from any physical geometry walls.
    print("Eroding alpha channel of generated orthoimage...")
    from erode_alpha import erode_alpha
    erode_alpha(ortho_path, ortho_path, iterations=2)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    bounds = (-122.5, 37.7, -122.3, 37.8)
    create_dem_and_ortho(bounds, "data/dem.tif", "data/ortho.tif")
