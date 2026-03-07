import { Deck, MapView, Layer, AmbientLight, LightingEffect } from '@deck.gl/core';
import { TerrainLayer } from '@deck.gl/geo-layers';

// Use absolute paths for the data files to avoid any relative path resolution issues in backend
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://serverhost:8000';
const DEM_URL = '/app/data/dem.tif';
const ORTHO_URL = '/app/data/ortho.tif';

let exaggeration = 1.0;

function getElevationDecoder(exag) {
  return {
    rScaler: 6553.6 * exag,   // Logic: (256 * 256) / 10
    gScaler: 25.6 * exag,     // Logic: 256 / 10
    bScaler: 0.1 * exag,      // Logic: 1 / 10
    offset: -10000 * exag     // Matches the backend +10000 offset
  };
}
let deck;
let dynamicBounds = null;
let demTiles = null;
let orthoTiles = null;

function createTerrainLayer(exag, bounds, elevationData, texture) {
  return new TerrainLayer({
    id: 'terrain-layer',
    elevationData: elevationData,
    texture: texture,
    elevationDecoder: getElevationDecoder(exag),
    bounds: bounds,
    wireframe: false,
    meshMaxError: 10,
    color: [255, 255, 255],
    transparentColor: [0, 0, 0, 0],
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
    const [orthoResponse, demResponse] = await Promise.all([
      fetch(`${BACKEND_URL}/ortho/WebMercatorQuad/tilejson.json?url=${ORTHO_URL}`),
      fetch(`${BACKEND_URL}/dem/WebMercatorQuad/tilejson.json?url=${DEM_URL}`)
    ]);

    if (!orthoResponse.ok) {
      throw new Error(`Failed to fetch ortho dataset metadata: ${orthoResponse.statusText}`);
    }
    if (!demResponse.ok) {
      throw new Error(`Failed to fetch dem dataset metadata: ${demResponse.statusText}`);
    }

    const tileJson = await orthoResponse.json();
    const demTileJson = await demResponse.json();

    orthoTiles = [`${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${ORTHO_URL}`];
    demTiles = [`${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x.png?url=${DEM_URL}`];
    dynamicBounds = tileJson.bounds;

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
          controller: true
        })
      ],
      layers: [
        createTerrainLayer(exaggeration, dynamicBounds, demTiles, orthoTiles)
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

  if (deck && dynamicBounds && demTiles && orthoTiles) {
    deck.setProps({
      layers: [createTerrainLayer(exaggeration, dynamicBounds, demTiles, orthoTiles)]
    });
  }
});

initViewer();
