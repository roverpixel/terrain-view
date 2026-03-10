import argparse
import rasterio
import numpy as np
from scipy.ndimage import binary_erosion
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
import os

def erode_alpha(input_path, output_path, iterations=2, overview_level=None):
    """
    Erodes the alpha channel of an image inward by a small amount.
    This ensures that when 3D terrain skirts drop down at the boundaries of the
    visible data, the textures on those skirts are completely transparent,
    preventing "striped draping" artifacts. Works with single-band or RGB inputs.
    """
    print(f"Reading {input_path}...")
    with rasterio.open(input_path) as src:
        if src.count < 1:
            raise ValueError("Input image must have at least 1 band.")

        # Determine number of data bands vs alpha band
        if src.count in (1, 2):
            data_bands_count = 1
            has_alpha = src.count == 2
            alpha_band_idx = 2
        else:
            data_bands_count = 3
            has_alpha = src.count >= 4
            alpha_band_idx = 4

        bands_data = [src.read(i) for i in range(1, data_bands_count + 1)]

        # Determine the initial valid data mask based on priority:
        # 1. Alpha band
        # 2. Dataset mask
        # 3. NoData value

        if has_alpha:
            print("Using Priority 1: Alpha band found.")
            alpha = src.read(alpha_band_idx)
            valid_mask = alpha > 0
            original_alpha = alpha
        else:
            # Check for dataset mask (often used if not an explicit alpha band)
            # rasterio's `dataset_mask` returns 255 for valid data, 0 for invalid.
            # However, if there are no nodata values or masks set, it returns all 255.
            ds_mask = src.dataset_mask()

            # Check if there is an explicit nodata value on the bands
            has_nodata = any(src.nodata for i in src.indexes)

            # A true mask usually has some 0s. If it doesn't have 0s, it might just be a default mask.
            # Priority 2: dataset_mask has invalid pixels
            if 0 in ds_mask:
                 print("Using Priority 2: Dataset mask found.")
                 valid_mask = ds_mask > 0
            # Priority 3: NoData values
            elif has_nodata:
                 print(f"Using Priority 3: NoData value found ({src.nodata}).")
                 # Check the first band for nodata as a representative mask
                 valid_mask = bands_data[0] != src.nodata
            else:
                 print("Warning: No Alpha, Mask, or NoData found. The entire image will be treated as valid data.")
                 valid_mask = np.ones_like(bands_data[0], dtype=bool)

            # If we didn't have an alpha band, we create a fully opaque one for valid pixels
            original_alpha = np.where(valid_mask, 255, 0).astype(np.uint8)

        profile = src.profile

        # Once we convert to an explicit alpha band, we should remove the 'nodata'
        # property to prevent rio-cogeo from conflicting between nodata and alpha
        # and potentially recreating the very artifact we are trying to fix by making
        # the eroded black pixels "nodata" again.
        if 'nodata' in profile:
            print("Removing 'nodata' tag from profile to favor new alpha mask.")
            profile.pop('nodata')

    print(f"Eroding valid data mask by {iterations} iteration(s)...")
    # binary_erosion considers True (valid data) as the object to be eroded.
    eroded_mask = binary_erosion(valid_mask, iterations=iterations)

    # Create the new alpha channel using the eroded mask.
    new_alpha = np.zeros_like(original_alpha)
    # Preserve original alpha intensity where the eroded mask is still True.
    # If the image was originally RGB-only, original_alpha is 255 where valid.
    new_alpha[eroded_mask] = original_alpha[eroded_mask]

    # We also need to zero out data bands where alpha is now 0 to prevent color leaking
    # if clamping or texture interpolation happens.
    for i in range(data_bands_count):
        bands_data[i][~eroded_mask] = 0

    # Write to a temporary file first before converting to COG
    temp_path = output_path + ".tmp.tif"
    profile.update(count=data_bands_count + 1)
    print("Writing temporary eroded file...")
    with rasterio.open(temp_path, 'w', **profile) as dst:
        for i in range(data_bands_count):
            dst.write(bands_data[i], i + 1)
        dst.write(new_alpha, data_bands_count + 1)

    print("Translating to Cloud Optimized GeoTIFF (COG)...")
    # Use deflate compression as JPEG does not support alpha channels well
    cog_profile = cog_profiles.get("deflate")
    cog_translate(temp_path, output_path, cog_profile, in_memory=True, quiet=True, overview_level=overview_level)

    print("Cleaning up temporary file...")
    os.remove(temp_path)
    print(f"Successfully wrote eroded COG to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Erode the alpha channel of an image.")
    parser.add_argument("input", help="Path to the input GeoTIFF.")
    parser.add_argument("output", help="Path to the output eroded COG.")
    parser.add_argument("--iterations", type=int, default=2, help="Number of pixels to erode the alpha mask inward. (default: 2)")
    parser.add_argument("--overview-level", type=int, default=None, help="Number of overview levels to generate. If not set, uses rio-cogeo default.")

    args = parser.parse_args()
    erode_alpha(args.input, args.output, args.iterations, args.overview_level)
