import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import mercantile
from tqdm import tqdm
import yaml

class BingBuildingDownloader:
    def __init__(self):
        self.config = self._load_config()
        self._ensure_directories()
        
    def _load_config(self):
        config_path = "config/bing_buildings.yml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)['bing_buildings']
    
    def _ensure_directories(self):
        os.makedirs(self.config['data_dir'], exist_ok=True)
        os.makedirs(os.path.join(self.config['data_dir'], self.config['cache_dir']), exist_ok=True)
    
    async def download_buildings(self, geometry):
        # 获取需要下载的quad_keys
        bounds = geometry.bounds
        quad_keys = self._get_quad_keys(bounds)
        
        # 下载并保存数据
        downloaded = []
        for quad_key in tqdm(quad_keys):
            try:
                file_path = await self._download_quad(quad_key)
                downloaded.append({"quad_key": quad_key, "file": file_path})
            except Exception as e:
                print(f"Error downloading {quad_key}: {e}")
                
        # 更新索引
        self._update_index(downloaded)
        return downloaded
    
    def _get_quad_keys(self, bounds):
        return list(mercantile.tiles(*bounds, zooms=self.config['zoom_level']))