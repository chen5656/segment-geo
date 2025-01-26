import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

const MapController = ({ geoJsonData, uploadedGeojson, setGeoJsonLayer, pointPosition }) => {
  const map = useMap();
  
  useEffect(() => {
    // Remove existing layers
    if (setGeoJsonLayer.current) {
      setGeoJsonLayer.current.remove();
    }

    // Function to create points from features
    const createPoints = (features) => {
      return features.map(feature => {
        const bounds = L.geoJSON(feature).getBounds();
        // Get coordinates based on selected position
        let point;
        switch (pointPosition) {
          case 'top-right':
            point = [bounds.getNorth(), bounds.getEast()];
            break;
          case 'top-left':
            point = [bounds.getNorth(), bounds.getWest()];
            break;
          case 'bottom-left':
            point = [bounds.getSouth(), bounds.getWest()];
            break;
          case 'bottom-right':
          default:
            point = [bounds.getSouth(), bounds.getEast()];
            break;
        }
        
        return L.circleMarker(point, {
          radius: 5,
          color: '#ff0000',
          fillColor: '#ff0000',
          fillOpacity: 1,
          weight: 1
        });
      });
    };

    // Create layers for both types of data
    const layers = [];
    
    if (geoJsonData?.features) {
      const detectionPoints = createPoints(geoJsonData.features);
      layers.push(...detectionPoints);
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
  }, [geoJsonData, uploadedGeojson, map, pointPosition]);

  return null;
};

export default MapController; 