import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

function MapController({ geoJsonData, uploadedGeojson, setGeoJsonLayer, pointPosition }) {
  const map = useMap();
  
  useEffect(() => {
    // ... existing MapController code ...
  }, [geoJsonData, uploadedGeojson, map, pointPosition]);

  return null;
}

export default MapController; 