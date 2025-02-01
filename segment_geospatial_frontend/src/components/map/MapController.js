import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

const MapController = ({ geoJsonData, uploadedGeojson, setGeoJsonLayer }) => {
  const map = useMap();
  
  useEffect(() => {
    // Remove existing layers
    if (setGeoJsonLayer.current) {
      setGeoJsonLayer.current.remove();
    }

    // Create layers for both types of data
    const layers = [];
    
    if (geoJsonData?.features) {
      // Directly render detection features with red color
      const detectionFeatures = geoJsonData.features.map(feature => {
        const geojson = L.geoJSON(feature, {
          style: {
            color: '#ff0000',
            weight: 2,
            opacity: 0.8,
            fillColor: '#ff0000',
            fillOpacity: 0.3
          }
        });
        return geojson;
      });
      layers.push(...detectionFeatures);
    }

    if (uploadedGeojson?.features) {
      // Use a different color for uploaded features
      const uploadedPoints = uploadedGeojson.features.map(feature => {
        const geojson = L.geoJSON(feature, {
          style: {
            color: '#0000ff',
            weight: 2,
            opacity: 0.8,
            fillColor: '#0000ff',
            fillOpacity: 0.3
          }
        });
        return geojson;
      });
      layers.push(...uploadedPoints);
    }

    if (layers.length > 0) {
      const layer = L.featureGroup(layers).addTo(map);
      setGeoJsonLayer.current = layer;
      map.fitBounds(layer.getBounds());
    }
  }, [geoJsonData, uploadedGeojson, map, setGeoJsonLayer]);

  return null;
};

export default MapController; 