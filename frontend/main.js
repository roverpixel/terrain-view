import { Deck } from '@deck.gl/core';
import { TerrainLayer } from '@deck.gl/geo-layers';

// Use absolute paths for the data files to avoid any relative path resolution issues in backend
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
const DEM_URL = '/app/dem/mock_dem.tif';
const ORTHO_URL = '/app/ortho/mock_ortho.tif';

const elevationDecoder = {
  rScaler: 25.6,
  gScaler: 0.1,
  bScaler: 0.00390625,
  offset: -10000
};

const INITIAL_VIEW_STATE = {
  latitude: 37.75,
  longitude: -122.4,
  zoom: 11,
  bearing: 0,
  pitch: 45,
  maxZoom: 16,
  minZoom: 1
};

let exaggeration = 1.0;

// The endpoint format for TiTiler WebMercatorQuad tiles is `/tiles/WebMercatorQuad/{z}/{x}/{y}@1x`
// Let's use the standard `{z}/{x}/{y}` endpoint for simplicity if it works, or fallback to WebMercatorQuad.
// Actually standard TiTiler default for `tiles` is `/tiles/{z}/{x}/{y}` or `/tiles/WebMercatorQuad/{z}/{x}/{y}`
// Let's use `/tiles/WebMercatorQuad/{z}/{x}/{y}@1x` as that's what was in TileJSON.

const deck = new Deck({
  container: 'app',
  initialViewState: INITIAL_VIEW_STATE,
  controller: true,
  layers: [
    new TerrainLayer({
      id: 'terrain-layer',
      elevationData: `${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=${encodeURIComponent(DEM_URL)}`,
      texture: `${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=${encodeURIComponent(ORTHO_URL)}`,
      elevationDecoder: elevationDecoder,
      bounds: [-122.5, 37.7, -122.3, 37.8],
      wireframe: false,
      color: [255, 255, 255],
      elevationMultiplier: exaggeration,
      transparentColor: [0, 0, 0, 0]
    })
  ]
});

const slider = document.getElementById('exaggeration');
const valLabel = document.getElementById('exag-val');

slider.addEventListener('input', (e) => {
  exaggeration = parseFloat(e.target.value);
  valLabel.textContent = exaggeration.toFixed(1);

  const terrainLayer = new TerrainLayer({
    id: 'terrain-layer',
    elevationData: `${BACKEND_URL}/dem/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=${encodeURIComponent(DEM_URL)}`,
    texture: `${BACKEND_URL}/ortho/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=${encodeURIComponent(ORTHO_URL)}`,
    elevationDecoder: elevationDecoder,
    bounds: [-122.5, 37.7, -122.3, 37.8],
    wireframe: false,
    color: [255, 255, 255],
    elevationMultiplier: exaggeration,
    transparentColor: [0, 0, 0, 0]
  });

  deck.setProps({
    layers: [terrainLayer]
  });
});
