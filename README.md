# Terrain-View

A simplistic web-based 3D DEM & Orthoimage Viewer that visualizes Cloud Optimized GeoTIFFs (COGs). The backend provides tile encoding via TiTiler (FastAPI), while the frontend renders the terrain using deck.gl in the browser.

## Running with Docker Compose

This project is fully containerized using Docker Compose. Both the frontend and backend are run as separate Docker containers.

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. **Prepare Data Directories**
   The backend expects to read COG files from a `data/` directory mapped from the host to the container. Create this directory:

   ```bash
   mkdir -p data
   ```

2. **Populate Data (Optional, for testing)**
   If you don't have your own `.tif` files, you can generate some mock data using the included script (requires Python and dependencies locally):

   ```bash
   # From the project root, this generates testing/data/ortho.tif and testing/data/dem.tif
   cd testing
   python generate_mock_data.py
   cd ..

   # Or move the generated files into your primary data directory
   cp testing/data/*.tif data/
   ```

3. **Start the Application**
   Run the following command to build the images and start the containers:

   ```bash
   docker compose up --build
   ```

4. **Access the Application**
   - The **frontend** is available at: `http://localhost:7006`
   - The **backend** API (TiTiler) is available at: `http://localhost:8001`

### Configuration

The exposed ports can be configured by providing a `.env` file or exporting environment variables before running Docker Compose:

```bash
# Example
export BACKEND_PORT=8080
export FRONTEND_PORT=3000
docker compose up
```

By default:
- **Backend Host Port:** 8001 (Internal container port: 8000)
- **Frontend Host Port:** 7006 (Internal container port: 7000)
