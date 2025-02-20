import os
import json


def save_geojson(data, filename="test_result"):
    """Save GeoJSON data to a file, overwriting if exists
    
    Args:
        data: The GeoJSON data to save
        prefix: The prefix for the output filename (default: "test_result")
        
    Returns:
        str: The path to the saved file
    """
    filename = f"{filename}.geojson"

    # Create results directory in parent folder if it doesn't exist
    results_dir = os.path.join(os.path.dirname(__file__), "test_results")
    os.makedirs(results_dir, exist_ok=True)

    filepath = os.path.join(results_dir, filename)

    # Write the file (will overwrite if exists)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"GeoJSON saved to: {filepath}")
    return filepath