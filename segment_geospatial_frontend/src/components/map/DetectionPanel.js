import React from 'react';
import { TextField, Button, Box, CircularProgress } from '@mui/material';

function DetectionPanel({ 
  pointPosition, 
  setPointPosition, 
  textPrompt, 
  setTextPrompt,
  zoomLevel,
  setZoomLevel,
  isLoading,
  bbox,
  handleDetect,
  showRequestBody,
  lastRequestBody,
  setShowRequestBody
}) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* ... existing detection panel content ... */}
    </Box>
  );
}

export default DetectionPanel; 