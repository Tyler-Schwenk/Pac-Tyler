from config import GEOJSON_FILE, SPLIT_GEOJSON_FILE
import json
from geopy.distance import geodesic
import logging

def load_geojson(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_geojson(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def split_activities(activities, threshold_km=0.5):
    new_activities = []
    
    for activity in activities['features']:
        coordinates = activity['geometry']['coordinates']
        properties = activity['properties']
        
        if len(coordinates) < 2:
            continue
        
        new_segments = []
        current_segment = [coordinates[0]]
        
        for i in range(1, len(coordinates)):
            prev_point = coordinates[i - 1]
            current_point = coordinates[i]
            
            distance = geodesic((prev_point[1], prev_point[0]), (current_point[1], current_point[0])).km
            
            if distance > threshold_km:
                new_segments.append(current_segment)
                current_segment = [current_point]
            else:
                current_segment.append(current_point)
        
        new_segments.append(current_segment)
        
        for segment in new_segments:
            new_activity = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": segment
                },
                "properties": properties
            }
            new_activities.append(new_activity)
    
    return {
        "type": "FeatureCollection",
        "features": new_activities
    }


