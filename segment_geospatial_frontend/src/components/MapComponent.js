import React, { useState, useRef } from 'react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { Tab, Tabs, TextField, Button, Box, Typography, Paper } from '@mui/material';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import './MapComponent.css';

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

const MapComponent = () => {
  const [tabValue, setTabValue] = useState(0);
  const [textPrompt, setTextPrompt] = useState('');
  const [zoomLevel, setZoomLevel] = useState(18);
  const [bbox, setBbox] = useState(null);
  const featureGroupRef = useRef();

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

    try {
      const response = await axios.post('http://localhost:8000/predict', {
        bbox: bbox,
        text_prompt: textPrompt,
        zoom_level: zoomLevel
      });
      
      // Switch to results tab after successful detection
      setTabValue(1);
      console.log(response.data);
    } catch (error) {
      console.error('Error during detection:', error);
      alert('Error during detection. Please try again.');
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
                disabled={!bbox || !textPrompt}
                size="small"
              >
                Detect Objects
              </Button>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="body2">Detection results will appear here</Typography>
          </TabPanel>
        </div>
      </Paper>

      <div className="map-container">
        <MapContainer
          center={[32.77058258620389, -96.79199913948932]}
          zoom={zoomLevel}
          style={{ height: "100vh", width: "100%" }}
        >
          <TileLayer
            url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
            attribution="Google Satellite"
          />
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
        </MapContainer>
      </div>
    </div>
  );
};

export default MapComponent; 