
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
        },
        {
          name: "value",
          type: "string"
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
        title: "{value}",
        content: displayMode === 'segments' ? 
          "Polygon Area: {value}" : 
          "Point Location: {value}"
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
            objectid: index + 1,
            value: feature.properties.value || 'Unknown'
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
            objectid: index + 1,
            value: feature.properties.value || 'Unknown'
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
  sketch = new Sketch({
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