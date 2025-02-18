from samgeo import SamGeo
from .basePredictor import BasePredictor, logger
from app.config import settings
import numpy as np

class PointSegmentationPredictor(BasePredictor):
    """Point-based segmentation predictor"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PointSegmentationPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_type=settings.SAMGEO_MODEL_TYPE):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.model_type = model_type
            self._model = None
            self._initialized = True
            logger.info(f"Initialized PointSegmentationPredictor with model type: {model_type}")

    @property
    def model(self):
        if not self._model:
            try:
                logger.info(f"Loading SamGeo model: {self.model_type}")
                self._model = SamGeo(
                    model_type=self.model_type,
                    automatic=False,
                    sam_kwargs=None
                )
                logger.success("SamGeo model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load SamGeo model: {str(e)}")
                raise
        return self._model

    async def predict(self, input_image, points, point_labels, box_threshold, output_image):
        """Point-based prediction logic that matches old version's behavior"""
        try:
            # Set image and run prediction with same parameters
            self.model.set_image(input_image)
            self.model.predict(
                point_coords=np.array(points),
                point_labels=np.array(point_labels),
                point_crs="EPSG:4326",
                box_threshold=box_threshold,
                output=output_image
            )
            
            logger.success("Point-based prediction and visualization completed")
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_model'):
            self._model = None
            logger.info("Cleaned up PointSegmentationPredictor instance") 