import React, { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, FeatureGroup, useMap, LayersControl } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { Tab, Tabs, TextField, Button, Box, Typography, Paper, CircularProgress, Autocomplete, InputAdornment, IconButton } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapComponent.css';
import axios from 'axios';
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
function MapController({ geoJsonData, setGeoJsonLayer }) {
  const map = useMap();
  
  useEffect(() => {
    if (geoJsonData) {
      // Remove existing layer if it exists
      if (setGeoJsonLayer.current) {
        setGeoJsonLayer.current.remove();
      }

      // Create new layer
      const layer = L.geoJSON(geoJsonData, {
        style: {
          color: '#ff0000',
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.4
        }
      }).addTo(map);

      // Store reference to layer
      setGeoJsonLayer.current = layer;

      // Fit map bounds to the new layer
      map.fitBounds(layer.getBounds());
    }
  }, [geoJsonData, map]);

  return null;
}

// Add new SearchControl component
function SearchControl() {
  const map = useMap();
  const [searchValue, setSearchValue] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchAddress = async (query) => {
    if (!query) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`https://nominatim.openstreetmap.org/search`, {
        params: {
          q: query,
          format: 'json',
          limit: 5
        }
      });
      
      const locations = response.data.map(item => ({
        label: item.display_name,
        lat: parseFloat(item.lat),
        lon: parseFloat(item.lon)
      }));
      
      setOptions(locations);
    } catch (error) {
      console.error('Error searching address:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event, newValue) => {
    if (newValue && newValue.lat && newValue.lon) {
      map.setView([newValue.lat, newValue.lon], 18);
    }
  };

  return (
    <div className="search-control">
      <Autocomplete
        freeSolo
        options={options}
        loading={loading}
        getOptionLabel={(option) => option.label || ''}
        onInputChange={(event, newValue) => {
          setSearchValue(newValue);
          if (newValue.length > 3) {
            searchAddress(newValue);
          }
        }}
        onChange={handleSearch}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            placeholder="Search address..."
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

const MapComponent = () => {
  const [tabValue, setTabValue] = useState(0);
  const [textPrompt, setTextPrompt] = useState('');
  const [zoomLevel, setZoomLevel] = useState(18);
  const [bbox, setBbox] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [geoJsonData, setGeoJsonData] = useState(null);
  const featureGroupRef = useRef();
  const geoJsonLayerRef = useRef(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDrawStart = () => {
    // Clear previous drawings when starting to draw
    const featureGroup = featureGroupRef.current;
    if (featureGroup) {
      featureGroup.clearLayers();
      setBbox(null);
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

    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:8001/api/v1/predict', {
        bounding_box: bbox,
        text_prompt: textPrompt,
        zoom_level: zoomLevel
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setGeoJsonData(response.data.geojson);
      // Switch to results tab after successful detection
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
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {geoJsonData ? (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Detection results displayed on map
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {geoJsonData.features?.length || 0} objects found
                </Typography>
              </Box>
            ) : (
              <Typography variant="body2">No detection results yet</Typography>
            )}
          </TabPanel>
        </div>
      </Paper>

      <div className="map-container">
        <MapContainer
          center={[32.77058258620389, -96.79199913948932]}
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
          <MapController geoJsonData={geoJsonData} setGeoJsonLayer={geoJsonLayerRef} />
          <SearchControl />
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent; 