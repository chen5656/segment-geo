/**
 * Converts an Esri Extent object to a bounding box array
 * @param {Object} extent - Esri Extent object containing xmin, ymin, xmax, ymax
 * @returns {Array} Bounding box array in [west, south, east, north] format
 */
function extentToBoundingBox(extent) {
  // Input validation
  if (!extent || typeof extent !== 'object') {
    throw new Error('Invalid extent object');
  }

  // Check if required properties exist
  if (!('xmin' in extent) || !('ymin' in extent) ||
    !('xmax' in extent) || !('ymax' in extent)) {
    throw new Error('Extent object missing required properties');
  }

  // Convert to bounding box format [west, south, east, north]
  return [
    extent.xmin,  // west
    extent.ymin,  // south
    extent.xmax,  // east
    extent.ymax   // north
  ];
}

/**
 * Converts Web Mercator coordinates to Geographic coordinates (lat/long)
 * @param {number} x - Web Mercator X coordinate
 * @param {number} y - Web Mercator Y coordinate
 * @returns {Array} Array containing [longitude, latitude]
 */
function webMercatorToGeographic(x, y) {
  // Earth's radius in meters
  const EARTH_RADIUS = 6378137;

  // Convert X coordinate to longitude
  const longitude = (x / EARTH_RADIUS) * (180 / Math.PI);

  // Convert Y coordinate to latitude
  const latitude = (Math.PI / 2 - 2 * Math.atan(Math.exp(-y / EARTH_RADIUS))) * (180 / Math.PI);

  return [longitude, latitude];
}

/**
* Converts Web Mercator bounding box to Geographic bounding box
* @param {Array} bbox - Bounding box in Web Mercator [west, south, east, north]
* @returns {Array} Bounding box in Geographic coordinates [west, south, east, north]
*/
function convertBoundingBoxToGeographic(bbox) {
  // Convert southwest corner
  const [westLong, southLat] = webMercatorToGeographic(bbox[0], bbox[1]);

  // Convert northeast corner
  const [eastLong, northLat] = webMercatorToGeographic(bbox[2], bbox[3]);

  // Return in [west, south, east, north] format
  return [westLong, southLat, eastLong, northLat];
}

class ObjectDetectionPanel {
  constructor(view, detectionParameters, sendTextPredictRequest) {
    this.view = view;
    this.detectionParameters = detectionParameters;
    this.textPrompt = '';
    this.pointPosition = 'bottom-right';
    this.zoomLevel = 20;
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.opacity = 0.9;
    this.color = '#3333CC';
    this.geoJsonData = null;
    this.panelVisible = false;
    this.sendRequest = sendTextPredictRequest;
    this.displayMode = 'segments';
    this.editableLayer = null;
    this.init();
  }

  async init() {
    await this.createPanel();
    this.setupEventListeners();
  }
  async createPanel() {
    this.panel = document.createElement('div');
    this.panel.className = 'object-detection-panel';
    this.panel.style.display = 'none';
    try {
      // Get the current module's URL and construct the relative path
      const moduleURL = new URL('./ObjectDetectionPanel.html', import.meta.url);
      const response = await fetch(moduleURL);
      const html = await response.text();
      this.panel.innerHTML = html;

      // Add zoom level options after loading template
      const zoomSelect = this.panel.querySelector('#zoom-level');
      [19, 20, 21, 22].forEach(zoom => {
        const option = document.createElement('option');
        option.value = zoom;
        option.textContent = zoom;
        zoomSelect.appendChild(option);
      });

      document.body.appendChild(this.panel);
    } catch (error) {
      console.error('Failed to load panel template:', error);
      throw error; // Propagate error to init method
    }
  }
  setupEventListeners() {
    // Close button
    this.panel.querySelector('.close-btn').addEventListener('click', () => {
      this.hide();
    });

    // Text prompt input
    const textPromptInput = this.panel.querySelector('#text-prompt');
    textPromptInput.addEventListener('input', (e) => {
      this.textPrompt = e.target.value;
    });

    // Zoom level select
    const zoomLevelSelect = this.panel.querySelector('#zoom-level');
    zoomLevelSelect.value = this.zoomLevel;
    zoomLevelSelect.addEventListener('change', (e) => {
      this.zoomLevel = parseInt(e.target.value);
    });

    // Box threshold slider
    const boxThresholdInput = this.panel.querySelector('#box-threshold');
    const boxThresholdValue = this.panel.querySelector('#box-threshold-value');
    boxThresholdInput.addEventListener('input', (e) => {
      this.boxThreshold = parseFloat(e.target.value);
      boxThresholdValue.textContent = this.boxThreshold.toFixed(2);
    });

    // Text threshold slider
    const textThresholdInput = this.panel.querySelector('#text-threshold');
    const textThresholdValue = this.panel.querySelector('#text-threshold-value');
    textThresholdInput.addEventListener('input', (e) => {
      this.textThreshold = parseFloat(e.target.value);
      textThresholdValue.textContent = this.textThreshold.toFixed(2);
    });

    // Opacity slider
    const opacityInput = this.panel.querySelector('#opacity');
    const opacityValue = this.panel.querySelector('#opacity-value');
    opacityInput.addEventListener('input', (e) => {
      this.opacity = parseFloat(e.target.value);
      opacityValue.textContent = this.opacity.toFixed(1);
      if (this.geoJsonData) {
        this.updateGeoJsonStyle();
      }
    });

    // Color picker
    const colorPicker = this.panel.querySelector('#color-picker');
    colorPicker.addEventListener('input', (e) => {
      this.color = e.target.value;
      if (this.geoJsonData) {
        this.updateGeoJsonStyle();
      }
    });

    // Display mode radio buttons
    const displayModeInputs = this.panel.querySelectorAll('input[name="display-mode"]');
    displayModeInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        this.displayMode = e.target.value;
        if (this.geoJsonData) {
          this.updateDisplay();
        }
      });
    });

    // Reset button
    const resetButton = this.panel.querySelector('#reset-btn');
    resetButton.addEventListener('click', () => {
      this.resetSettings();
    });

    // Detect button
    const detectButton = this.panel.querySelector('#detect-btn');
    detectButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.handleDetect();
    });
  }

  show() {
    this.panel.style.display = 'block';
    this.panelVisible = true;
  }

  hide() {
    this.panel.style.display = 'none';
    this.panelVisible = false;
    this.detectionParameters.geometry = null;
    this.detectionParameters.textDetectionLayer.removeAll();
    document.querySelector('#toolButton').textContent = "Activate Object Detection Tool";
    document.querySelector('#sketch_container').innerHTML = '';
  }

  toggle() {
    if (this.panelVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  async handleDetect() {
    const bbox = this.detectionParameters?.geometry?.extent;
    if (!this.zoomLevel || !this.textPrompt || !bbox) {
      alert('Please draw a rectangle and enter detection parameters');
      return;
    }
    const detectButton = this.panel.querySelector('#detect-btn');
    try {
      detectButton.classList.add('loading');
      detectButton.disabled = true;

      const boundingBox = convertBoundingBoxToGeographic(extentToBoundingBox(bbox));
  
      const requestBody = {
        "bounding_box": boundingBox,
        "text_prompt": this.textPrompt,
        "zoom_level": this.zoomLevel,
        "box_threshold": this.boxThreshold,
        "text_threshold": this.textThreshold,
      };  
  
      await this.sendRequest(requestBody);
      
    } catch (error) {
      throw error;      
    } finally{
      detectButton.classList.remove('loading');
      detectButton.disabled = false;
    }
  }

  resetSettings() {
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.opacity = 0.9;
    this.color = '#3333CC';

    // Update UI elements
    this.panel.querySelector('#box-threshold').value = this.boxThreshold;
    this.panel.querySelector('#box-threshold-value').textContent = this.boxThreshold.toFixed(2);
    this.panel.querySelector('#text-threshold').value = this.textThreshold;
    this.panel.querySelector('#text-threshold-value').textContent = this.textThreshold.toFixed(2);
    this.panel.querySelector('#opacity').value = this.opacity;
    this.panel.querySelector('#opacity-value').textContent = this.opacity.toFixed(1);
    this.panel.querySelector('#color-picker').value = this.color;

    if (this.geoJsonData) {
      this.updateGeoJsonStyle();
    }
  }

  updateGeoJsonStyle() {
    if (!this.editableLayer) {
      return;
    }

    // Update the renderer of the feature layer
    this.editableLayer.renderer = {
      type: "simple",
      symbol: this.displayMode === 'segments' ? {
        type: "simple-fill",
        color: [
          parseInt(this.color.slice(1, 3), 16),
          parseInt(this.color.slice(3, 5), 16),
          parseInt(this.color.slice(5, 7), 16),
          this.opacity
        ],
        style: "solid",
        outline: {
          color: "white",
          width: 1
        }
      } : {
        type: "simple-marker",
        style: "circle",
        color: [
          parseInt(this.color.slice(1, 3), 16),
          parseInt(this.color.slice(3, 5), 16),
          parseInt(this.color.slice(5, 7), 16),
          this.opacity
        ],
        size: "12px",
        outline: {
          color: "white",
          width: 1
        }
      }
    };
  }

  updateDisplay() {
    if (!this.geoJsonData) return;
    
    const graphicsLayer = this.detectionParameters.textDetectionLayer;
    graphicsLayer.removeAll();

    // Create appropriate FeatureLayer based on display mode
    const featureLayer = new FeatureLayer({
      source: [], // Start with empty source
      title: "Detection Result",
      objectIdField: "objectid",
      fields: [
        {
          name: "objectid",
          type: "oid"
        },
        {
          name: "value",
          type: "string"
        }
      ],
      renderer: this.displayMode === 'segments' ? 
        // Polygon renderer
        {
          type: "simple",
          symbol: {
            type: "simple-fill",
            color: [
              parseInt(this.color.slice(1, 3), 16),
              parseInt(this.color.slice(3, 5), 16),
              parseInt(this.color.slice(5, 7), 16),
              this.opacity
            ],
            style: "solid",
            outline: {
              color: "white",
              width: 1
            }
          }
        } :
        // Point renderer
        {
          type: "simple",
          symbol: {
            type: "simple-marker",
            style: "circle",
            color: [
              parseInt(this.color.slice(1, 3), 16),
              parseInt(this.color.slice(3, 5), 16),
              parseInt(this.color.slice(5, 7), 16),
              this.opacity
            ],
            size: "12px",
            outline: {
              color: "white",
              width: 1
            }
          }
        },
      geometryType: this.displayMode === 'segments' ? "polygon" : "point",
      popupTemplate: {
        title: "{value}",
        content: this.displayMode === 'segments' ? 
          "Polygon Area: {value}" : 
          "Point Location: {value}"
      }
    });

    // Add features to the layer
    if (this.displayMode === 'segments') {
      // Display polygons
      const features = this.geoJsonData.features.map((feature, index) => {
        return {
          geometry: {
            type: "polygon",
            rings: feature.geometry.coordinates[0],
            spatialReference: { wkid: 4326 }
          },
          attributes: {
            objectid: index + 1,
            value: feature.properties.value || 'Unknown'
          }
        };
      });

      featureLayer.applyEdits({
        addFeatures: features
      });
    } else if (this.displayMode === 'centroids') {
      // Display centroids
      const features = this.geoJsonData.features.map((feature, index) => {
        const coordinates = feature.geometry.coordinates[0];
        const centroid = this.calculateCentroid(coordinates);

        return {
          geometry: {
            type: "point",
            longitude: centroid[0],
            latitude: centroid[1],
            spatialReference: { wkid: 4326 }
          },
          attributes: {
            objectid: index + 1,
            value: feature.properties.value || 'Unknown'
          }
        };
      });

      featureLayer.applyEdits({
        addFeatures: features
      });
    }

    // Remove old layer if exists
    if (this.editableLayer) {
      this.view.map.remove(this.editableLayer);
    }

    // Add new layer to map
    this.view.map.add(featureLayer);
    this.editableLayer = featureLayer;
  }

  calculateCentroid(coordinates) {
    let sumX = 0;
    let sumY = 0;
    const len = coordinates.length - 1; // Subtract 1 because in polygons, last point equals first point

    for (let i = 0; i < len; i++) {
      sumX += coordinates[i][0];
      sumY += coordinates[i][1];
    }

    return [sumX / len, sumY / len];
  }
}

// Export the class
export { ObjectDetectionPanel };
