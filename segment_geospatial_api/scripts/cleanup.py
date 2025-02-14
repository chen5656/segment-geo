import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_temp_files():
    """Clean up temporary files created during API operation"""
    # Clean up temporary image and geojson files
    temp_patterns = ['satellite_*.tif', 'segment_*.tif', 'segment_*.geojson']
    
    cleaned = 0
    for pattern in temp_patterns:
        for file in Path('.').glob(pattern):
            try:
                os.remove(file)
                cleaned += 1
                logger.info(f"Removed temporary file: {file}")
            except Exception as e:
                logger.error(f"Error removing {file}: {e}")
                
    logger.info(f"Cleaned up {cleaned} temporary files")

def cleanup_model_cache():
    """Clean up downloaded model files"""
    # Common cache directories for huggingface models
    cache_dirs = [
        os.path.expanduser("~/.cache/huggingface"),
        os.path.expanduser("~/.cache/torch"),
        "./models"  # Local models directory if used
    ]
    
    cleaned = 0
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                cleaned += 1
                logger.info(f"Removed cache directory: {cache_dir}")
            except Exception as e:
                logger.error(f"Error removing {cache_dir}: {e}")
                
    logger.info(f"Cleaned up {cleaned} cache directories")

if __name__ == "__main__":
    logger.info("Starting cleanup process...")
    cleanup_temp_files()
    cleanup_model_cache()
    logger.info("Cleanup completed") 