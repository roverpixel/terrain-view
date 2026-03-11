import { Deck, MapView, Layer, AmbientLight, LightingEffect } from '@deck.gl/core';
import { TerrainLayer } from '@deck.gl/geo-layers';

// Use absolute paths for the data files to avoid any relative path resolution issues in backend
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://serverhost:8000';
const DEM_URL = '/app/data/dem.tif';
const ORTHO_URL = '/app/data/ortho.tif';

let exaggeration = 1.0;
let isWireframe = false;
let baseElevation = 0;
let maxElevation = 20000;

function getElevationDecoder(exag) {
  return {
    rScaler: 6553.6 * exag,   // Logic: (256 * 256) / 10
    gScaler: 25.6 * exag,     // Logic: 256 / 10
    bScaler: 0.1 * exag,      // Logic: 1 / 10
    // We normalize the bottom of the terrain to 0 before exaggerating,
    // so scaling pushes mountains up instead of pushing the negative base deeper.
    // We also account for the +10000 backend offset.
    offset: (-10000 - baseElevation) * exag
  };
}
let deck;
let dynamicBounds = null;
let demTiles = null;
let orthoTiles = null;
let layerMinZoom = 0;
let layerMaxZoom = 20;

function createTerrainLayer(exag, bounds, elevationData, texture, wireframe, minZoom, maxZoom) {
  // Since we normalized the base elevation to 0, the actual maximum vertical range
  // above the baseline is the difference between max and base.
  const elevationSpan = Math.max(0, maxElevation - baseElevation);

  return new TerrainLayer({
    id: 'terrain-layer',
    elevationData: elevationData,
    texture: texture,
    elevationDecoder: getElevationDecoder(exag*10),
    bounds: bounds,
    wireframe: wireframe,
    meshMaxError: 10,
    color: [255, 255, 255],
    transparentColor: [0, 0, 0, 0],
    minZoom: minZoom,
    maxZoom: maxZoom,
    // Tell deck.gl's tile culling system exactly how high the mesh stretches above z=0.
    // This perfectly fits the normalized bounding box and stops tiles from disappearing.
    zRange: [0, elevationSpan * exag],
    loadOptions: {
      terrain: {
        skirtHeight: 1000 * exag
      }
    },
    fetch: (url, context) => {
      if (context.propName === 'texture') {
        return fetch(url, { signal: context.signal })
          .then(res => res.blob())
          .then(blob => createImageBitmap(blob))
          .catch(_ => null);
      }
      return Layer.defaultProps.fetch.value(url, context);
    }
  });
}

// Setup lighting 
const ambientLight = new AmbientLight({
  color: [255, 255, 255],
  intensity: 3.0
});
const lightingEffect = new LightingEffect({ambientLight});

async function initViewer() {
  try {
    // Fetch TileJSON or Info to get the actual bounds, center, and tile endpoints of the data
    const [orthoResponse, demResponse, demStatsResponse] = await Promise.all([
      fetch(`${BACKEND_URL}/ortho/WebMercatorQuad/tilejson.json?url=${ORTHO_URL}`),
      fetch(`${BACKEND_URL}/dem/WebMercatorQuad/tilejson.json?url=${DEM_URL}`),
      fetch(`${BACKEND_URL}/dem/raw/statistics?url=${DEM_URL}`)
    ]);

    if (!orthoResponse.ok) {
      throw new Error(`Failed to fetch ortho dataset metadata: ${orthoResponse.statusText}`);
    }
    if (!demResponse.ok) {
      throw new Error(`Failed to fetch dem dataset metadata: ${demResponse.statusText}`);
    }

    const tileJson = await orthoResponse.json();
    const demTileJson = await demResponse.json();

    // Attempt to extract real base and max elevations from the raw dataset
    if (demStatsResponse.ok) {
      try {
        const statsData = await demStatsResponse.json();
        const bandKey = Object.keys(statsData)[0];
        if (bandKey && statsData[bandKey] && statsData[bandKey].min !== undefined) {
          baseElevation = statsData[bandKey].min;
          maxElevation = statsData[bandKey].max;
          console.log(`Extracted DEM stats - Min: ${baseElevation}, Max: ${maxElevation}`);
        }
      } catch (e) {
        console.warn('Failed to parse DEM statistics, falling back to defaults', e);
      }
    } else {
      console.warn('Failed to fetch DEM statistics, falling back to defaults', demStatsResponse.statusText);
    }

    orthoTiles = [`${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${ORTHO_URL}`];
    demTiles = [`${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${DEM_URL}`];
    dynamicBounds = tileJson.bounds;

    // Read minzoom and maxzoom from TileJSON
    if (demTileJson.minzoom !== undefined) layerMinZoom = demTileJson.minzoom;
    if (demTileJson.maxzoom !== undefined) layerMaxZoom = demTileJson.maxzoom;

    let centerLon = -122.4;
    let centerLat = 37.75;
    let centerZoom = 11;
    let minZoom = -10;
    let maxZoom = 20;

    if (tileJson.center) {
      centerLon = tileJson.center[0];
      centerLat = tileJson.center[1];
      centerZoom = tileJson.center[2] || 11;
    } else if (dynamicBounds) {
      centerLon = (dynamicBounds[0] + dynamicBounds[2]) / 2;
      centerLat = (dynamicBounds[1] + dynamicBounds[3]) / 2;
    }

    const initialViewState = {
      latitude: centerLat,
      longitude: centerLon,
      zoom: centerZoom,
      bearing: 0,
      pitch: 45,
      maxZoom: maxZoom,
      minZoom: minZoom
    };

    deck = new Deck({
      container: 'app',
      initialViewState: initialViewState,
      effects: [lightingEffect],
      controller: {
        dragRotate: true,
        dragMode: 'rotate'
      },
      views: [
        new MapView({
          id: 'map',
          controller: true,
          nearZMultiplier: 0.01,
          farZMultiplier: 100
        })
      ],
      layers: [
        createTerrainLayer(exaggeration, dynamicBounds, demTiles, orthoTiles, isWireframe, layerMinZoom, layerMaxZoom)
      ]
    });

  } catch (error) {
    console.error('Error initializing viewer:', error);
    document.getElementById('app').innerHTML = `<div style="color: white; padding: 20px;">Error loading viewer: ${error.message}</div>`;
  }
}

const slider = document.getElementById('exaggeration');
const valLabel = document.getElementById('exag-val');
const wireframeToggle = document.getElementById('wireframe-toggle');

slider.addEventListener('input', (e) => {
  exaggeration = parseFloat(e.target.value);
  valLabel.textContent = exaggeration.toFixed(1);

  if (deck && dynamicBounds && demTiles && orthoTiles) {
    deck.setProps({
      layers: [createTerrainLayer(exaggeration, dynamicBounds, demTiles, orthoTiles, isWireframe, layerMinZoom, layerMaxZoom)]
    });
  }
});

wireframeToggle.addEventListener('change', (e) => {
  isWireframe = e.target.checked;
  if (deck && dynamicBounds && demTiles && orthoTiles) {
    deck.setProps({
      layers: [createTerrainLayer(exaggeration, dynamicBounds, demTiles, orthoTiles, isWireframe, layerMinZoom, layerMaxZoom)]
    });
  }
});

initViewer();
