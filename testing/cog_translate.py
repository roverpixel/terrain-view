import argparse
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles

def translate_to_cog(input_path, output_path, overview_level=None):
    """
    Translates an input GeoTIFF to a Cloud Optimized GeoTIFF (COG).
    """
    print(f"Reading {input_path}...")
    print("Translating to Cloud Optimized GeoTIFF (COG)...")

    # Use deflate compression as JPEG does not support alpha channels well
    cog_profile = cog_profiles.get("deflate")

    # Translate using rio-cogeo
    cog_translate(
        input_path,
        output_path,
        cog_profile,
        in_memory=True,
        quiet=False,
        overview_level=overview_level
    )

    print(f"Successfully wrote COG to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate a GeoTIFF to a Cloud Optimized GeoTIFF (COG).")
    parser.add_argument("input", help="Path to the input GeoTIFF.")
    parser.add_argument("output", help="Path to the output COG.")
    parser.add_argument("--overview-level", type=int, default=None, help="Number of overview levels to generate. If not set, uses rio-cogeo default.")

    args = parser.parse_args()
    translate_to_cog(args.input, args.output, overview_level=args.overview_level)
