import React, { useState, useRef } from 'react';
import { MapContainer, TileLayer, FeatureGroup, LayersControl } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapComponent.css';

import ControlPanel from './map/ControlPanel';
import MapControls from './map/MapControls';
import SearchControl from './map/SearchControl';
import MapController from './map/MapController';

const { BaseLayer } = LayersControl;

const MapComponent = ({ center, zoom }) => {
  const [textPrompt, setTextPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const featureGroupRef = useRef();
  const geoJsonLayerRef = useRef(null);
  const [pointPosition, setPointPosition] = useState('bottom-right');
  const [lastRequestBody, setLastRequestBody] = useState(null);
  const fileInputRef = useRef(null);
  const [bbox, setBbox] = useState(null);
  const [box_threshold, setBoxThreshold] = useState(0.24);
  const [text_threshold, setTextThreshold] = useState(0.24);
  const [zoomLevel, setZoomLevel] = useState(zoom || 13);
  const [uploadedGeojson, setUploadedGeojson] = useState(null);

  const handleDrawStart = () => {
    const featureGroup = featureGroupRef.current;
    if (featureGroup) {
      featureGroup.clearLayers();
    }
  };

  const handleDrawCreated = (e) => {
    const layer = e.layer;
    const featureGroup = featureGroupRef.current;
    if (featureGroup) {
      featureGroup.addLayer(layer);
    }
    
    const bounds = layer.getBounds();
    setBbox([
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth()
    ]);
  };

  const handleDrawDeleted = () => {
    setBbox(null);
  };

  const handleDetect = async () => {
    if (!bbox || !textPrompt) {
      alert('Please draw a rectangle and enter detection parameters');
      return;
    }

    const requestBody = {
      bounding_box: bbox,
      text_prompt: textPrompt,
      zoom_level: zoomLevel,
      box_threshold: box_threshold,
      text_threshold: text_threshold,
    };

    setLastRequestBody(requestBody);
    setIsLoading(true);
    
    try {
      const response = await axios.post(process.env.PREDICT_API_URL + '/predict', requestBody, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setGeoJsonData(response.data.geojson);
      console.log(response.data);
    } catch (error) {
      console.error('Error during detection:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Server error';
      alert(`Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

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

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const geojsonData = JSON.parse(e.target.result);
          if (geojsonData.type !== 'FeatureCollection') {
            alert('Invalid GeoJSON format: Must be a FeatureCollection');
            return;
          }
          setUploadedGeojson(geojsonData);
        } catch (error) {
          console.error('Error parsing GeoJSON:', error);
          alert('Invalid GeoJSON file');
        }
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file');
    }
  };

  const handleClearUpload = () => {
    setUploadedGeojson(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="map-layout">
      <ControlPanel
        bbox={bbox}
        textPrompt={textPrompt}
        setTextPrompt={setTextPrompt}
        isLoading={isLoading}
        handleDetect={handleDetect}
        pointPosition={pointPosition}
        setPointPosition={setPointPosition}
        zoomLevel={zoomLevel}
        setZoomLevel={setZoomLevel}
        geoJsonData={geoJsonData}
        handleDownloadGeoJson={handleDownloadGeoJson}
        lastRequestBody={lastRequestBody}
      />

      <div className="map-container">
        <MapControls
          fileInputRef={fileInputRef}
          handleFileUpload={handleFileUpload}
          uploadedGeojson={uploadedGeojson}
          handleClearUpload={handleClearUpload}
        />
        
        <MapContainer
          center={center || [32.77058258620389, -96.79199913948932]}
          zoom={zoomLevel}
          style={{ height: "100vh", width: "100%" }}
        >
          <LayersControl position="topright">
            <BaseLayer checked name="ESRI Satellite">
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                maxZoom={19}
                attribution='&copy; <a href="https://www.esri.com/en-us/home">Esri</a>'
              />
            </BaseLayer>
            <BaseLayer name="ESRI Topographic">
              <TileLayer
                url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
                maxZoom={19}
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
                maxZoom={19}
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
            </BaseLayer>
          </LayersControl>
          
          <FeatureGroup ref={featureGroupRef}>
            <EditControl
              position="topright"
              onCreated={handleDrawCreated}
              onDeleted={handleDrawDeleted}
              onDrawStart={handleDrawStart}
              draw={{
                rectangle: true,
                polygon: false,
                circle: false,
                circlemarker: false,
                marker: false,
                polyline: false,
              }}
              edit={{
                edit: false,
                remove: true
              }}
            />
          </FeatureGroup>
          
          <MapController 
            geoJsonData={geoJsonData} 
            uploadedGeojson={uploadedGeojson}
            setGeoJsonLayer={geoJsonLayerRef}
            pointPosition={pointPosition}
          />
          <SearchControl />
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent; 