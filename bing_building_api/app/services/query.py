import geopandas as gpd
import json
import os
import pandas as pd
from shapely.geometry import shape

class BingBuildingQuery:
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _load_index(self):
        index_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'index.json')
        with open(index_path, 'r') as f:
            return json.load(f)
    
    def _find_intersecting_quads(self, geometry, index):
        intersecting_quads = []
        for quad in index['quads']:
            quad_geom = shape(quad['geometry'])
            if geometry.intersects(quad_geom):
                intersecting_quads.append(quad)
        return intersecting_quads
    
    def _filter_intersecting_buildings(self, buildings, geometry):
        if buildings.empty:
            return buildings
        return buildings[buildings.geometry.intersects(geometry)]
    
    def query_buildings(self, geometry):
        index = self._load_index()
        
        intersecting_quads = self._find_intersecting_quads(geometry, index)
        
        buildings = self._load_buildings(intersecting_quads)
        
        result = self._filter_intersecting_buildings(buildings, geometry)
        
        return result.to_json()
    
    def _load_buildings(self, quads):
        gdfs = []
        for quad in quads:
            file_path = quad['file_path']
            if os.path.exists(file_path):
                gdf = gpd.read_file(file_path)
                gdfs.append(gdf)
        
        if gdfs:
            return pd.concat(gdfs)
        return gpd.GeoDataFrame()