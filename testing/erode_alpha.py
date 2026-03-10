import argparse
import rasterio
import numpy as np
from scipy.ndimage import binary_erosion
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import os

def erode_alpha(input_path, output_path, iterations=2):
    """
    Erodes the alpha channel (Band 4) of an RGBA GeoTIFF inward by a small amount.
    This ensures that when 3D terrain skirts drop down at the boundaries of the
    visible data, the textures on those skirts are completely transparent,
    preventing "striped draping" artifacts.
    """
    print(f"Reading {input_path}...")
    with rasterio.open(input_path) as src:
        # Check if the image has at least 4 bands (assumed RGBA)
        if src.count < 4:
            raise ValueError("Input image must have at least 4 bands (RGBA).")

        # Read the first 4 bands (RGB and Alpha)
        r = src.read(1)
        g = src.read(2)
        b = src.read(3)
        alpha = src.read(4)

        profile = src.profile

    print(f"Eroding alpha channel by {iterations} iteration(s)...")
    # Alpha is typically 0 (transparent) or 255 (opaque). We erode the opaque region.
    # binary_erosion considers True (non-zero) as the object to be eroded.
    alpha_mask = alpha > 0
    eroded_mask = binary_erosion(alpha_mask, iterations=iterations)

    # Apply the eroded mask back to the alpha channel (preserving original opaque values, usually 255)
    new_alpha = np.zeros_like(alpha)
    # We could just do new_alpha[eroded_mask] = 255, but to be safe with partial transparencies
    # we copy the original alpha values where the eroded mask is still True.
    new_alpha[eroded_mask] = alpha[eroded_mask]

    # We also need to zero out RGB where alpha is now 0 to prevent color leaking
    # if clamping or texture interpolation happens.
    r[~eroded_mask] = 0
    g[~eroded_mask] = 0
    b[~eroded_mask] = 0

    # Write to a temporary file first before converting to COG
    temp_path = output_path + ".tmp.tif"
    profile.update(count=4)
    print("Writing temporary eroded file...")
    with rasterio.open(temp_path, 'w', **profile) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)
        dst.write(new_alpha, 4)

    print("Translating to Cloud Optimized GeoTIFF (COG)...")
    # Use deflate compression as JPEG does not support alpha channels well
    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_path, output_path, cog_profile, in_memory=True, quiet=True)

    print("Cleaning up temporary file...")
    os.remove(temp_path)
    print(f"Successfully wrote eroded COG to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Erode the alpha channel of an RGBA Orthoimage.")
    parser.add_argument("input", help="Path to the input RGBA GeoTIFF.")
    parser.add_argument("output", help="Path to the output eroded COG.")
    parser.add_argument("--iterations", type=int, default=2, help="Number of pixels to erode the alpha mask inward. (default: 2)")

    args = parser.parse_args()
    erode_alpha(args.input, args.output, args.iterations)
