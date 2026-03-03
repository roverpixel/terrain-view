# Project Overview: Web-Based 3D DEM & Orthoimage Viewer

This repository houses a high-performance web application for visualizing large (e.g., 8000x20000) 16-bit Digital Elevation Models (DEMs) and co-registered orthoimages. 

The architecture relies on streaming data dynamically based on the user's camera position, rather than loading entire datasets into memory.

## Tech Stack & Architecture

We are using a modern 3-tier spatial web stack:
1. **Data Layer:** Cloud Optimized GeoTIFFs (COGs)
2. **Backend/Middleware:** TiTiler (Python/FastAPI)
3. **Frontend:** deck.gl (JavaScript/WebGL)

---

## Agent Instructions & Coding Conventions

When writing or modifying code for this project, please adhere to the following strict guidelines:

### 1. Backend Rules (TiTiler)
* **Framework:** Python, FastAPI, and TiTiler.
* **DEM Handling:** The raw DEMs are 16-bit integer GeoTIFFs. The backend must dynamically read these via HTTP Range Requests and encode the elevation data into Mapbox Terrain-RGB PNG tiles on the fly. 
* **Orthoimage Handling:** Orthoimages must be served as standard 8-bit web tiles (PNG/JPEG) scaled to match the DEM zoom levels.
* **NoData Handling:** Orthoimages often have `NoData` (value=0) black margins due to orbital ground tracks or Sinusoidal projections. The backend should map these `NoData` values to an alpha channel so they render transparently.

### 2. Frontend Rules (deck.gl)
* **Framework:** JavaScript using the `deck.gl` library.
* **Terrain Rendering:** Use the `TerrainLayer` in deck.gl.
* **Data Sources:** Point the `TerrainLayer`'s `elevationData` to the TiTiler Terrain-RGB endpoint, and the `texture` to the TiTiler orthoimage endpoint.
* **Camera:** Implement an orbit-style camera (locked Z-axis/horizon) similar to a standard GIS turntable view. Do not use a free-floating trackball.
* **UI Controls:** Include a UI slider to dynamically adjust the Z-axis exaggeration (elevation scaling) of the terrain.

### 3. Data Processing (GDAL)
* Whenever writing data processing scripts, utilize standard `gdal_translate` and `gdaladdo` commands to convert raw GeoTIFFs into valid Cloud Optimized GeoTIFFs (COGs) with internal overviews.

### 4. General Development
* **Environment:** Keep Python dependencies in a `requirements.txt` and Node dependencies in a `package.json`.
* **Clarity:** Favor readable, well-commented code over clever one-liners. 
* **Testing:** Ensure local backend endpoints are tested and confirmed to be returning valid image bytes before wiring them to the frontend.
