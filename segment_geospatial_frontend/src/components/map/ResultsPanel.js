import React from 'react';
import { Box, Typography, TextField, Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

function ResultsPanel({ 
  geoJsonData, 
  pointPosition, 
  setPointPosition, 
  handleDownloadGeoJson 
}) {
  return (
    geoJsonData ? (
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
    )
  );
}

export default ResultsPanel; 