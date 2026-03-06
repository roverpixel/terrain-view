import { Deck, MapView, Layer } from '@deck.gl/core';
import { TerrainLayer } from '@deck.gl/geo-layers';

// Use absolute paths for the data files to avoid any relative path resolution issues in backend
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://serverhost:8000';
const DEM_URL = '/app/data/dem.tif';
const ORTHO_URL = '/app/data/ortho.tif';

const elevationDecoder = {
  rScaler: 6553.6,   // Logic: (256 * 256) / 10
  gScaler: 25.6,     // Logic: 256 / 10
  bScaler: 0.1,      // Logic: 1 / 10
  offset: -10000     // Matches the backend +10000 offset
};

let exaggeration = 1.0;
let deck;
let dynamicBounds = null;

async function initViewer() {
  try {
    // Fetch TileJSON or Info to get the actual bounds and center of the data
    const response = await fetch(`${BACKEND_URL}/ortho/WebMercatorQuad/tilejson.json?url=${ORTHO_URL}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch dataset metadata: ${response.statusText}`);
    }

    const tileJson = await response.json();
    dynamicBounds = tileJson.bounds;

    let centerLon = -122.4;
    let centerLat = 37.75;
    let centerZoom = 11;
    let minZoom = 1;
    let maxZoom = 16;

    if (tileJson.center) {
      centerLon = tileJson.center[0];
      centerLat = tileJson.center[1];
      centerZoom = tileJson.center[2] || 11;
    } else if (dynamicBounds) {
      centerLon = (dynamicBounds[0] + dynamicBounds[2]) / 2;
      centerLat = (dynamicBounds[1] + dynamicBounds[3]) / 2;
    }

    if (tileJson.minzoom !== undefined) minZoom = tileJson.minzoom;
    if (tileJson.maxzoom !== undefined) maxZoom = tileJson.maxzoom;

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
      views: [
        new MapView({
          id: 'map',
          controller: true
        })
      ],
      layers: [
        new TerrainLayer({
          id: 'terrain-layer',
          elevationData: `${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${DEM_URL}`,
          texture: `${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${ORTHO_URL}`,
          elevationDecoder: elevationDecoder,
          bounds: dynamicBounds,
          wireframe: false,
          color: [255, 255, 255],
          elevationMultiplier: exaggeration,
          transparentColor: [0, 0, 0, 0],
          fetch: (url, context) => {
            if (context.propName === 'texture') {
              return fetch(url, { signal: context.signal })
                .then(res => res.blob())
                .then(blob => createImageBitmap(blob))
                .catch(_ => null);
            }
            return Layer.defaultProps.fetch.value(url, context);
          }
        })
      ]
    });

  } catch (error) {
    console.error('Error initializing viewer:', error);
    document.getElementById('app').innerHTML = `<div style="color: white; padding: 20px;">Error loading viewer: ${error.message}</div>`;
  }
}

const slider = document.getElementById('exaggeration');
const valLabel = document.getElementById('exag-val');

slider.addEventListener('input', (e) => {
  exaggeration = parseFloat(e.target.value);
  valLabel.textContent = exaggeration.toFixed(1);

  if (deck && dynamicBounds) {
    const terrainLayer = new TerrainLayer({
      id: 'terrain-layer',
      elevationData: `${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${DEM_URL}`,
      texture: `${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${ORTHO_URL}`,
      elevationDecoder: elevationDecoder,
      bounds: dynamicBounds,
      wireframe: false,
      color: [255, 255, 255],
      elevationMultiplier: exaggeration,
      transparentColor: [0, 0, 0, 0],
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

    deck.setProps({
      layers: [terrainLayer]
    });
  }
});

initViewer();
