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
        self._df = None
        self.force_download = False
        self.semaphore = asyncio.Semaphore(5)  # limit to 5 concurrent downloads
        self._ensure_directories()
        self._df = None
        
    @property
    def df(self):
        if self._df is None:
            self._df = pd.read_csv(
                "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv", 
                dtype=str
            )
        return self._df

    def _ensure_directories(self):
        """Ensure required directories exist."""
        try:
            os.makedirs(self.settings.data_dir, exist_ok=True)
            os.makedirs(os.path.join(self.settings.data_dir, self.settings.cache_dir), exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise
        
    async def _download_each_quad(self, quad_key: str) -> str:
        quad_key_str = mercantile.quadkey(quad_key)
        
        rows = self.df[self.df["QuadKey"] == quad_key_str]
        if rows.shape[0] != 1:
            raise ValueError(f"No data found for quad_key: {quad_key_str}")
            
        url = rows.iloc[0]["Url"]
        building_json_file_path = os.path.join(self.settings.data_dir, self.settings.cache_dir, f"{quad_key_str}_processed.json")
        
        if not self.force_download and os.path.exists(building_json_file_path):
            logger.info(f"Using cached file for {quad_key}: {building_json_file_path}")
            return building_json_file_path
            
        async with self.semaphore:
            try:
                # read data from url
                df2 = pd.read_json(url, lines=True)
                df2["geometry"] = df2["geometry"].apply(shape)
                gdf = gpd.GeoDataFrame(df2, crs=self.settings.BING_BUILDING_CRS)
                gdf.to_file(building_json_file_path, driver="GeoJSON")
                
                logger.info(f"Successfully downloaded {quad_key}")
                return building_json_file_path
                
            except Exception as e:
                logger.error(f"Error downloading {quad_key}: {e}")
                raise

    async def download_buildings(self, geometries: List[Dict]) -> List[Dict]:
        all_quad_keys = set()
        
        # collect quad_keys
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
        
        # download 
        tasks = [self._download_each_quad(quad_key) for quad_key in all_quad_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        downloaded = []
        for quad_key, result in zip(all_quad_keys, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to download {quad_key}: {result}")
            else:
                downloaded.append({"quad_key": quad_key, "file": result})
                
        return downloaded
    
    def _get_quad_keys(self, bounds):
        return list(mercantile.tiles(*bounds, zooms=self.settings.ZOOM_LEVEL))