import React, { useState, useEffect } from 'react';
import {
  TextField,
  Button,
  Box,
  Typography,
  Paper,
  CircularProgress,
  Tabs,
  Tab,
  ToggleButton
} from '@mui/material';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import DownloadIcon from '@mui/icons-material/Download';
import RectangleIcon from '@mui/icons-material/Rectangle';
import AddLocationIcon from '@mui/icons-material/AddLocation';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

const ControlPanel = ({
  bbox,
  textPrompt,
  setTextPrompt,
  isLoading,
  handleDetect,
  zoomLevel,
  setZoomLevel,
  geoJsonData,
  handleDownloadGeoJson,
  detectionMode,
  onDetectionModeChange,
  interactiveBoxThreshold,
  setInteractiveBoxThreshold,
  box_threshold,
  setBoxThreshold,
  text_threshold,
  setTextThreshold,
  handleClear,
  drawingMode,
  setDrawingMode,
  includePoints
}) => {
  const [tabValue, setTabValue] = useState('1');

  useEffect(() => {
    if (geoJsonData) {
      setTabValue('2');
    }
  }, [geoJsonData]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{
      position: 'absolute',
      bottom: 50,
      left: 10,
      zIndex: 1000,
      backgroundColor: 'white',
      borderRadius: 1,
      boxShadow: 1,
      padding: 2,
      width: '500px'
    }}>
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <TabList
            onChange={handleTabChange}
            aria-label="map tabs"
            variant="fullWidth"
          >
            <Tab label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <span>Detection</span>
                {geoJsonData && <CheckCircleIcon sx={{ ml: 1, fontSize: 16, color: 'success.main' }} />}
              </Box>
            } value="1" />
            <Tab label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <span>Results</span>
                {geoJsonData && 
                  <Typography variant="caption" sx={{ ml: 1 }}>
                    ({geoJsonData.features?.length || 0})
                  </Typography>
                }
              </Box>
            } value="2" />
            <Tab label="Instructions" value="3" />
          </TabList>
        </Box>

        <TabPanel value="1" sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              select
              label="Zoom Level of the image for detection"
              value={zoomLevel}
              onChange={(e) => setZoomLevel(Number(e.target.value))}
              SelectProps={{
                native: true,
              }}
              size="small"
              disabled={isLoading}
            >
              {[19, 20, 21, 22].map((zoom) => (
                <option key={zoom} value={zoom}>
                  {zoom}
                </option>
              ))}
            </TextField>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs
                value={detectionMode}
                onChange={onDetectionModeChange}
                variant="fullWidth"
              >
                <Tab value="text" label="Text-based" />
                <Tab value="interactive" label="Interactive" />
              </Tabs>
            </Box>

            {detectionMode === 'text' ? (
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

                <Typography>Box Threshold: {box_threshold}</Typography>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={box_threshold}
                  onChange={(e) => setBoxThreshold(parseFloat(e.target.value))}
                />

                <Typography>Text Threshold: {text_threshold}</Typography>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={text_threshold}
                  onChange={(e) => setTextThreshold(parseFloat(e.target.value))}
                />

                <ToggleButton
                  value="rectangle"
                  selected={drawingMode === 'rectangle'}
                  onChange={() => {
                    setDrawingMode(drawingMode === 'rectangle' ? null : 'rectangle');
                  }}
                  sx={{ width: '100%' }}
                >
                  <RectangleIcon sx={{ mr: 1 }} />
                  {drawingMode === 'rectangle' ? 'Click and drag to draw' : 'Draw a rectangle to start'}
                </ToggleButton>

              </Box>
            ) : (
              <Box  sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <div>Add control points to detect objects:</div>

                <div className="input-group">
                  <label>Box Threshold: {interactiveBoxThreshold}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={interactiveBoxThreshold}
                    onChange={(e) => setInteractiveBoxThreshold(parseFloat(e.target.value))}
                  />
                </div>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <ToggleButton
                    value="include"
                    selected={drawingMode === 'include'}
                    onChange={() => {
                      setDrawingMode(drawingMode === 'include' ? null : 'include');
                    }}
                    color="success"
                  >
                    <AddLocationIcon />
                  </ToggleButton>

                  <ToggleButton
                    value="exclude"
                    selected={drawingMode === 'exclude'}
                    onChange={() => {
                      setDrawingMode(drawingMode === 'exclude' ? null : 'exclude');
                    }}
                    color="error"
                  >
                    <RemoveCircleIcon />
                  </ToggleButton>
                </Box>
                <Typography variant="caption" sx={{ ml: 1 }}>
                  {drawingMode === 'include' ? 'Click to add points' :
                    drawingMode === 'exclude' ? 'Click to add exclude points' :
                      'Select a point type'}
                </Typography>
                <ToggleButton value="delete"
                  selected={drawingMode === 'delete'}
                  onChange={() => {
                    setDrawingMode(drawingMode === 'delete' ? null : 'delete');
                  }}
                >
                  <DeleteIcon />
                </ToggleButton>
              </Box>
            )}
            <Button
              variant="contained"
              onClick={handleDetect}
              disabled={
                (detectionMode === 'text' && (!bbox || !textPrompt)) || 
                (detectionMode === 'interactive' && includePoints.length === 0) || 
                isLoading
              }
              size="small"
              startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : null}
            >
              {isLoading ? 'Detecting...' : 'Detect Objects'}
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              onClick={handleClear}
              size="small"
            >
              Clear
            </Button>

          </Box>
        </TabPanel>

        <TabPanel value="2" sx={{ p: 2 }}>
          {geoJsonData ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="body2" gutterBottom>
                Detection results displayed on map
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {geoJsonData.features?.length || 0} objects found
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={handleDownloadGeoJson}
                startIcon={<DownloadIcon />}
                fullWidth
              >
                Download GeoJSON
              </Button>
              <Button
                variant="outlined"
                color="primary"
                onClick={() => setTabValue('1')}
                startIcon={<ArrowBackIcon />}
                fullWidth
              >
                Back to Detection
              </Button>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center' }}>
              <Typography variant="body2">No detection results yet</Typography>
              <Button
                variant="outlined"
                color="primary"
                onClick={() => setTabValue('1')}
                startIcon={<ArrowBackIcon />}
                fullWidth
              >
                Back to Detection
              </Button>
            </Box>
          )}
        </TabPanel>

        <TabPanel value="3" sx={{ p: 2 }}>
        <div className="instruction-panel">
      <h3>Instructions</h3>
      {detectionMode === 'text' ? (
        <div>
          <h4>Text-based Detection Mode:</h4>
          <ol>
            <li>Click "Draw Rectangle" button to enable drawing</li>
            <li>Draw a rectangle on the map by clicking and dragging</li>
            <li>Enter text description of objects to detect</li>
            <li>Adjust detection thresholds if needed</li>
            <li>Click "Detect" to start detection</li>
          </ol>
        </div>
      ) : (
        <div>
          <h4>Interactive Detection Mode:</h4>
          <ol>
            <li>Click "Add Include Points" to mark target objects (green)</li>
            <li>Click "Add Exclude Points" to mark non-target areas (red)</li>
            <li>Click points on map to add markers</li>
            <li>Use "Delete Points" to remove markers if needed</li>
            <li>Click "Detect" when ready</li>
          </ol>
        </div>
      )}
      
      <h4>Results:</h4>
      <ol>
        <li>Detection results will appear on the map</li>
        <li>Use "Download GeoJSON" to save results</li>
        <li>Click "Clear" to reset and start over</li>
      </ol>
      
      <h4>Tips:</h4>
      <ul>
        <li>Higher thresholds = more precise but fewer results</li>
        <li>Lower thresholds = more results but may include false positives</li>
        <li>Use the layer control to switch map backgrounds</li>
      </ul>
    </div>
        </TabPanel>
      </TabContext>
    </Box>
  );
};

export default ControlPanel; 