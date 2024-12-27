import requests
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import json
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


# Global variables to store the token and its expiration time
spotify_token = None
token_expiry_time = 0

# Authorization blueprint
spotify_blueprint = Blueprint('spotify', __name__)

# Function to fetch the Spotify access token
def get_spotify_token():
    global spotify_token, token_expiry_time

    # Check if the token is still valid
    if spotify_token and time.time() < token_expiry_time:
        # If valid, return the cached token
        return spotify_token

    # If no valid token, fetch a new one
    url = "https://accounts.spotify.com/api/token"
    print(SPOTIFY_CLIENT_ID)
    print(SPOTIFY_CLIENT_SECRET)
    payload = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,  
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Make the request to get the access token
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        # Extract the token and set the expiration time (1 hour)
        response_data = response.json()
        spotify_token = response_data.get('access_token')
        token_expiry_time = time.time() + response_data.get('expires_in', 3600)  # Default to 3600 seconds (1 hour)
        return spotify_token
    else:
        print(f"Error fetching token: {response.status_code}, {response.text}")
        return None

# Function to fetch data from the Spotify Web API
def fetch_web_api(endpoint, method, body=None):
    token = get_spotify_token()  # Fetch the access token (cached or new)

    if not token:
        return {'error': 'Unable to fetch access token'}

    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = f'https://api.spotify.com/{endpoint}'
    response = requests.request(method, url, headers=headers, json=body)
    
    if response.status_code != 200:
        return {'error': 'Request failed', 'status_code': response.status_code, 'details': response.text}
    
    return response.json()


def fetch_spotify_playlist(playlist_id, force_update=False):
    print("Fetching Spotify playlist...")
    cache_dir = "backend/cached_playlists"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists
    filename = f"Playlist - {playlist_id}.json".replace(" ", "_")
    filepath = os.path.join(cache_dir, filename)

    # Check if cached file exists
    if not force_update and os.path.exists(filepath):
        with open(filepath, "r") as file:
            cached_data = json.load(file)

        # Check if cache is less than 24 hours old
        updated_at = datetime.fromisoformat(cached_data["updated_at"])
        if datetime.now() - updated_at < timedelta(hours=24):
            print("Returning cached playlist data.")
            return cached_data
    
    endpoint = f"v1/playlists/{playlist_id}"
    playlist_overview_data = fetch_web_api(endpoint, "GET")
    print("TEST")
    playlist_overview_data = {
        "name": playlist_overview_data.get("name"),
        "external_urls": playlist_overview_data.get("external_urls"),
        "images": playlist_overview_data.get("images"),
        "owner": playlist_overview_data.get("owner"),
    }
    # playlist_tracks_data = playlist_overview_data.get("items", [])

    # Fetch data from Spotify API
    endpoint = f"v1/playlists/{playlist_id}/tracks"
    response_data = fetch_web_api(endpoint, "GET")
    playlist_tracks_data = response_data.get("items", [])

    # Load existing data to preserve youtube_links
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            existing_data = json.load(file)
            existing_tracks = existing_data.get("tracks", [])

    # Process tracks
    tracks_info = []
    for index, item in enumerate(playlist_tracks_data, start=1):
        track = item["track"]
        track_name = track["name"]
        artists = [artist["name"] for artist in track["artists"]]
        external_url = track["external_urls"]["spotify"]
        track_image = track["album"]["images"][0]["url"] if track["album"]["images"] else None
 
        # Check if the track exists in the existing data
        existing_track = next((t for t in existing_tracks if t["track_name"] == track_name), None)
        
        # If the track exists, preserve the existing youtube_links
        if existing_track:
            youtube_links = existing_track.get("youtube_links", [])
        else:
            youtube_links = []

        tracks_info.append({
            "id": index,
            "track_name": track_name,
            "track_artists": artists,
            "external_url": external_url,
            "track_image": track_image,
            "youtube_links": youtube_links  # Preserve existing youtube_links
        })

    # Build final structure
    data = {
    "playlist_id": playlist_id,
    "overview": playlist_overview_data,
    "tracks": tracks_info,
    "updated_at": datetime.now().isoformat(),
    }

    # Save to JSON file
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

    print("Returning fresh playlist data.")
    return data
    
# Example of the /get-playlist endpoint
@spotify_blueprint.route('/get-playlist/<playlist_id>')
def get_spotify_playlist(playlist_id):
    tracks_info = fetch_spotify_playlist(playlist_id)
    return jsonify({
        'message': 'Spotify Playlist received', 
        'playlist': tracks_info,
    })
