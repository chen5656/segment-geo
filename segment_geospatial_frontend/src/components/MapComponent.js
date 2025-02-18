import React, { useState, useRef, useCallback, useEffect } from 'react';
import { MapContainer, TileLayer, FeatureGroup, LayersControl } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import L from 'leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapComponent.css';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import { useMapEvents } from 'react-leaflet';
import ControlPanel from './map/ControlPanel';
import SearchControl from './map/SearchControl';
import MapController from './map/MapController';

const { BaseLayer } = LayersControl;

const REACT_APP_SEGMENT_TEXT_PROMPT_API_URL = process.env.REACT_APP_SEGMENT_TEXT_PROMPT_API_URL;
const REACT_APP_SEGMENT_POINT_PROMPT_API_URL = process.env.REACT_APP_SEGMENT_POINT_PROMPT_API_URL;

// Create custom icons for points
const includePointIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="8" fill="green"/>
      <circle cx="12" cy="12" r="4" fill="white"/>
    </svg>
  `),
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const excludePointIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="8" fill="red"/>
      <path d="M8 8L16 16M8 16L16 8" stroke="white" stroke-width="2"/>
    </svg>
  `),
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const MapComponent = ({ center, zoom }) => {
  const [textPrompt, setTextPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const featureGroupRef = useRef();
  const geoJsonLayerRef = useRef(null);
  const [lastRequestBody, setLastRequestBody] = useState(null);// reduce duplicate requests
  const [bbox, setBbox] = useState(null);
  const [box_threshold, setBoxThreshold] = useState(0.24); // Default box threshold, can add a function to change it in the control panel
  const [text_threshold, setTextThreshold] = useState(0.24); // Default text threshold, can add a function to change it in the control panel
  const [zoomLevel, setZoomLevel] = useState(20);
  const [uploadedGeojson, setUploadedGeojson] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('detection');
  const [detectionMode, setDetectionMode] = useState('text'); // 'text' or 'interactive'
  const [ignoreSmallAreas, setIgnoreSmallAreas] = useState(false);
  const [areaThreshold, setAreaThreshold] = useState(10); // Default value in square meters
  const [interactiveBoxThreshold, setInteractiveBoxThreshold] = useState(0.24);
  const [includePoints, setIncludePoints] = useState([]);
  const [excludePoints, setExcludePoints] = useState([]);
  const [drawingMode, setDrawingMode] = useState(null);
  const isDrawingRef = useRef(false);
  const startPointRef = useRef(null);
  const rectangleRef = useRef(null);
  const [lastRequestTime, setLastRequestTime] = useState(null);

  const thresholdsRef = useRef({ box: box_threshold, text: text_threshold });

  // Update draw mode when detection mode changes
  useEffect(() => {
   
    // Clear existing drawings and points when switching modes
    if (featureGroupRef.current) {
      featureGroupRef.current.clearLayers();
      setIncludePoints([]);
      setExcludePoints([]);
    }
  }, [detectionMode]);

  const handleDetectionModeChange = (event, newValue) => {
    setDetectionMode(newValue);
    handleClear();
  };

  const handleDetect = useCallback(async () => {
    if (isLoading) {
      return;
    }
    console.log('handleDetect');

    let requestBody = null;
    let apiUrl = null;

    if (detectionMode === 'text') {
      if (!bbox || !textPrompt) {
        alert('Please draw a rectangle and enter detection parameters');
        return;
      }
      requestBody = {
        bounding_box: bbox,
        text_prompt: textPrompt,
        zoom_level: zoomLevel,
        box_threshold: thresholdsRef.current.box,
        text_threshold: thresholdsRef.current.text,
      };
      apiUrl = `${REACT_APP_SEGMENT_TEXT_PROMPT_API_URL}`;
    }else if (detectionMode === 'interactive') {
      if (!includePoints.length) {
        alert('Please add at least one include point');
        return;
      }
      requestBody = {
        zoom_level: zoomLevel,
        box_threshold: thresholdsRef.current.box,
        points_include: includePoints,
        points_exclude: excludePoints,
      };
      apiUrl = `${REACT_APP_SEGMENT_POINT_PROMPT_API_URL}`;
    }else{
      alert('Unknown detection mode');
      return;
    }

    // Check if 30 seconds have passed since last request
    const now = Date.now();
    if (lastRequestBody && 
        JSON.stringify(requestBody) === JSON.stringify(lastRequestBody) &&
        lastRequestTime && 
        (now - lastRequestTime) < 30000) {
      console.log('Duplicate request within 30s, skipping...');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await axios.post(apiUrl, requestBody, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      if (response.status > 299) {
        throw new Error("Failed to get response from server");
      }
      // Update last request time
      setLastRequestTime(now);
      setLastRequestBody(requestBody);
      setGeoJsonData(response.data);
      setError(null);
      setActiveTab('results'); // Switch to results tab after detection
      
    } catch (error) {
      console.error('Error during detection:', error);
      let errorData = error.response?.data?.error;
      
      if (errorData) {
        if (typeof errorData === 'object') {
          setError(errorData);
          alert(`Error: ${errorData.message}`);
        } else {
          setError({ message: errorData });
          alert(`Error: ${errorData}`);
        }
      } else {
        setError({ message: error.message || 'Server error' });
        alert(error.message || 'Server error');
      }
      setLastRequestBody(null);
    } finally {
      setIsLoading(false);
    }
  }, [bbox, textPrompt, zoomLevel, isLoading, lastRequestBody, lastRequestTime, geoJsonData, detectionMode, includePoints, excludePoints]);

  const handleDownloadGeoJson = () => {
    if (geoJsonData) {
      const dataStr = JSON.stringify(geoJsonData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'detection_results.geojson';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const filterSmallAreas = useCallback((geoJsonData) => {
    if (!geoJsonData || !ignoreSmallAreas) return geoJsonData;

    const filtered = {
      ...geoJsonData,
      features: geoJsonData.features.filter(feature => {
        // Calculate area in square meters
        const coordinates = feature.geometry.coordinates[0];
        const area = calculatePolygonArea(coordinates);
        return area >= areaThreshold;
      })
    };

    return filtered;
  }, [ignoreSmallAreas, areaThreshold]);

  const calculatePolygonArea = (coordinates) => {
    let area = 0;
    for (let i = 0; i < coordinates.length - 1; i++) {
      const [x1, y1] = coordinates[i];
      const [x2, y2] = coordinates[i + 1];
      area += x1 * y2 - x2 * y1;
    }
    return Math.abs(area) / 2;
  };

  const handleClear = useCallback(() => {
    // Clear map layers
    const featureGroup = featureGroupRef.current;
    if (featureGroup) {
      featureGroup.clearLayers();
    }
    
    // Clear state values
    setTextPrompt('');
    setBbox(null);
    setLastRequestBody(null);
    setIncludePoints([]);
    setExcludePoints([]);
    setDrawingMode(null);
    setGeoJsonData(null);  // Clear detection results
    
    // Reset thresholds to default if needed
    if (detectionMode === 'text') {
      setBoxThreshold(0.24);
      setTextThreshold(0.24);
    } else {
      setInteractiveBoxThreshold(0.24);
    }
  }, [detectionMode]);

  // Add this after points are added to visualize them
  useEffect(() => {
    if (featureGroupRef.current) {
      // Clear existing points
      featureGroupRef.current.clearLayers();
      
      // Add include points
      includePoints.forEach(point => {
        const marker = L.marker([point[1], point[0]], {
          icon: includePointIcon
        });
        featureGroupRef.current.addLayer(marker);
      });
      
      // Add exclude points
      excludePoints.forEach(point => {
        const marker = L.marker([point[1], point[0]], {
          icon: excludePointIcon
        });
        featureGroupRef.current.addLayer(marker);
      });
    }
  }, [includePoints, excludePoints]);

  // Map events handler
  const MapEventsHandler = () => {
    const map = useMapEvents({
      mousedown: (e) => {
        if (drawingMode === 'rectangle') {
          // Clear existing rectangle
          if (featureGroupRef.current) {
            featureGroupRef.current.clearLayers();
          }
          
          isDrawingRef.current = true;
          startPointRef.current = e.latlng;
          
          const bounds = L.latLngBounds(e.latlng, e.latlng);
          rectangleRef.current = L.rectangle(bounds, {
            color: '#0000ff',
            weight: 2
          }).addTo(featureGroupRef.current);
          
          // Disable map dragging while drawing
          map.dragging.disable();
        }
      },
      mousemove: (e) => {
        if (isDrawingRef.current && rectangleRef.current) {
          const bounds = L.latLngBounds(startPointRef.current, e.latlng);
          rectangleRef.current.setBounds(bounds);
        }
      },
      mouseup: (e) => {
        if (isDrawingRef.current && rectangleRef.current) {
          const bounds = L.latLngBounds(startPointRef.current, e.latlng);
          setBbox([
            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth()
          ]);
          isDrawingRef.current = false;
          startPointRef.current = null;
          
          // Re-enable map dragging
          map.dragging.enable();
        }
      },
      click: (e) => {
        if (drawingMode === 'delete') {
          // Find the nearest marker at click position
          const clickPoint = e.latlng;
          const layers = featureGroupRef.current.getLayers();
          
          for (let layer of layers) {
            if (layer instanceof L.Marker) {
              const markerPoint = layer.getLatLng();
              // If click position is within 20 pixels of the marker
              if (map.latLngToLayerPoint(clickPoint).distanceTo(map.latLngToLayerPoint(markerPoint)) < 20) {
                // Remove marker
                featureGroupRef.current.removeLayer(layer);
                // Remove point from state
                const point = [markerPoint.lng, markerPoint.lat];
                setIncludePoints(prev => prev.filter(p => p[0] !== point[0] || p[1] !== point[1]));
                setExcludePoints(prev => prev.filter(p => p[0] !== point[0] || p[1] !== point[1]));
                break;
              }
            }
          }
        } else if (drawingMode === 'include') {
          const marker = L.marker(e.latlng, { icon: includePointIcon })
            .addTo(featureGroupRef.current);
          setIncludePoints(prev => [...prev, [e.latlng.lng, e.latlng.lat]]);
          
          // Add click handler for point deletion
          marker.on('click', () => {
            if (drawingMode === null) {
              featureGroupRef.current.removeLayer(marker);
              setIncludePoints(prev => 
                prev.filter(p => p[0] !== e.latlng.lng || p[1] !== e.latlng.lat)
              );
            }
          });
        } else if (drawingMode === 'exclude') {
          const marker = L.marker(e.latlng, { icon: excludePointIcon })
            .addTo(featureGroupRef.current);
          setExcludePoints(prev => [...prev, [e.latlng.lng, e.latlng.lat]]);
          
          // Add click handler for point deletion
          marker.on('click', () => {
            if (drawingMode === null) {
              featureGroupRef.current.removeLayer(marker);
              setExcludePoints(prev => 
                prev.filter(p => p[0] !== e.latlng.lng || p[1] !== e.latlng.lat)
              );
            }
          });
        }
      }
    });
    return null;
  };

  return (
    <div className="map-layout">
      <ControlPanel
        bbox={bbox}
        textPrompt={textPrompt}
        setTextPrompt={setTextPrompt}
        isLoading={isLoading}
        handleDetect={handleDetect}
        zoomLevel={zoomLevel}
        setZoomLevel={setZoomLevel}
        geoJsonData={geoJsonData}
        handleDownloadGeoJson={handleDownloadGeoJson}
        lastRequestBody={lastRequestBody}
        detectionMode={detectionMode}
        onDetectionModeChange={handleDetectionModeChange}
        interactiveBoxThreshold={interactiveBoxThreshold}
        setInteractiveBoxThreshold={setInteractiveBoxThreshold}
        box_threshold={box_threshold}
        setBoxThreshold={setBoxThreshold}
        text_threshold={text_threshold}
        setTextThreshold={setTextThreshold}
        handleClear={handleClear}
        error={error}
        drawingMode={drawingMode}
        setDrawingMode={setDrawingMode}
        includePoints={includePoints}
      >
      </ControlPanel>

      <div className="map-container">
        <MapContainer
          center={center || [32.77058258620389, -96.79199913948932]}
          zoom={zoom || 18}
          style={{ height: "100vh", width: "100%" }}
        >
          <LayersControl position="topright">
            <BaseLayer checked name="ESRI Satellite">
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                maxZoom={20}
                attribution='&copy; <a href="https://www.esri.com/en-us/home">Esri</a>'
              />
            </BaseLayer>
            <BaseLayer name="ESRI Topographic">
              <TileLayer
                url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
                maxZoom={20}
                attribution='&copy; <a href="https://www.esri.com/en-us/home">Esri</a>'
              />
            </BaseLayer>
            <BaseLayer name="Google Satellite">
              <TileLayer
                url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                maxZoom={20}
                attribution="Google Satellite"
              />
            </BaseLayer>
            <BaseLayer name="OpenStreetMap">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                maxZoom={20}
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
            </BaseLayer>
          </LayersControl>

          <FeatureGroup ref={featureGroupRef}>
            <MapEventsHandler />
          </FeatureGroup>
          
          <MapController 
            geoJsonData={geoJsonData} 
            uploadedGeojson={uploadedGeojson}
            setGeoJsonLayer={geoJsonLayerRef}
          />
          <SearchControl />
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent; 