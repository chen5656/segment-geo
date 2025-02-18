import React from 'react';
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

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <main>
          <MapComponent
            center={[32.7767, -96.7970]}
            zoom={18}
          />
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App; 