import React, { useState } from 'react';
import MapComponent from './components/MapComponent';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'light',
  },
});

function App() {
  const [predictions, setPredictions] = useState([]);
  const [uploadedGeojson, setUploadedGeojson] = useState(null);
  
  const handlePredict = (event) => {
    // Implementation of handlePredict function
  };

  const handleFileUpload = (geojsonData) => {
    // Validate that it's a FeatureCollection
    if (geojsonData.type !== 'FeatureCollection') {
      alert('Invalid GeoJSON format: Must be a FeatureCollection');
      return;
    }

    setUploadedGeojson(geojsonData);
    // If the GeoJSON has features, we can also add them to predictions
    if (geojsonData.features && geojsonData.features.length > 0) {
      setPredictions(geojsonData.features);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <header className="App-header">
          <h1>Tree Detection</h1>
        </header>
        <main>
          <MapComponent
            center={[32.7767, -96.7970]}
            zoom={13}
            predictions={predictions}
            onMapClick={handlePredict}
            onFileUpload={handleFileUpload}
          />
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App; 