import time
from datetime import datetime, timedelta
import logging
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded

def is_valid_coordinate(coord):
    """
    Validates if the given coordinate is within the valid range for latitude and longitude.

    Args:
        coord (list): List containing latitude and longitude.

    Returns:
        bool: True if coordinate is valid, False otherwise.
    """
    lat, lon = coord  # Latitude first
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        logging.warning(f"Invalid coordinate found: {coord}")
        return False
    return True

def activities_to_geojson(activities):
    """
    Converts a list of activities into a GeoJSON format.

    Args:
        activities (list): List of activities with their coordinates.

    Returns:
        dict: GeoJSON formatted data.
    """
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for activity in activities:
        if activity['coordinates']:
            valid_coords = [[lon, lat] for lat, lon in activity['coordinates'] if is_valid_coordinate([lat, lon])]
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": valid_coords
                },
                "properties": {
                    "name": activity['name'],
                    "date": str(activity['date']),
                    "distance": activity['distance'],
                    "type": activity['type']
                }
            }
            geojson['features'].append(feature)
    return geojson

class StravaClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        """
        Initializes the StravaClient with the given credentials and URI.

        Args:
            client_id (str): Client ID for Strava API.
            client_secret (str): Client Secret for Strava API.
            redirect_uri (str): Redirect URI for OAuth.
        """
        self.client = Client()
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        logging.debug(f"StravaClient initialized with client_id={client_id}")

    def get_authorization_url(self):
        """
        Generates the authorization URL for the Strava API.

        Returns:
            str: The authorization URL.
        """
        url = self.client.authorization_url(client_id=self.client_id, redirect_uri=self.redirect_uri, scope=['read_all', 'activity:read_all'])
        logging.debug(f"Authorization URL with extended scope: {url}")
        return url

    def authenticate(self, code):
        """
        Authenticates the client with the given authorization code.

        Args:
            code (str): The authorization code received from Strava.
        """
        logging.debug(f"Exchanging code for token with code={code}")
        token_response = self.client.exchange_code_for_token(client_id=self.client_id, client_secret=self.client_secret, code=code)
        self.client.access_token = token_response['access_token']
        logging.debug(f"Access token received: {token_response['access_token']}")

    def fetch_detailed_activities(self, start_date):
        """
        Fetches detailed activities from Strava, starting from the given date.

        Args:
            start_date (datetime): The date to start fetching activities from.

        Returns:
            list: List of detailed activities.
        """
        activities = []

        try:
            logging.info(f"Fetching activities starting from {start_date}")
            summary_activities = list(self.client.get_activities(after=start_date, limit=100))

            for summary_activity in summary_activities:
                full_activity = self.client.get_activity(summary_activity.id)
                streams = self.client.get_activity_streams(full_activity.id, types=['latlng'], resolution='medium')
                coordinates = streams['latlng'].data if 'latlng' in streams else []
                logging.debug(f"Fetched {len(coordinates)} coordinates for activity {full_activity.name}")

                activities.append({
                    "name": full_activity.name,
                    "type": full_activity.type,
                    "date": full_activity.start_date_local,
                    "distance": full_activity.distance.num,
                    "coordinates": coordinates  # Ensure coordinates are in the correct format
                })

        except RateLimitExceeded as e:
            logging.warning("Short term API rate limit exceeded. Waiting for 15 minutes before retrying...")
            time.sleep(15 * 60)  # Sleep for 15 minutes
            return self.fetch_detailed_activities(start_date)  # Retry fetching activities after cooldown

        return activities

