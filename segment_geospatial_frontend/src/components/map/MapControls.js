import React from 'react';
import './MapControls.css';

const MapControls = ({ fileInputRef, handleFileUpload, uploadedGeojson, handleClearUpload }) => {
  return (
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
  );
};

export default MapControls; 