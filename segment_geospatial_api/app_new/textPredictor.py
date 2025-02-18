from samgeo import tms_to_geotiff, raster_to_vector
from samgeo.text_sam import LangSAM
from .basePredictor import BasePredictor, logger
from app.config import settings
import inspect

class TextSegmentationPredictor(BasePredictor):
    """Text-based segmentation predictor"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TextSegmentationPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_type=settings.LANGSAM_MODEL_TYPE):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self.model_type = model_type
            self._sam = None
            self._initialized = True
            print(f"\n[Init] model_type: {model_type}")
            logger.info(f"Initialized TextSegmentationPredictor with model type: {model_type}")

    def download_satellite_image(self, image_name, bounding_box, zoom_level):
        """Download satellite imagery using the same method as the old version"""
        tms_to_geotiff(
            image_name,
            bounding_box,
            zoom_level,
            source="Satellite",
            overwrite=True
        )

    @property
    def sam(self):
        if not self._sam:
            try:
                print(f"\n[Loading Model] model_type: {self.model_type}")
                self._sam = LangSAM(model_type=self.model_type)
                print(f"[Model Loaded] Model attributes: {dir(self._sam)}")
                print(f"[Model Loaded] Model type: {type(self._sam)}")
                logger.success("LangSAM model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load LangSAM model: {str(e)}")
                raise
        return self._sam

    async def predict(self, input_image, text_prompt, box_threshold, text_threshold, output_image):
        """Integrated prediction logic that matches old version's behavior"""
        try:
            print("\n[Predict] Parameters:")
            print(f"- input_image: {input_image}")
            print(f"- text_prompt: {text_prompt}")
            print(f"- box_threshold: {box_threshold} (type: {type(box_threshold)})")
            print(f"- text_threshold: {text_threshold} (type: {type(text_threshold)})")
            print(f"- output_image: {output_image}")
            
            # 打印predict方法的签名
            predict_signature = inspect.signature(self.sam.predict)
            print(f"\n[Method Signature] predict: {predict_signature}")
            
            self.sam.predict(
                input_image, 
                text_prompt, 
                box_threshold,
                text_threshold
            )
            print("\n[Predict] Prediction completed")
            
            # 打印show_anns方法的签名
            show_anns_signature = inspect.signature(self.sam.show_anns)
            print(f"\n[Method Signature] show_anns: {show_anns_signature}")
            
            self.sam.show_anns(
                cmap="Greys_r",
                add_boxes=False,
                alpha=1,
                title=f"Automatic Segmentation of {text_prompt}",
                blend=False,
                output=output_image,
            )
            print("\n[Show Anns] Visualization completed")
            
            logger.success("Prediction and visualization completed")
            
        except Exception as e:
            print(f"\n[Error] Exception occurred: {str(e)}")
            print(f"[Error] Exception type: {type(e)}")
            logger.error(f"Prediction failed: {str(e)}")
            raise

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, '_sam'):
            self._sam = None
            logger.info("Cleaned up TextSegmentationPredictor instance")
        