import os
import sys
import json
from datetime import datetime

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

def save_geojson(data, prefix="test_result"):
    """Save GeoJSON data to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.geojson"

    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "support/test_results")
    os.makedirs(results_dir, exist_ok=True)

    filepath = os.path.join(results_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"GeoJSON saved to: {filepath}")
    return filepath