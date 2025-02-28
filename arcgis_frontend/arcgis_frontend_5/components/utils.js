
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

const getGeojsonLayer = (FeatureLayer, geoJsonData, displayParameters, title='Detection Result') => {
    const color = displayParameters?.color || '#ff0000';
    const opacity = displayParameters?.opacity || 0.5;
    const displayMode = displayParameters?.displayMode || 'segments';
    
    // Create appropriate FeatureLayer based on display mode
    const featureLayer = new FeatureLayer({
      source: [], // Start with empty source
      title: title,
      objectIdField: "objectid",
      fields: [
        {
          name: "objectid",
          type: "oid"
        }
      ],
      renderer: displayMode === 'segments' ? 
        // Polygon renderer
        {
          type: "simple",
          symbol: {
            type: "simple-fill",
            color: [
              parseInt(color.slice(1, 3), 16),
              parseInt(color.slice(3, 5), 16),
              parseInt(color.slice(5, 7), 16),
              opacity
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
              parseInt(color.slice(1, 3), 16),
              parseInt(color.slice(3, 5), 16),
              parseInt(color.slice(5, 7), 16),
              opacity
            ],
            size: "12px",
            outline: {
              color: "white",
              width: 1
            }
          }
        },
      geometryType: displayMode === 'segments' ? "polygon" : "point",
      popupTemplate: {
        title: "{objectid}",
        content: "objectid: {objectid}"
      }
    });
  
    // Add features to the layer
    if (displayMode === 'segments') {
      // Display polygons
      const features = geoJsonData.features.map((feature, index) => {
        return {
          geometry: {
            type: "polygon",
            rings: feature.geometry.coordinates[0],
            spatialReference: { wkid: 4326 }
          },
          attributes: {
            objectid: index + 1
          }
        };
      });
  
      featureLayer.applyEdits({
        addFeatures: features
      });
    } else if (displayMode === 'centroids') {
      // Display centroids
      const features = geoJsonData.features.map((feature, index) => {
        const coordinates = feature.geometry.coordinates[0];
        const centroid = calculateCentroid(coordinates);
  
        return {
          geometry: {
            type: "point",
            longitude: centroid[0],
            latitude: centroid[1],
            spatialReference: { wkid: 4326 }
          },
          attributes: {
            objectid: index + 1
          }
        };
      });
  
      featureLayer.applyEdits({
        addFeatures: features
      });
    }
    return featureLayer;
}

function getNewSketch(Sketch, view, graphicsLayer, detectionParameters){
  const sketch = new Sketch({
    layer: graphicsLayer,
    view: view,
    container: "sketch_container",
    availableCreateTools: ["rectangle"],
    visibleElements: {
      selectionTools: {
        "lasso-selection": false,
        "rectangle-selection": false,
      },
      settingsMenu: false,
      undoRedoMenu: false,
    },
  });
  sketch.on('create', (event) => {
    if (event.state === 'start') {
      detectionParameters.geometry = null;
      detectionParameters.textDetectionLayer.removeAll();
    }
    if (event.state === 'complete') {
      detectionParameters.geometry = event.graphic.geometry;
    }
  });
  return sketch;
};


function calculateCentroid(coordinates) {
  let sumX = 0;
  let sumY = 0;
  const len = coordinates.length - 1; // Subtract 1 because in polygons, last point equals first point

  for (let i = 0; i < len; i++) {
    sumX += coordinates[i][0];
    sumY += coordinates[i][1];
  }

  return [sumX / len, sumY / len];
}

function updatePoints(detectionParameters, pointsPromptParameters, view, event, Graphic){
  let {currentMode, deleteMode} = pointsPromptParameters;

  const pointsLayer = detectionParameters.pointsDetectionLayer

  if (deleteMode) {
    const screenPoint = {
      x: event.x,
      y: event.y
    };

    view.hitTest(screenPoint).then((response) => {
      const graphics = response.results?.filter(result => 
        result.graphic.layer === pointsLayer
      );

      if (graphics && graphics.length > 0) {
        const point = [graphics[0].graphic.geometry.longitude, graphics[0].graphic.geometry.latitude];
        pointsPromptParameters.includePoints = pointsPromptParameters.includePoints.filter(p => 
          Math.abs(p[0] - point[0]) > 0.0000001 || Math.abs(p[1] - point[1]) > 0.0000001
        );
        pointsPromptParameters.excludePoints = pointsPromptParameters.excludePoints.filter(p => 
          Math.abs(p[0] - point[0]) > 0.0000001 || Math.abs(p[1] - point[1]) > 0.0000001
        );
        updatePointsGraphics(pointsLayer, pointsPromptParameters.includePoints, pointsPromptParameters.excludePoints, Graphic);
      }
    });
  } else if (currentMode) {
    const mapPoint = view.toMap({x: event.x, y: event.y});
    const point = [mapPoint.longitude, mapPoint.latitude];
    
    if (currentMode === 'include') {
      pointsPromptParameters.includePoints.push(point);
    } else {
      pointsPromptParameters.excludePoints.push(point);
    }
    updatePointsGraphics(pointsLayer, pointsPromptParameters.includePoints, pointsPromptParameters.excludePoints, Graphic);
  }
}


 function updatePointsGraphics(pointsLayer, includePoints, excludePoints, Graphic) {
    pointsLayer.removeAll();
  
    includePoints.forEach(coords => {
      const point = {
        type: "point",
        longitude: coords[0],
        latitude: coords[1]
      };
      
      const markerSymbol = {
        type: "simple-marker",
        style: "circle",
        color: [0, 255, 0, 0.8],  // 绿色
        size: "12px",
        outline: {
          color: [255, 255, 255, 0.8],
          width: 2
        }
      };
      
      const graphic = new Graphic({
        geometry: point,
        symbol: markerSymbol
      });
      
      pointsLayer.add(graphic);
    });

    excludePoints.forEach(coords => {
      const point = {
        type: "point",
        longitude: coords[0],
        latitude: coords[1]
      };
      
      const markerSymbol = {
        type: "simple-marker",
        style: "circle",
        color: [255, 0, 0, 0.8],  // 红色
        size: "12px",
        outline: {
          color: [255, 255, 255, 0.8],
          width: 2
        }
      };
      
      const graphic = new Graphic({
        geometry: point,
        symbol: markerSymbol
      });
      
      pointsLayer.add(graphic);
    });
  }