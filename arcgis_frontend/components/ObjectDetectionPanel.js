class ObjectDetectionPanel {
  constructor(view, detectionParameters) {
    this.view = view;
    this.detectionParameters = detectionParameters;
    this.textPrompt = '';
    this.isLoading = false;
    this.bbox = null;
    this.pointPosition = 'bottom-right';
    this.zoomLevel = view.zoom;
    this.geoJsonData = null;
    this.lastRequestBody = null;
    this.panelVisible = false;
    
    this.createPanel();
    this.setupEventListeners();
  }

  createPanel() {
    this.panel = document.createElement('div');
    this.panel.className = 'object-detection-panel';
    this.panel.style.display = 'none';
    
    this.panel.innerHTML = `
      <div class="panel-header">
        <h3>Object Detection</h3>
        <button class="close-btn">×</button>
      </div>
      <div class="panel-content">
        <div class="input-group">
          <label for="text-prompt">What do you want to detect?</label>
          <input type="text" id="text-prompt" placeholder="e.g., poles, trees, buildings">
        </div>
        
        <div class="input-group">
          <label for="point-position">Point Position</label>
          <select id="point-position" disabled>
            <option value="top-right">Top Right</option>
            <option value="top-left">Top Left</option>
            <option value="bottom-right" selected>Bottom Right</option>
            <option value="bottom-left">Bottom Left</option>
          </select>
        </div>
        
        <div class="input-group">
          <label for="zoom-level">Zoom Level</label>
          <select id="zoom-level">
            ${[15, 16, 17, 18, 19, 20, 21, 22].map(zoom => 
              `<option value="${zoom}">${zoom}</option>`
            ).join('')}
          </select>
        </div>
        <div class="instruction">
          <span>Draw a rectangle to start</span>
        </div>
        <div id='sketch_container'>
          
        </div>
        
        <button id="detect-btn" class="detect-button">
          Detect Objects
        </button>
        
        <div id="request-info" style="display: none">
          <button class="toggle-request-btn">Show Request</button>
          <pre class="request-body" style="display: none"></pre>
        </div>
      </div>
    `;
    
    document.body.appendChild(this.panel);
    this.addStyles();
  }

  addStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .object-detection-panel {
        position: absolute;
        top: 10px;
        left: 10px;
        width: 300px;
        background: white;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        z-index: 1000;
        font-family: Arial, sans-serif;
      }
      
      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 15px;
        border-bottom: 1px solid #eee;
      }
      
      .panel-header h3 {
        margin: 0;
        font-size: 16px;
      }
      
      .close-btn {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        padding: 0 5px;
      }
      
      .panel-content {
        padding: 15px;
      }
      
      .input-group {
        margin-bottom: 15px;
      }
      
      .input-group label {
        display: block;
        margin-bottom: 5px;
        font-size: 14px;
      }
      
      .input-group input,
      .input-group select {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
      }
      
      .instruction {
        margin: 10px 0;
        font-size: 14px;
        color: #666;
      }
      
      .detect-button {
        width: 100%;
        padding: 10px;
        background: #1976d2;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
      }
      
      .detect-button:disabled {
        background: #ccc;
        cursor: not-allowed;
      }
      
      .detect-button.loading {
        position: relative;
        color: transparent;
      }
      
      .detect-button.loading::after {
        content: '';
        position: absolute;
        width: 16px;
        height: 16px;
        top: 50%;
        left: 50%;
        margin: -8px 0 0 -8px;
        border: 2px solid #fff;
        border-radius: 50%;
        border-right-color: transparent;
        animation: spin 0.75s linear infinite;
      }
      
      @keyframes spin {
        100% { transform: rotate(360deg); }
      }
      
      .toggle-request-btn {
        margin-top: 10px;
        background: none;
        border: 1px solid #ddd;
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
      }
      
      .request-body {
        margin-top: 10px;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 4px;
        font-size: 12px;
        white-space: pre-wrap;
        max-height: 200px;
        overflow: auto;
      }
    `;
    document.head.appendChild(style);
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

    // Point position select
    const pointPositionSelect = this.panel.querySelector('#point-position');
    pointPositionSelect.addEventListener('change', (e) => {
      this.pointPosition = e.target.value;
    });

    // Zoom level select
    const zoomLevelSelect = this.panel.querySelector('#zoom-level');
    zoomLevelSelect.value = this.zoomLevel;
    zoomLevelSelect.addEventListener('change', (e) => {
      this.zoomLevel = parseInt(e.target.value);
    });

    // Detect button
    const detectButton = this.panel.querySelector('#detect-btn');
    detectButton.addEventListener('click', () => this.handleDetect());

    // Toggle request info
    const toggleRequestBtn = this.panel.querySelector('.toggle-request-btn');
    toggleRequestBtn.addEventListener('click', () => {
      const requestBody = this.panel.querySelector('.request-body');
      const isHidden = requestBody.style.display === 'none';
      requestBody.style.display = isHidden ? 'block' : 'none';
      toggleRequestBtn.textContent = isHidden ? 'Hide Request' : 'Show Request';
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
    this.detectionParameters.layer.removeAll();
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
    this.bbox = this.detectionParameters?.geometry?.extent;
    if (!this.zoomLevel || !this.textPrompt || !this.bbox) {
      alert('Please draw a rectangle and enter detection parameters');
      return;
    }

    const requestBody = {
      bounding_box: bbox,
      text_prompt: this.textPrompt,
      zoom_level: this.zoomLevel,
      box_threshold: 0.24,
      text_threshold: 0.24,
    };

    this.lastRequestBody = requestBody;
    this.updateRequestInfo(requestBody);
    
    const detectButton = this.panel.querySelector('#detect-btn');
    detectButton.classList.add('loading');
    this.isLoading = true;

    try {
      const response = await fetch('http://localhost:8001/api/v1/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      } else if (data.geojson) {
        this.geoJsonData = data.geojson;
        // Emit event for map to handle
        const event = new CustomEvent('detection-complete', {
          detail: { geojson: data.geojson }
        });
        document.dispatchEvent(event);
      } else {
        throw new Error('No geojson data');
      }
    } catch (error) {
      console.error('Error during detection:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Server error';
      alert(`Error: ${errorMessage}`);
    } finally {
      detectButton.classList.remove('loading');
      this.isLoading = false;
    }
  }

  updateRequestInfo(requestBody) {
    const requestInfo = this.panel.querySelector('#request-info');
    const requestBodyPre = this.panel.querySelector('.request-body');
    requestInfo.style.display = 'block';
    requestBodyPre.textContent = JSON.stringify(requestBody, null, 2);
  }
}

// Export the class
export { ObjectDetectionPanel }; 