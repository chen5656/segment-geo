# Overture Building Footprint API

A FastAPI service that provides building footprint data from Overture Maps.

## Features

- Fetch building footprints for a given bounding box
- Get building statistics (total count, buildings with height, etc.)
- GeoJSON output format
- Error handling and validation

## Installation

1. Create conda environment:
```bash
conda env create -f environment.yml
```
2. Activate conda environment:
```bash
conda activate overture-api
```
3. Run the API:
```bash
uvicorn app.main:app --reload
```

## API Endpoints
### GET /health
Health check endpoint

### POST /buildings
Get building footprints and statistics for a given bounding box

Request body:
```json
{
    "bbox": [-117.6029, 47.65, -117.5936, 47.6563]
}
```

Response:
```json
{
    "geojson": {
        "type": "FeatureCollection",
        "features": [...]
    },
    "stats": {
        "total_buildings": 199,
        "has_height": 84,
        "has_name": 0,
        "bbox": [-117.6017984, 47.650168297348685, -117.5937308, 47.655846]
    }
}
```

