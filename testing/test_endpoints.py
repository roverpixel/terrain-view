import requests
import sys

def test_endpoints():
    base_url = "http://localhost:8000"
    # Same tile coordinate requested by the frontend in earlier tests
    tile_z, tile_x, tile_y = 11, 327, 791

    # Use the absolute container paths as we simulate the frontend request
    dem_url = "/app/data/dem.tif"
    ortho_url = "/app/data/ortho.tif"

    print(f"Testing DEM endpoint for {dem_url} at tile {tile_z}/{tile_x}/{tile_y}...")
    dem_req = f"{base_url}/dem/tiles/WebMercatorQuad/{tile_z}/{tile_x}/{tile_y}@1x?url={dem_url}"
    dem_resp = requests.get(dem_req)

    if dem_resp.status_code == 200:
        print("✅ DEM tile request successful.")
    else:
        print(f"❌ DEM tile request failed with status {dem_resp.status_code}: {dem_resp.text}")
        sys.exit(1)

    print(f"Testing Ortho endpoint for {ortho_url} at tile {tile_z}/{tile_x}/{tile_y}...")
    ortho_req = f"{base_url}/ortho/tiles/WebMercatorQuad/{tile_z}/{tile_x}/{tile_y}@1x?url={ortho_url}"
    ortho_resp = requests.get(ortho_req)

    if ortho_resp.status_code == 200:
        print("✅ Ortho tile request successful.")
    else:
        print(f"❌ Ortho tile request failed with status {ortho_resp.status_code}: {ortho_resp.text}")
        sys.exit(1)

    print("All endpoints returned 200 OK.")

if __name__ == "__main__":
    test_endpoints()
