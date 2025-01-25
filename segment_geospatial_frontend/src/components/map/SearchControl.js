import React, { useState, useCallback } from 'react';
import { useMap } from 'react-leaflet';
import { TextField, CircularProgress, InputAdornment, IconButton, Autocomplete } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';
import debounce from 'lodash/debounce';

if (!process.env.REACT_APP_MAPBOX_TOKEN) {
  console.warn('Mapbox token is not set in environment variables. Search functionality will not work.');
}

function SearchControl() {
  const map = useMap();
  const [searchValue, setSearchValue] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const searchAddress = async (query) => {
    if (!query) return;
    
    setLoading(true);
    try {
      const response = await axios.get(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json`,
        {
          params: {
            access_token: process.env.REACT_APP_MAPBOX_TOKEN,
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

export default SearchControl; 