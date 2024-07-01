import logging
import webbrowser
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from src.strava_client import StravaClient, activities_to_geojson
from src.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

LAST_FETCH_FILE = "last_fetch.txt"
GEOJSON_FILE = "activities.geojson"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Handles the OAuth callback and extracts the authorization code from the URL.
        """
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        code = query.get('code', [None])[0]
        
        logging.info(f"Authorization code received: {code}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You can close this window now.')
        
        if code:
            global authorization_code
            authorization_code = code

def run_server():
    """
    Runs a simple HTTP server to handle OAuth callbacks.
    """
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    logging.info('Starting HTTP server for OAuth callback...')
    httpd.handle_request()

def save_geojson(geojson, filename=GEOJSON_FILE):
    """
    Saves the GeoJSON data to a file.

    Args:
        geojson (dict): The GeoJSON data to save.
        filename (str): The name of the file to save the data to.
    """
    with open(filename, 'w') as f:
        json.dump(geojson, f, indent=4)  # Use indent for a pretty-printed JSON

def load_last_fetch_date():
    """
    Loads the last fetch date from a file.

    Returns:
        datetime: The last fetch date, or a default value of one year ago if the file doesn't exist.
    """
    try:
        with open(LAST_FETCH_FILE, 'r') as f:
            last_fetch = datetime.fromisoformat(f.read().strip())
            logging.info(f"Last fetch date loaded: {last_fetch}")
            return last_fetch
    except FileNotFoundError:
        one_year_ago = datetime.now() - timedelta(days=365)
        logging.info(f"No last fetch date found. Defaulting to one year ago: {one_year_ago}")
        return one_year_ago

def save_last_fetch_date(date):
    """
    Saves the last fetch date to a file.

    Args:
        date (datetime): The date to save.
    """
    with open(LAST_FETCH_FILE, 'w') as f:
        f.write(date.isoformat())
        logging.info(f"Last fetch date saved: {date}")

def load_existing_geojson(filename=GEOJSON_FILE):
    """
    Loads the existing GeoJSON data from a file.

    Args:
        filename (str): The name of the file to load the data from.

    Returns:
        dict: The loaded GeoJSON data, or a new GeoJSON structure if the file doesn't exist.
    """
    try:
        with open(filename, 'r') as f:
            geojson = json.load(f)
            logging.info(f"Loaded existing GeoJSON file with {len(geojson['features'])} features.")
            return geojson
    except FileNotFoundError:
        logging.info("No existing GeoJSON file found. Creating a new one.")
        return {"type": "FeatureCollection", "features": []}

def main():
    """
    Main function to run the Strava data fetch and save the results to a GeoJSON file.
    """
    strava = StravaClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    url = strava.get_authorization_url()
    print(f"Visit this URL and authorize the application: {url}")
    webbrowser.open_new(url)
    run_server()
    
    strava.authenticate(authorization_code)

    last_fetch_date = load_last_fetch_date()
    activities = strava.fetch_detailed_activities(start_date=last_fetch_date)

    if activities:
        # Update the last fetch date to the date of the last fetched activity
        new_last_fetch_date = activities[-1]['date']
        save_last_fetch_date(new_last_fetch_date)

        # Load existing GeoJSON data
        existing_geojson = load_existing_geojson()
        
        # Convert new activities to GeoJSON and append to existing data
        new_geojson = activities_to_geojson(activities)
        existing_geojson['features'].extend(new_geojson['features'])
        
        # Save the updated GeoJSON data
        save_geojson(existing_geojson)
        print("GeoJSON file has been updated with new activities.")
    else:
        print("No new activities found.")

if __name__ == '__main__':
    main()
