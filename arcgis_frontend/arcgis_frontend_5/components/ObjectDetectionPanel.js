class ObjectDetectionPanel {
  constructor(detectionParameters, displayPredictResult) {
    this.textPromptUrl = "http://localhost:8001/api/v1/predict/text";
    this.pointsPromptUrl = "http://localhost:8001/api/v1/predict/points";
    this.view = detectionParameters.view;
    this.detectionParameters = detectionParameters;
    this.textPrompt = '';
    this.zoomLevel = 20;
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.predictResult = null;
    this.panelVisible = false;
    this.displayPredictResult = displayPredictResult;
    this.displayParameters = {
      color: '#3333CC',
      opacity: 0.9,
      displayMode: 'segments',
    };

    // points prompt related
    this.pointsPromptParameters = {
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
    const opacityInputs = this.panel.querySelectorAll('input[name="opacity"]');
    const opacityValues = this.panel.querySelectorAll('input[name="opacity-value"]');
    opacityInputs.forEach(opacityInput => {
      opacityInput.addEventListener('input', (e) => {
        this.displayParameters.opacity = parseFloat(e.target.value);
        opacityValues.forEach(opacityValue => {
          opacityValue.textContent = this.displayParameters.opacity.toFixed(1);
        });
        if (this.predictResult) {
          this.displayPredictResult(this.predictResult, this.displayParameters);
        }
      });
    });

    // Color picker
    const colorPickers = this.panel.querySelectorAll('input[name="color-picker"]');
    colorPickers.forEach(colorPicker => {
      colorPicker.addEventListener('input', (e) => {
        this.displayParameters.color = e.target.value;
        if (this.predictResult) {
          this.displayPredictResult(this.predictResult, this.displayParameters);
        }
      });
    });

    // Display mode radio buttons
    const displayModeInputs = this.panel.querySelectorAll('input[name="text-display-mode"], input[name="points-display-mode"]');
    displayModeInputs.forEach(input => {
      input.addEventListener('change', (e) => {
        this.displayParameters.displayMode = e.target.value;
        if (this.predictResult) {
          this.displayPredictResult(this.predictResult, this.displayParameters);
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
    this.panel.querySelector('#detect-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.handleTextDetect();
    });
    this.panel.querySelector('#points-detect-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      this.handlePointsDetect();
    });

    //Add points button
    this.panel.querySelector('#includeMode').addEventListener('click', () => {
      if (this.pointsPromptParameters.deleteMode) {
        this.pointsPromptParameters.deleteMode = false;
      }
      this.pointsPromptParameters.currentMode = this.pointsPromptParameters.currentMode === 'include' ? null : 'include';
      this.updatePointButtonStates();
      this.view.cursor = this.pointsPromptParameters.currentMode ? "crosshair" : "default";
    });

    this.panel.querySelector('#excludeMode').addEventListener('click', () => {
      if (this.pointsPromptParameters.deleteMode) {
        this.pointsPromptParameters.deleteMode = false;
      }
      this.pointsPromptParameters.currentMode = this.pointsPromptParameters.currentMode === 'exclude' ? null : 'exclude';
      this.updatePointButtonStates();
      this.view.cursor = this.pointsPromptParameters.currentMode ? "crosshair" : "default";
    });

    this.panel.querySelector('#deleteMode').addEventListener('click', () => {
      this.pointsPromptParameters.deleteMode = !this.pointsPromptParameters.deleteMode;
      if (this.pointsPromptParameters.deleteMode) {
        this.pointsPromptParameters.currentMode = null;
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

    includeButton.className = `mode-button ${this.pointsPromptParameters.currentMode === 'include' ? 'active' : ''}`;
    excludeButton.className = `mode-button ${this.pointsPromptParameters.currentMode === 'exclude' ? 'active' : ''}`;
    deleteButton.className = `mode-button ${this.pointsPromptParameters.deleteMode ? 'delete-mode' : ''}`;
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

  async handleTextDetect() {
    const bbox = this.detectionParameters?.geometry?.extent;
    if (!this.zoomLevel || !this.textPrompt || !bbox) {
      alert('Please draw a rectangle and enter detection parameters');
      return;
    }
    const detectButton = this.panel.querySelector('#detect-btn');
    try {
      detectButton.classList.add('loading');
      detectButton.disabled = true;
      this.disablePanel();

      const boundingBox = convertBoundingBoxToGeographic(extentToBoundingBox(bbox));

      const testPrompts = this.textPrompt.split(",").map((prompt) => ({
        value: prompt.trim(),
        box_threshold: this.boxThreshold,
        text_threshold: this.textThreshold
      }))
      const requestBody = {
        "bounding_box": boundingBox,
        "text_prompts": testPrompts,
        "zoom_level": this.zoomLevel,
      };  
      await this.sendPredictRequest(this.textPromptUrl, requestBody);
      
    } catch (error) {
      throw error;      
    } finally{
      detectButton.classList.remove('loading');
      detectButton.disabled = false;
      this.enablePanel();
    }
  }
        
  async handlePointsDetect() {
    if (this.pointsPromptParameters.includePoints.length === 0) {
      alert('Please add at least one include point');
      return;
    }
    const detectButton = this.panel.querySelector('#points-detect-btn');    
    try {
      detectButton.classList.add('loading');
      detectButton.disabled = true;
      this.disablePanel();

      const requestBody = {
        zoom_level: this.zoomLevel,
        box_threshold: this.boxThreshold,
        points_include: this.pointsPromptParameters.includePoints,
        points_exclude: this.pointsPromptParameters.excludePoints
      };

      await this.sendPredictRequest(this.pointsPromptUrl, requestBody);
      
    } catch (error) {
      throw error;      
    } finally{
      detectButton.classList.remove('loading');
      detectButton.disabled = false;
      this.enablePanel();
    }
  }
        
  async sendPredictRequest(url, requestBody) {

    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const raw = JSON.stringify(requestBody);

    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: raw,
      redirect: "follow"
    };

    const response = await fetch(url, requestOptions);
    if (!response.ok) {
      throw new Error("Network response was not ok while sending object detection request.");
    }
    this.predictResult = await response.json();
    this.displayPredictResult(this.predictResult, this.displayParameters);
  }

  resetSettings() {  
    this.textPrompt = '';
    this.zoomLevel = 20;
    this.boxThreshold = 0.24;
    this.textThreshold = 0.24;
    this.predictResult = null;
    this.displayParameters = {
      color: '#3333CC',
      opacity: 0.9,
      displayMode: 'segments',
    };
    this.pointsPromptParameters = {
      includePoints : [],
      excludePoints :[],
      currentMode : null,
      deleteMode : false,
    }

    // Update UI elements
    this.panel.querySelectorAll('input[name="opacity"]').forEach(input => {
      input.value = this.displayParameters.opacity;
    });
    this.panel.querySelectorAll('span[name="opacity-value"]').forEach(span => {
      span.textContent = this.displayParameters.opacity.toFixed(1);
    });
    this.panel.querySelectorAll('input[name="color-picker"]').forEach(picker => {
      picker.value = this.displayParameters.color;
    });
    this.panel.querySelectorAll('input[name="text-display-mode"], input[name="points-display-mode"]').forEach(radio => {
      radio.checked = (radio.value === this.displayParameters.displayMode);
    });

    //text tab
    this.panel.querySelector('#box-threshold').value = this.boxThreshold;
    this.panel.querySelector('#box-threshold-value').textContent = this.boxThreshold.toFixed(2);
    this.panel.querySelector('#text-threshold').value = this.textThreshold;
    this.panel.querySelector('#text-threshold-value').textContent = this.textThreshold.toFixed(2);
    this.panel.querySelector('#zoom-level').value = '20';
    this.panel.querySelector('#text-prompt').value = '';
    this.detectionParameters.sketch.cancel();
    this.detectionParameters.textDetectionLayer.removeAll();
    //points tab
    this.panel.querySelector('#points-box-threshold').value = this.boxThreshold;
    this.panel.querySelector('#points-box-threshold-value').textContent = this.boxThreshold.toFixed(2);
    this.panel.querySelector('#points-zoom-level').value = '20';
    this.updatePointButtonStates();

  }


  disablePanel() {
    const inputs = this.panel.querySelectorAll('input, select, button, .tab-btn');
    inputs.forEach(input => {
      input.disabled = true;
    });
    this.panel.style.opacity = '0.95';
    this.panel.style.pointerEvents = 'none';
    this.detectionParameters.sketch.cancel();
  }

  enablePanel() {
    const inputs = this.panel.querySelectorAll('input, select, button, .tab-btn');
    inputs.forEach(input => {
      input.disabled = false;
    });
    this.panel.style.opacity = '1';
    this.panel.style.pointerEvents = 'auto';
  }
}

// Export the class
export { ObjectDetectionPanel };
