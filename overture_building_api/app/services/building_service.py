import os
import time

from geoai.download import download_overture_buildings, extract_building_stats

async def get_building_data(bbox: list) -> dict:
    """
    Get building footprints and statistics for a given bounding box
    """
    temp_path = f"temp_buildings_{int(time.time())}.geojson"
    
    try:
        data_file = download_overture_buildings(
            bbox=bbox,
            output_file=temp_path,
            output_format="geojson",
            data_type="building",
            verbose=True
        )

        if not data_file:
            return {
                "status_code": 404,
                "content": {"error": {"message": "No building data found for the given bbox"}}
            }

        stats = extract_building_stats(data_file)

        with open(data_file, 'r') as f:
            geojson_data = f.read()

        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "geojson": geojson_data,
            "stats": stats
        }
        

    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

if __name__ == "__main__":
    import asyncio
    bbox = [-76.15741548689954, 43.05635088078997, -76.15648427005196, 43.05692144640927]
    result = asyncio.run(get_building_data(bbox))
    print(result)
