import React, { useState } from 'react';
import { Tab, TextField, Button, Box, Typography, Paper, CircularProgress } from '@mui/material';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import DownloadIcon from '@mui/icons-material/Download';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

const ControlPanel = ({ 
  bbox,
  textPrompt,
  setTextPrompt,
  isLoading,
  handleDetect,
  pointPosition,
  setPointPosition,
  zoomLevel,
  setZoomLevel,
  geoJsonData,
  handleDownloadGeoJson,
  lastRequestBody
}) => {
  const [tabValue, setTabValue] = useState('1');
  const [showRequestBody, setShowRequestBody] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ width: '30%', typography: 'body1' }}>
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <TabList onChange={handleTabChange} aria-label="map tabs">
            <Tab label="Detection" value="1" />
            <Tab label="Results" value="2" />
            <Tab label="Instructions" value="3" />
          </TabList>
        </Box>
        <TabPanel value="1">
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              select
              disabled 
              label="Point Position"
              value={pointPosition}
              onChange={(e) => setPointPosition(e.target.value)}
              size="small"
              fullWidth
            >
              <option value="top-right">Top Right</option>
              <option value="top-left">Top Left</option>
              <option value="top-left">Center</option>
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
            <div> <ArrowForwardIcon />  Draw a rectangle to start</div>
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
        <TabPanel value="2">
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
        <TabPanel value="3">
          <Typography variant="body2">
            Instructions for using the map will go here
          </Typography>
        </TabPanel>
      </TabContext>
    </Box>
  );
};

export default ControlPanel; 