from samgeo.text_sam import LangSAM
from .basePredictor import BasePredictor, logger
from app.config import settings

class TextSegmentationPredictor(BasePredictor):
    """Text-based segmentation predictor"""
    def __init__(self, model_type=settings.LANGSAM_MODEL_TYPE):
        super().__init__()
        self.model_type = model_type
        self._model = None
        logger.info(f"Initialized TextSegmentationPredictor with model type: {model_type}")

    @property
    def model(self):
        if not self._model:
            try:
                logger.info(f"Loading LangSAM model: {self.model_type}")
                self._model = LangSAM(model_type=self.model_type)
                logger.success("LangSAM model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LangSAM model: {str(e)}")
                raise
        return self._model

    async def predict(self, input_image, text_prompt, box_threshold, text_threshold, output_image):
        """Text-based prediction logic"""
        try:
            self.model.predict(
                input_image,
                text_prompt,
                box_threshold,
                text_threshold
            )
            logger.success("Text-based prediction completed successfully")
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise 

        try:
            self.model.show_anns(
                cmap="Greys_r",
                add_boxes=False,
                alpha=1,
                title=f"Segmentation of {text_prompt}",
                blend=False,
                output=output_image,
            )
            logger.success("Visualization generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate visualization: {str(e)}", exc_info=True)
            return {"error": f"Failed to generate visualization: {str(e)}"}
        