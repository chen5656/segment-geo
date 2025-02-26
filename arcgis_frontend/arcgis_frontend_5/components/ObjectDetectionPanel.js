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
  constructor(detectionParameters,displayGeojsonData,  geojsonLayer) {
    this.view = detectionParameters.view;
    this.textDetectionLayer = detectionParameters.textDetectionLayer,
    this.pointDetectionLayer = detectionParameters.pointDetectionLayer,
    this.detectionParameters = detectionParameters;
    this.textPrompt = '';
    this.zoomLevel = 20;
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.geoJsonData = null;
    this.panelVisible = false;
    this.displayGeojsonData = displayGeojsonData;
    this.displayParameters = {
      color: '#3333CC',
      opacity: 0.9,
      displayMode: 'segments',
    };
    this.editableLayer = geojsonLayer;
    
    // points prompt related
    this.pointPromptParameters = {
      includePoints : [],
      excludePoints :[],
      currentMode : null,
      deleteMode : false,
    }

        
    this.init();
  }

  async init() {
    this.addStyles();
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
      this.displayParameters.opacity = parseFloat(e.target.value);
      opacityValue.textContent = this.displayParameters.opacity.toFixed(1);
      if (this.geoJsonData) {
        this.displayGeojsonData(this.geoJsonData, this.displayParameters);
      }
    });

    // Color picker
    const colorPicker = this.panel.querySelector('#color-picker');
    colorPicker.addEventListener('input', (e) => {
      this.displayParameters.color = e.target.value;
      if (this.geoJsonData) {        
        this.displayGeojsonData(this.geoJsonData, this.displayParameters);
      }
    });

    // Display mode radio buttons
    const displayModeInputs = this.panel.querySelectorAll('input[name="display-mode"]');
    displayModeInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        this.displayParameters.displayMode = e.target.value;
        if (this.geoJsonData) {
          this.displayGeojsonData(this.geoJsonData, this.displayParameters);
        }
      });
    });

    // Reset button
    this.panel.querySelector('#reset-btn').addEventListener('click', () => {
      this.resetSettings();
    });
    this.panel.querySelector('#points-reset-btn').addEventListener('click', () => {
      this.resetSettings();
    });

    // Tab switching
    const tabButtons = this.panel.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        // Remove active class from all buttons and panes
        tabButtons.forEach(btn => btn.classList.remove('active'));
        this.panel.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

        // Add active class to clicked button and corresponding pane
        button.classList.add('active');
        const tabId = button.dataset.tab;
        this.panel.querySelector(`#${tabId}-tab`).classList.add('active');

        //reset panel
        this.resetSettings();
      });
    });

    // Detect button
    const detectButton = this.panel.querySelector('#detect-btn');
    detectButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.handleDetect();
    });

    //Add points button
    this.panel.querySelector('#includeMode').addEventListener('click', () => {
      if (this.pointPromptParameters.deleteMode) {
        this.pointPromptParameters.deleteMode = false;
      }
      this.pointPromptParameters.currentMode = this.pointPromptParameters.currentMode === 'include' ? null : 'include';
      this.updatePointButtonStates();
      this.view.cursor = this.pointPromptParameters.currentMode ? "crosshair" : "default";
    });

    this.panel.querySelector('#excludeMode').addEventListener('click', () => {
      if (this.pointPromptParameters.deleteMode) {
        this.pointPromptParameters.deleteMode = false;
      }
      this.pointPromptParameters.currentMode = this.pointPromptParameters.currentMode === 'exclude' ? null : 'exclude';
      this.updatePointButtonStates();
      this.view.cursor = this.pointPromptParameters.currentMode ? "crosshair" : "default";
    });

    this.panel.querySelector('#deleteMode').addEventListener('click', () => {
      this.pointPromptParameters.deleteMode = !this.pointPromptParameters.deleteMode;
      if (this.pointPromptParameters.deleteMode) {
        this.pointPromptParameters.currentMode = null;
        this.view.cursor = "not-allowed";
      } else {
        this.view.cursor = "default";
      }
      this.updatePointButtonStates();
    });           

  }
  
  updatePointButtonStates = () => {
    const includeButton = this.panel.querySelector('#includeMode');
    const excludeButton = this.panel.querySelector('#excludeMode');
    const deleteButton = this.panel.querySelector('#deleteMode');

    includeButton.className = `mode-button ${this.pointPromptParameters.currentMode === 'include' ? 'active' : ''}`;
    excludeButton.className = `mode-button ${this.pointPromptParameters.currentMode === 'exclude' ? 'active' : ''}`;
    deleteButton.className = `mode-button ${this.pointPromptParameters.deleteMode ? 'delete-mode' : ''}`;
  };

  async addStyles() {
    const style = document.createElement('style');
    const moduleURL = new URL('./ObjectDetectionPanel.css', import.meta.url);
    const response = await fetch(moduleURL);
    const css = await response.text();
    style.textContent = css;
    document.head.appendChild(style);
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
  
      await this.sendTextPredictRequest(requestBody);
      
    } catch (error) {
      throw error;      
    } finally{
      detectButton.classList.remove('loading');
      detectButton.disabled = false;
    }
  }
          
  async sendTextPredictRequest(requestBody) {

    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const raw = JSON.stringify(requestBody);

    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow"
    };

    const response = await fetch("http://localhost:8001/api/v1/predict", requestOptions);
    if (!response.ok) {
      throw new Error("Network response was not ok while sending object detection request.");
    }
    this.geoJsonData = await response.json();
    this.displayGeojsonData(this.geoJsonData, this.displayParameters);
  }

  resetSettings() {  
    this.textPrompt = '';
    this.zoomLevel = 20;
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.geoJsonData = null;
    this.displayParameters = {
      color: '#3333CC',
      opacity: 0.9,
      displayMode: 'segments',
    };
    this.pointPromptParameters = {
      includePoints : [],
      excludePoints :[],
      currentMode : null,
      deleteMode : false,
    }

    // Update UI elements
    //text tab
    this.panel.querySelector('#box-threshold').value = this.boxThreshold;
    this.panel.querySelector('#box-threshold-value').textContent = this.boxThreshold.toFixed(2);
    this.panel.querySelector('#text-threshold').value = this.textThreshold;
    this.panel.querySelector('#text-threshold-value').textContent = this.textThreshold.toFixed(2);
    this.panel.querySelector('#zoom-level').value = '20';
    this.panel.querySelector('#opacity').value = this.displayParameters.opacity;
    this.panel.querySelector('#opacity-value').textContent = this.displayParameters.opacity.toFixed(1);
    this.panel.querySelector('#color-picker').value = this.displayParameters.color;
    this.panel.querySelector('#display-segments').checked = true;
    this.panel.querySelector('#text-prompt').value = '';
    //points tab
    this.panel.querySelector('#points-box-threshold').value = this.boxThreshold;
    this.panel.querySelector('#points-box-threshold-value').textContent = this.boxThreshold.toFixed(2);
    this.panel.querySelector('#points-zoom-level').value = '20';
    this.panel.querySelector('#point-opacity').value = this.displayParameters.opacity;
    this.panel.querySelector('#point-opacity-value').textContent = this.displayParameters.opacity.toFixed(1);
    this.panel.querySelector('#point-color-picker').value = this.displayParameters.color;
    this.panel.querySelector('#points-display-segments').checked = true;
    this.updatePointButtonStates();

  }
}

// Export the class
export { ObjectDetectionPanel };
