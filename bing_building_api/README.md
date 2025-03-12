# Bing Buildings API

## Overview
This API provides access to query and download Bing Buildings data. It supports querying building footprints using bbox, polygon, or point geometries.

## Features
- Query building footprints by bbox/polygon/point
- Download and cache building data
- Interactive web demo interface
- GeoJSON format support

## Installation
1. Clone the repository
2. Install dependencies:
```bash
conda env create -f environment.yml
conda activate bing-building-api   
```

## Usage
1. Start the server:
```bash
conda activate bing-building-api   
python -m app.main
```
2. Access the demo interface:
- Open http://localhost:8001 in your browser
- Before use, download the Bing Buildings data with the download button on the top left.
- Use the map interface to query building data
3. API Endpoints:
- POST /query/buildings
- POST /download/buildings

## License
MIT License
