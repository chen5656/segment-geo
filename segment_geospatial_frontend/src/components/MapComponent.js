import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, FeatureGroup, useMap, LayersControl } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { Tab, Tabs, TextField, Button, Box, Typography, Paper, CircularProgress, Autocomplete, InputAdornment, IconButton } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapComponent.css';
import axios from 'axios';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import debounce from 'lodash/debounce';
const { BaseLayer } = LayersControl;

// TabPanel component for MUI tabs
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Create a component to handle map interactions
function MapController({ geoJsonData, uploadedGeojson, setGeoJsonLayer, pointPosition }) {
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
}

// Update the SearchControl component
function SearchControl() {
  const map = useMap();
  const [searchValue, setSearchValue] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const MAPBOX_TOKEN = 'pk.eyJ1IjoiaHVhanVuMTExMSIsImEiOiJjbTZjbnh5dDUwYXdsMmxvajhjbWxkeHI3In0.3qeLn9-pd0Dk2aam30rvbg';

  const searchAddress = async (query) => {
    if (!query) return;
    
    setLoading(true);
    try {
      const response = await axios.get(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json`,
        {
          params: {
            access_token: MAPBOX_TOKEN,
            limit: 5,
            types: 'address,place,locality,neighborhood'
          }
        }
      );
      
      const locations = response.data.features.map(feature => ({
        label: feature.place_name,
        lat: feature.center[1],
        lon: feature.center[0]
      }));
      
      setOptions(locations);
    } catch (error) {
      console.error('Error searching address:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event, newValue) => {
    if (newValue && newValue.lat && newValue.lon) {
      map.setView([newValue.lat, newValue.lon], 18);
    }
  };

  // Debounce the search to avoid too many API calls
  const debouncedSearch = useCallback(
    debounce((query) => {
      if (query.length > 2) {
        searchAddress(query);
      }
    }, 300),
    []
  );

  return (
    <div className="search-control">
      <Autocomplete
        freeSolo
        options={options}
        loading={loading}
        getOptionLabel={(option) => option.label || ''}
        onInputChange={(event, newValue) => {
          setSearchValue(newValue);
          debouncedSearch(newValue);
        }}
        onChange={handleSearch}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            placeholder="Search location..."
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <InputAdornment position="end">
                  {loading ? (
                    <CircularProgress size={20} />
                  ) : (
                    <IconButton 
                      size="small"
                      onClick={() => searchAddress(searchValue)}
                    >
                      <SearchIcon />
                    </IconButton>
                  )}
                </InputAdornment>
              )
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                searchAddress(searchValue);
              }
            }}
          />
        )}
      />
    </div>
  );
}

const MapComponent = ({ center, zoom, predictions, onMapClick, onFileUpload }) => {
  const [tabValue, setTabValue] = useState(0);
  const [textPrompt, setTextPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const featureGroupRef = useRef();
  const geoJsonLayerRef = useRef(null);
  const [pointPosition, setPointPosition] = useState('bottom-right');
  const [showRequestBody, setShowRequestBody] = useState(false);
  const [lastRequestBody, setLastRequestBody] = useState(null);
  const fileInputRef = useRef(null);
  const [bbox, setBbox] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(zoom || 13);
  const [uploadedGeojson, setUploadedGeojson] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDrawStart = () => {
    // Clear previous drawings when starting to draw
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
      zoom_level: zoomLevel
    };

    setLastRequestBody(requestBody);
    setIsLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8001/api/v1/predict', requestBody, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setGeoJsonData(response.data.geojson);
      setTabValue(1);
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
          // Validate GeoJSON format
          if (geojsonData.type !== 'FeatureCollection') {
            alert('Invalid GeoJSON format: Must be a FeatureCollection');
            return;
          }
          setUploadedGeojson(geojsonData);
          onFileUpload(geojsonData); // Call parent handler if needed
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

  // Add clear function for uploaded data
  const handleClearUpload = () => {
    setUploadedGeojson(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="map-layout"> 
    
      <Paper className="sidebar">
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          orientation="vertical"
          sx={{ borderRight: 1, borderColor: 'divider' }}
        >
          <Tab label="Detection Settings" />
          <Tab label="Results" />
        </Tabs>

        <div className="tab-panels">
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>

              <TextField
                select
                label="Point Position"
                value={pointPosition}
                onChange={(e) => setPointPosition(e.target.value)}
                size="small"
                fullWidth
              >
                <option value="top-right">Top Right</option>
                <option value="top-left">Top Left</option>
                <option value="bottom-right">Bottom Right</option>
                <option value="bottom-left">Bottom Left</option>
              </TextField>
              <TextField
                label="What do you want to detect?"
                placeholder="e.g., poles, trees, buildings"
                value={textPrompt}
                onChange={(e) => setTextPrompt(e.target.value)}
                fullWidth
                size="small"
                disabled={isLoading}
              />
              
              <TextField
                select
                label="Zoom Level"
                value={zoomLevel}
                onChange={(e) => setZoomLevel(Number(e.target.value))}
                SelectProps={{
                  native: true,
                }}
                size="small"
                disabled={isLoading}
              >
                {[15, 16, 17, 18, 19].map((zoom) => (
                  <option key={zoom} value={zoom}>
                    {zoom}
                  </option>
                ))}
              </TextField>

              <Button 
                variant="contained" 
                onClick={handleDetect}
                disabled={!bbox || !textPrompt || isLoading}
                size="small"
                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
              >
                {isLoading ? 'Detecting...' : 'Detect Objects'}
              </Button>

              {lastRequestBody && (
                <>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setShowRequestBody(!showRequestBody)}
                    startIcon={showRequestBody ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  >
                    {showRequestBody ? 'Hide Request' : 'Show Request'}
                  </Button>

                  {showRequestBody && (
                    <Paper 
                      elevation={0} 
                      variant="outlined"
                      sx={{ 
                        p: 1,
                        backgroundColor: '#f5f5f5',
                        maxHeight: '200px',
                        overflow: 'auto'
                      }}
                    >
                      <Typography variant="caption" component="pre" sx={{ margin: 0 }}>
                        {JSON.stringify(lastRequestBody, null, 2)}
                      </Typography>
                    </Paper>
                  )}
                </>
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {geoJsonData ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Detection results displayed on map
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {geoJsonData.features?.length || 0} objects found
                </Typography>
                <TextField
                  select
                  label="Point Position"
                  value={pointPosition}
                  onChange={(e) => setPointPosition(e.target.value)}
                  size="small"
                  fullWidth
                >
                  <option value="top-right">Top Right</option>
                  <option value="top-left">Top Left</option>
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                </TextField>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleDownloadGeoJson}
                  startIcon={<DownloadIcon />}
                  fullWidth
                >
                  Download GeoJSON
                </Button>
              </Box>
            ) : (
              <Typography variant="body2">No detection results yet</Typography>
            )}
          </TabPanel>
        </div>
      </Paper>

      <div className="map-container">
        <div className="map-controls">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".geojson,.json"
            style={{ display: 'none' }}
          />
          <div className="upload-controls">
            <button 
              className="upload-btn"
              onClick={() => fileInputRef.current.click()}
            >
              Upload GeoJSON
            </button>
            {uploadedGeojson && (
              <button 
                className="clear-btn"
                onClick={handleClearUpload}
              >
                Clear Upload
              </button>
            )}
          </div>
        </div>
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