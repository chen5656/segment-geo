from samgeo import tms_to_geotiff
from samgeo.text_sam import LangSAM
import threading
import asyncio
import uuid
import json
import os


class SegmentationPredictor:
    def __init__(self):
        self._sam = None
        self._lock = threading.Lock()  # 用于线程安全

    @property
    def sam(self):
        if self._sam is None:
            with self._lock:
                if self._sam is None:  # 双重检查锁定
                    self._sam = LangSAM()
        return self._sam

    async def make_prediction(self, *, bounding_box, text_prompt, zoom_level = 20):
        """Make a prediction using SAM."""
        # 为每个请求生成唯一的文件名
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        try:
            await tms_to_geotiff(bounding_box, input_image, zoom_level)
            
            # 使用线程池执行CPU密集型操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, 
                self.sam.predict, 
                input_image, 
                text_prompt, 
                0.24,  # box_threshold 
                0.24   # text_threshold
            )
            
            await loop.run_in_executor(None,
                self.sam.show_anns,
                "Greys_r",  # cmap
                False,      # add_boxes
                1,         # alpha
                f"Automatic Segmentation of {text_prompt}",
                False,     # blend
                output_image
            )
            
            await loop.run_in_executor(None,
                self.sam.tiff_to_geojson,
                output_image,
                output_geojson,
                None      # simplify_tolerance
            )
            
            # 读取geojson内容
            with open(output_geojson, 'r') as f:
                geojson_content = json.load(f)
                
            return {"geojson": geojson_content}
            
        finally:
            # 清理临时文件
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    os.remove(file)

# 创建单例实例
predictor = SegmentationPredictor()

