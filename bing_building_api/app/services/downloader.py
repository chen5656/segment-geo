import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import mercantile
from tqdm import tqdm
import yaml
from loguru import logger
from app.config import settings
import aiohttp
import asyncio
from typing import List, Dict

class BingBuildingDownloader:
    def __init__(self):
        self.settings = settings
        self._ensure_directories()
        self._df = None
        self.force_download = False
        self.semaphore = asyncio.Semaphore(5)  # 限制并发数
        
    async def _download_quad(self, quad_key: str) -> str:
        rows = self.df[self.df["QuadKey"] == str(quad_key)]
        if rows.shape[0] != 1:
            raise ValueError(f"No data found for quad_key: {quad_key}")
            
        url = rows.iloc[0]["Url"]
        json_fn = os.path.join(self.settings.data_dir, self.settings.cache_dir, f"{quad_key}_processed.json")
        
        if not self.force_download and os.path.exists(json_fn):
            logger.info(f"Using cached file for {quad_key}: {json_fn}")
            return json_fn
            
        async with self.semaphore:  # 控制并发数
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise ValueError(f"Failed to download {url}: {response.status}")
                        data = await response.json(content_type=None)
                        
                df2 = pd.DataFrame(data)
                df2["geometry"] = df2["geometry"].apply(shape)
                gdf = gpd.GeoDataFrame(df2, crs=self.settings.BING_BUILDING_CRS)
                gdf.to_file(json_fn, driver="GeoJSON")
                
                logger.info(f"Successfully downloaded {quad_key}")
                return json_fn
                
            except Exception as e:
                logger.error(f"Error downloading {quad_key}: {e}")
                raise

    async def download_buildings(self, geometries: List[Dict]) -> List[Dict]:
        all_quad_keys = set()
        
        # 收集所有需要下载的 quad_keys
        for geometry in geometries:
            try:
                geo_dict = geometry if isinstance(geometry, dict) else geometry.__dict__
                geometry = shape(geo_dict)
                bounds = geometry.bounds
                quad_keys = self._get_quad_keys(bounds)
                all_quad_keys.update(quad_keys)
            except Exception as e:
                logger.error(f"Error processing geometry: {e}")

        logger.info(f"Preparing to download {len(all_quad_keys)} quad keys")
        
        # 并发下载所有文件
        tasks = [self._download_quad(quad_key) for quad_key in all_quad_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        downloaded = []
        for quad_key, result in zip(all_quad_keys, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to download {quad_key}: {result}")
            else:
                downloaded.append({"quad_key": quad_key, "file": result})
                
        return downloaded
    
    def _get_quad_keys(self, bounds):
        return list(mercantile.tiles(*bounds, zooms=self.settings.ZOOM_LEVEL))