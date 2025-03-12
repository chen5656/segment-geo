import geopandas as gpd
import json
import os
import mercantile
from tqdm import tqdm
import tempfile
from shapely import geometry
from loguru import logger
from app.config import settings

class BingBuildingQuery:
    def __init__(self):
        self.settings = settings
        self.building_json_location = os.path.join(self.settings.data_dir, self.settings.cache_dir)

    def _find_intersecting_buildings(self, aoi_shape, quad_keys):
        intersecting_features = []  # 统一变量名
        with tempfile.TemporaryDirectory() as tmpdir:
            for quad_key in tqdm(quad_keys):
                file_path = os.path.join(self.building_json_location, f'{quad_key}_processed.json')
                if os.path.exists(file_path):
                    gdf = gpd.read_file(file_path)                              
                    if not gdf.empty:
                        intersecting = gdf[gdf.intersects(aoi_shape)]
                        if not intersecting.empty:
                            for idx, feature in intersecting.iterrows():
                                intersecting_features.append(feature)  # 使用正确的变量名
        return intersecting_features  # 返回正确的变量名
    
    def _get_quad_keys(self, minx, miny, maxx, maxy):
        quad_keys = set()
        for tile in list(mercantile.tiles(minx, miny, maxx, maxy, zooms=settings.ZOOM_LEVEL)):
            quad_keys.add(mercantile.quadkey(tile))
        return quad_keys
    
    def query_buildings(self, geometries):
        all_buildings = [] 
        
        for geom in geometries:
            # Convert GeometryInput to dict
            geom_dict = {
                "type": geom.type,
                "coordinates": geom.coordinates
            }
            aoi_shape = geometry.shape(geom_dict)
            minx, miny, maxx, maxy = aoi_shape.bounds
            quad_keys = self._get_quad_keys(minx, miny, maxx, maxy)
            logger.info('quad_keys', quad_keys)

            # Remove duplicate aoi_shape parameter
            intersecting_buildings = self._find_intersecting_buildings(aoi_shape, quad_keys)

            logger.info('intersecting_buildings', intersecting_buildings)
            all_buildings.extend(intersecting_buildings)

        # Create GeoDataFrame from all intersecting features
        if all_buildings:
            gdf = gpd.GeoDataFrame(all_buildings)
            return gdf.to_json()
        
        # Return empty FeatureCollection if no buildings found
        return json.dumps({
            "type": "FeatureCollection",
            "features": []
        })
    