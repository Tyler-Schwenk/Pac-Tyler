import json
import logging

from config import GEOJSON_FILE

def save_geojson(geojson, filename=GEOJSON_FILE):
    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=4)

def load_existing_geojson(filename=GEOJSON_FILE):
    try:
        with open(filename, 'r') as f:
            geojson = json.load(f)
            logging.info(f"Loaded existing GeoJSON file with {len(geojson['features'])} features.")
            return geojson
    except FileNotFoundError:
        logging.info("No existing GeoJSON file found. Creating a new one.")
        return {"type": "FeatureCollection", "features": []}
