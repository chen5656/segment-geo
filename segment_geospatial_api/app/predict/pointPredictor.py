from samgeo import SamGeo
from .basePredictor import BasePredictor, logger
from app.config import settings
import numpy as np

class PointSegmentationPredictor(BasePredictor):
    """Point-based segmentation predictor"""
    def __init__(self, model_type=settings.SAMGEO_MODEL_TYPE):
        super().__init__()
        self.model_type = model_type
        self._model = None
        logger.success(f"Initialized PointSegmentationPredictor with model type: {model_type}")

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
        """Point-based prediction logic"""
        try:
            self.model.set_image(input_image)
            self.model.predict(
                point_coords=np.array(points),
                point_labels=np.array(point_labels),
                point_crs="EPSG:4326",
                box_threshold=box_threshold,
                output=output_image
            )
            return True
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise 