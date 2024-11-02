import logging
import webbrowser
import os
from datetime import datetime, timedelta, timezone
from src.utils.strava_client import StravaClient, activities_to_geojson
from src.utils.file_utils import load_existing_geojson, save_geojson
from src.utils.separate_pauses import split_activities
from src.utils.oauth_server import run_server
from dotenv import load_dotenv
from config import REDIRECT_URI

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

def main():
    strava = StravaClient(client_id=client_id, client_secret=client_secret, redirect_uri=REDIRECT_URI)
    url = strava.get_authorization_url()
    logging.info(f"Visit this URL and authorize the application: {url}")
    webbrowser.open_new(url)
    authorization_code = run_server()
    
    strava.authenticate(authorization_code)

    # Load existing GeoJSON and get the most recent activity date
    existing_geojson = load_existing_geojson()
    if existing_geojson['features']:
        # Find the most recent date in the existing GeoJSON
        most_recent_activity_date = max(
            datetime.fromisoformat(feature['properties']['date']) 
            for feature in existing_geojson['features']
        )
        logging.info(f"Existing geojson found, downloading activities since: {most_recent_activity_date}")
    else:
        # Default to one year ago if no existing data
        logging.info("No existing geojson found, downloading all activites from past year")
        most_recent_activity_date = datetime.now() - timedelta(days=365)

    # Initialize the combined GeoJSON with existing features
    combined_geojson = {"type": "FeatureCollection", "features": existing_geojson['features']}
    batch_size = 5
    new_activities_fetched = True  # Initialize flag

    # Adjust most_recent_activity_date to be timezone-aware if not already
    if most_recent_activity_date.tzinfo is None:
        most_recent_activity_date = most_recent_activity_date.replace(tzinfo=timezone.utc)

    while new_activities_fetched:
        # Fetch a batch of new activities
        activities = strava.fetch_detailed_activities_batch(start_date=most_recent_activity_date, batch_size=batch_size)
        
        # Check if any activities were fetched; if not, exit the loop
        if not activities:
            logging.info("No more new activities found.")
            break

        # Convert the batch of activities to GeoJSON format and add to combined GeoJSON
        batch_geojson = activities_to_geojson(activities)
        combined_geojson['features'].extend(batch_geojson['features'])
        
        # Split the activities if necessary and save after each batch
        final_geojson = split_activities(combined_geojson, threshold_km=0.5)
        save_geojson(final_geojson)
        logging.info(f"Saved batch of {len(activities)} activities to GeoJSON.")
        
        # Update the most recent date with the last activity's date + 1 second
        most_recent_activity_date = max(activity['date'] for activity in activities) + timedelta(seconds=1)
    
    logging.info("Finished updating the GeoJSON with all fetched activities.")

if __name__ == '__main__':
    main()
